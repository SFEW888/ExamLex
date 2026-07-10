import json
import unittest
from pathlib import Path

from examlex.scripts import analyze_trends


class AnalyzeTrendsTests(unittest.TestCase):
    def test_analyzes_ledger_accuracy_direction_by_module(self):
        ledger = [
            {"module": "reading", "total_items": 10, "correct_items": 5},
            {"module": "reading", "total_items": 10, "correct_items": 8},
            {"module": "writing", "total_items": 10, "correct_items": 9},
            {"module": "writing", "total_items": 10, "correct_items": 6},
            {"module": "listening", "total_items": 10, "correct_items": 7},
        ]

        trends = analyze_trends.analyze_trends(ledger=ledger)

        self.assertEqual(trends["modules"]["reading"]["direction"], "improving")
        self.assertEqual(trends["modules"]["writing"]["direction"], "declining")
        self.assertEqual(trends["modules"]["listening"]["direction"], "insufficient_data")

    def test_analyzes_history_level_direction_and_writes_cli_output(self):
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        history_path = root / "task6-history.json"
        output_path = root / "task6-trends.json"
        try:
            history_path.write_text(
                json.dumps(
                    [
                        {"modules": {"reading": [{"level": 2}, {"level": 2}]}},
                        {"modules": {"reading": [{"level": 4}, {"level": 4}]}},
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                analyze_trends.main(["--history", str(history_path), "--output", str(output_path)]),
                0,
            )

            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result["modules"]["reading"]["direction"], "improving")
            self.assertEqual(result["inputs"]["history_snapshots"], 2)
        finally:
            for path in (history_path, output_path):
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
