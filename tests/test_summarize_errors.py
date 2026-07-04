import unittest
from pathlib import Path

from skills.english_exam_ai_tutor.scripts import common, summarize_errors


class SummarizeErrorsTests(unittest.TestCase):
    def test_summarizes_counts_and_percentages_by_tag_module_dimension(self):
        ledger = Path("test-artifacts") / "task5-summary-ledger.json"
        ledger.parent.mkdir(exist_ok=True)
        try:
            common.save_data(
                ledger,
                [
                    {"module": "reading", "total_items": 10, "correct_items": 6, "error_tags": ["READING_PARAPHRASE_FAIL"]},
                    {"module": "reading", "total_items": 10, "correct_items": 7, "error_tags": ["READING_PARAPHRASE_FAIL"]},
                    {"module": "writing", "total_items": 1, "correct_items": 0, "error_tags": ["WRITING_ARTICLE_OMISSION"]},
                ],
            )

            summary = summarize_errors.summarize_errors(ledger)

            self.assertEqual(summary["total_records"], 3)
            self.assertEqual(summary["by_tag"]["READING_PARAPHRASE_FAIL"]["count"], 2)
            self.assertEqual(summary["by_tag"]["READING_PARAPHRASE_FAIL"]["percentage"], 0.67)
            self.assertEqual(summary["by_module"]["reading"]["count"], 2)
            self.assertEqual(summary["by_dimension"]["语言准确性"]["count"], 1)
        finally:
            if ledger.exists():
                ledger.unlink()


if __name__ == "__main__":
    unittest.main()
