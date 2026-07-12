import unittest
import json
import threading
import time
from pathlib import Path

from examlex.scripts import record_practice
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RecordPracticeTests(unittest.TestCase):
    def test_concurrent_appends_keep_both_records(self):
        ledger = Path("test-artifacts") / "concurrent-record-ledger.json"
        ledger.parent.mkdir(exist_ok=True)
        ledger.write_text("[]\n", encoding="utf-8")
        original_load = record_practice.common.load_data

        def delayed_load(path):
            data = original_load(path)
            time.sleep(0.05)
            return data

        def append(task_id):
            record_practice.record_practice(
                ledger,
                {
                    "task_id": task_id,
                    "duration_minutes": 1,
                    "total_items": 1,
                    "correct_items": 1,
                    "error_tags": [],
                },
            )

        try:
            with patch.object(record_practice.common, "load_data", side_effect=delayed_load):
                workers = [threading.Thread(target=append, args=(f"task-{i}",)) for i in range(2)]
                for worker in workers:
                    worker.start()
                for worker in workers:
                    worker.join()
            saved = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual({"task-0", "task-1"}, {item["task_id"] for item in saved})
        finally:
            ledger.unlink(missing_ok=True)

    def test_packaged_practice_template_is_an_appendable_ledger(self):
        template = json.loads(
            (PROJECT_ROOT / "examlex/assets/templates/exercise-record.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIsInstance(template, list)

    def test_appends_record_and_computes_accuracy_from_items(self):
        ledger = Path("test-artifacts") / "task5-record-ledger.json"
        ledger.parent.mkdir(exist_ok=True)
        if ledger.exists():
            ledger.unlink()
        try:

            record = record_practice.record_practice(
                ledger,
                {
                    "date": "2026-07-04",
                    "module": "reading",
                    "task_id": "reading-001",
                    "duration_minutes": 20,
                    "total_items": 10,
                    "correct_items": 7,
                    "error_tags": ["READING_PARAPHRASE_FAIL"],
                },
            )

            self.assertEqual(record["accuracy"], 0.7)
            self.assertNotIn("total", record)
            self.assertNotIn("correct", record)
            self.assertIn('"correct_items": 7', ledger.read_text(encoding="utf-8"))
        finally:
            if ledger.exists():
                ledger.unlink()

    def test_rejects_invalid_totals_and_unknown_tags(self):
        ledger = Path("test-artifacts") / "task5-invalid-ledger.json"
        ledger.parent.mkdir(exist_ok=True)
        if ledger.exists():
            ledger.unlink()
        try:

            with self.assertRaisesRegex(ValueError, "total_items"):
                record_practice.record_practice(
                    ledger,
                    {"total_items": 0, "correct_items": 0, "error_tags": []},
                )

            with self.assertRaisesRegex(ValueError, "UNKNOWN_TAG"):
                record_practice.record_practice(
                    ledger,
                    {"total_items": 1, "correct_items": 1, "error_tags": ["UNKNOWN_TAG"]},
                )
        finally:
            if ledger.exists():
                ledger.unlink()


if __name__ == "__main__":
    unittest.main()
