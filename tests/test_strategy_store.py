from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from examlex.scripts import (
    ingest_strategy,
    list_strategies,
    strategy_database,
    strategy_sqlite,
    strategy_store,
    validate_strategy,
)


class StrategyStoreHealthTests(unittest.TestCase):
    def test_strategy_database_json_flag_is_position_independent(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "source.json"
            database = root / "strategies.db"
            exported = root / "exported.json"
            source.write_text(json.dumps({"strategies": []}), encoding="utf-8")

            before_subcommand = StringIO()
            with redirect_stdout(before_subcommand):
                self.assertEqual(
                    0,
                    strategy_database.main(
                        [
                            "--json",
                            "import-json",
                            "--input",
                            str(source),
                            "--database",
                            str(database),
                        ]
                    ),
                )
            self.assertTrue(json.loads(before_subcommand.getvalue())["ok"])

            after_subcommand = StringIO()
            with redirect_stdout(after_subcommand):
                self.assertEqual(
                    0,
                    strategy_database.main(
                        [
                            "export-json",
                            "--database",
                            str(database),
                            "--output",
                            str(exported),
                            "--json",
                        ]
                    ),
                )
            self.assertTrue(json.loads(after_subcommand.getvalue())["ok"])
            self.assertEqual({"strategies": []}, json.loads(exported.read_text(encoding="utf-8")))

    def test_sqlite_round_trip_and_json_export_preserve_revisions(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            database = root / "strategies.db"
            exported = root / "exported.json"
            library = {
                "schema_version": 1,
                "strategies": [
                    {
                        "strategy_id": "reading-001",
                        "title": "Locate contrast markers",
                        "content": "Mark contrast words before comparing the options.",
                        "exam_types": ["CET4"],
                        "modules": ["reading"],
                        "revisions": [
                            {
                                "version": 1,
                                "sha256": "a" * 64,
                                "strategy": {"content": "Mark contrast words."},
                            }
                        ],
                    }
                ],
            }
            strategy_store.atomic_save_strategy_library(library, database)
            loaded = strategy_store.load_strategy_library(database)
            self.assertEqual(library, loaded)
            report = strategy_store.strategy_library_health(
                database, warning_threshold_bytes=1
            )
            self.assertEqual("sqlite", report["storage_backend"])
            strategy_sqlite.export_json(database, exported)
            self.assertEqual(library, json.loads(exported.read_text(encoding="utf-8")))

    def test_approximate_duplicates_are_review_only_candidates(self):
        library = {
            "strategies": [
                {
                    "strategy_id": "one",
                    "title": "Contrast location",
                    "content": "Locate the contrast marker first, then compare every option with the evidence sentence.",
                    "exam_types": ["CET4"],
                    "modules": ["reading"],
                },
                {
                    "strategy_id": "two",
                    "title": "Contrast-based location",
                    "content": "Locate a contrast marker first, and then compare every option with the exact evidence sentence.",
                    "exam_types": ["CET4"],
                    "modules": ["reading"],
                },
            ]
        }
        candidates = strategy_store.find_possible_duplicate_strategies(
            library, similarity_threshold=0.80
        )
        near = [item for item in candidates if item["reason"] == "near_duplicate_content"]
        self.assertEqual(1, len(near))
        self.assertTrue(near[0]["requires_reference_check"])
        self.assertIn("similarity", near[0])
        self.assertEqual(2, len(library["strategies"]))

    def test_threshold_warning_lists_candidates_without_deleting_data(self):
        with self._temporary_dir() as temp:
            library_path = Path(temp) / "strategy-library.json"
            library = self._library_with_duplicates()
            strategy_store.atomic_save_strategy_library(library, library_path)
            original_bytes = library_path.read_bytes()

            with self.assertLogs("examlex.scripts.strategy_store", level="WARNING") as logs:
                report = strategy_store.warn_if_strategy_library_large(
                    library_path,
                    warning_threshold_bytes=1,
                )

            self.assertTrue(report["threshold_reached"])
            self.assertFalse(report["automatic_deletion"])
            self.assertEqual(original_bytes, library_path.read_bytes())
            reasons = {candidate["reason"] for candidate in report["duplicate_candidates"]}
            self.assertIn("same_normalized_content", reasons)
            self.assertIn("same_content_across_revisions", reasons)
            self.assertIn("no strategies or revisions were deleted", " ".join(logs.output))

    def test_list_strategies_can_return_review_only_duplicate_groups(self):
        with self._temporary_dir() as temp:
            library_path = Path(temp) / "strategy-library.json"
            library_path.write_text(
                json.dumps(self._library_with_duplicates()),
                encoding="utf-8",
            )

            report = list_strategies.list_strategies(
                library_path,
                include_duplicates=True,
            )

            self.assertEqual(2, report["total"])
            self.assertGreaterEqual(len(report["duplicate_candidates"]), 2)
            revision_group = next(
                candidate
                for candidate in report["duplicate_candidates"]
                if candidate["reason"] == "same_content_across_revisions"
            )
            self.assertTrue(revision_group["requires_reference_check"])

    def test_list_strategies_tolerates_null_exam_types_and_modules(self):
        # A hand-edited library may carry null (or non-list) exam_types/modules;
        # the histogram must skip them rather than crash on `for x in None`.
        with self._temporary_dir() as temp:
            library_path = Path(temp) / "strategy-library.json"
            library_path.write_text(
                json.dumps(
                    {
                        "strategies": [
                            {"strategy_id": "a", "exam_types": None, "modules": None},
                            {"strategy_id": "b", "exam_types": "CET4", "modules": 3},
                            {"strategy_id": "c", "exam_types": ["CET6", 7],
                             "modules": ["reading"]},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = list_strategies.list_strategies(library_path)

            self.assertEqual(3, report["total"])
            # Only well-formed string members are counted; null/non-list/non-str
            # values are skipped without error.
            self.assertEqual({"CET6": 1}, report["by_exam"])
            self.assertEqual({"reading": 1}, report["by_module"])

    def test_ingest_list_and_validate_support_sqlite_libraries(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "reading-method.md"
            database = root / "strategy-library.sqlite"
            source.write_text(
                "Read the question stem, locate its evidence sentence, and compare every option with that evidence.",
                encoding="utf-8",
            )

            written = ingest_strategy.ingest_strategy(
                file_path=source,
                library_path=database,
                exam_types=["CET4"],
                modules=["reading"],
            )
            listed = list_strategies.list_strategies(database)

            self.assertEqual(1, listed["total"])
            self.assertEqual(written["strategy_id"], listed["strategies"][0]["strategy_id"])
            report = validate_strategy.validate_library(
                strategy_store.load_strategy_library(database)
            )
            self.assertEqual(0, report["summary"]["total_error"])

    @staticmethod
    def _library_with_duplicates():
        first = {
            "strategy_id": "cet4-reading-locate-001",
            "title": "Locate evidence",
            "exam_types": ["CET4"],
            "modules": ["reading"],
            "content": "Read the stem and locate the evidence.",
            "revisions": [
                {
                    "version": 1,
                    "sha256": "a" * 64,
                    "strategy": {"title": "Locate evidence", "content": "Same method"},
                },
                {
                    "version": 2,
                    "sha256": "b" * 64,
                    "strategy": {"title": "Locate evidence", "content": " same   method "},
                },
            ],
        }
        second = {
            "strategy_id": "cet4-reading-locate-002",
            "title": "Another title",
            "exam_types": ["CET4"],
            "modules": ["reading"],
            "content": " read the stem AND locate the evidence. ",
        }
        return {"strategies": [first, second]}

    @staticmethod
    def _temporary_dir():
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()
