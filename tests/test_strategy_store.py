from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from examlex.scripts import list_strategies, strategy_store


class StrategyStoreHealthTests(unittest.TestCase):
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
