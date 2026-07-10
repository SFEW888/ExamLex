import unittest
from pathlib import Path

from examlex.scripts import record_practice


class RecordPracticeTests(unittest.TestCase):
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
