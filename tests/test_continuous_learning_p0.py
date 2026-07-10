import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from examlex.scripts import cli_commit, cli_extract, generate_daily_plan, ingest_strategy


class _FakeExtractor:
    def __init__(self):
        self.calls = []

    def extract(self, input_ref, output_dir):
        self.calls.append((input_ref, output_dir))
        artifact = Path(output_dir) / "full_text.txt"
        artifact.write_text("distilled source", encoding="utf-8")
        return SimpleNamespace(
            artifacts={"full_text": artifact},
            metadata={"char_count": 16, "word_count_approx": 2},
            warnings=[],
        )


class ContinuousLearningP0Tests(unittest.TestCase):
    def test_book_cli_dispatches_to_book_extractor(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "guide.pdf"
            source.write_bytes(b"not parsed by fake")
            fake = _FakeExtractor()

            with patch.object(cli_extract, "BookExtractor", return_value=fake, create=True):
                with redirect_stdout(io.StringIO()):
                    result = cli_extract.main([
                        "--input", str(source), "--type", "book", "--output-dir", str(root / "sessions"),
                    ])

            self.assertEqual(result, 0)
            self.assertEqual(len(fake.calls), 1)

    def test_video_cli_dispatches_to_video_extractor(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            fake = _FakeExtractor()

            with patch.object(cli_extract, "VideoExtractor", return_value=fake, create=True):
                with redirect_stdout(io.StringIO()):
                    result = cli_extract.main([
                        "--input", "https://youtu.be/example", "--type", "video", "--output-dir", str(root / "sessions"),
                    ])

            self.assertEqual(result, 0)
            self.assertEqual(len(fake.calls), 1)

    def test_ingest_creates_a_valid_draft_strategy(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "method.md"
            source.write_text("Use a concrete reading method with a checkpoint.", encoding="utf-8")
            library = root / "strategy-library.json"

            strategy = ingest_strategy.ingest_strategy(
                file_path=source,
                library_path=library,
                exam_types=["CET4"],
                modules=["reading"],
            )

            self.assertEqual(strategy["lifecycle_status"], "draft")
            self.assertRegex(strategy["strategy_id"], r"^cet4-reading-[a-z0-9-]+-001$")

    def test_daily_plan_excludes_draft_strategies(self):
        plan = generate_daily_plan.generate_daily_plan(
            {"learner_id": "learner", "exam_type": "CET4", "daily_time_budget_minutes": 20},
            {"modules": {"reading": [{"node": "locating", "level": 1, "status": "priority"}]}},
            strategies={"strategies": [{
                "strategy_id": "cet4-reading-locate-001",
                "title": "Draft method",
                "exam_types": ["CET4"],
                "modules": ["reading"],
                "lifecycle_status": "draft",
                "darwin_score": 100,
                "steps": ["1. Read"],
            }]},
        )

        hints = [hint for task in plan["tasks"] for hint in task.get("strategy_hints", [])]
        self.assertEqual(hints, [])

    def test_commit_rejects_missing_validation_and_evaluation_reports(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            self._write_distilled(root)

            with redirect_stdout(io.StringIO()):
                result = cli_commit.main(["--artifacts-dir", str(root), "--library", str(root / "library.json")])

            self.assertEqual(result, 2)

    def test_commit_rejects_below_threshold_evaluation(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            self._write_distilled(root)
            (root / "validation_report.json").write_text(json.dumps({
                "all_format_passed": True,
                "results": [{"strategy_id": "cet4-reading-locate-001", "format_passed": True,
                             "structure_passed": True, "structure_score": 59}],
            }), encoding="utf-8")
            (root / "evaluation.json").write_text(json.dumps({
                "strategies": [{"strategy_id": "cet4-reading-locate-001", "effect_total": 10}],
            }), encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                result = cli_commit.main(["--artifacts-dir", str(root), "--library", str(root / "library.json")])

            self.assertEqual(result, 2)

    def test_commit_approves_a_complete_passing_strategy(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            library = root / "library.json"
            self._write_distilled(root)
            (root / "validation_report.json").write_text(json.dumps({
                "all_format_passed": True,
                "results": [{"strategy_id": "cet4-reading-locate-001", "format_passed": True,
                             "structure_passed": True, "structure_score": 59}],
            }), encoding="utf-8")
            (root / "evaluation.json").write_text(json.dumps({
                "strategies": [{"strategy_id": "cet4-reading-locate-001", "effect_total": 11}],
            }), encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                result = cli_commit.main(["--artifacts-dir", str(root), "--library", str(library)])

            self.assertEqual(result, 0)
            committed = json.loads(library.read_text(encoding="utf-8"))["strategies"][0]
            self.assertEqual(committed["lifecycle_status"], "approved")
            self.assertEqual(committed["darwin_score"], 70)

    @staticmethod
    def _write_distilled(root):
        (root / "distilled.json").write_text(json.dumps({"strategies": [{
            "strategy_id": "cet4-reading-locate-001",
            "title": "Locate evidence",
            "exam_types": ["CET4"],
            "modules": ["reading"],
            "content": "Read the question, locate matching evidence, and verify the answer.",
            "source_file": "source.md",
            "added_at": "2026-07-10",
        }]}), encoding="utf-8")

    @staticmethod
    def _temporary_dir():
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()
