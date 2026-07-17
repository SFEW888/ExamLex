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
            self.assertEqual(result["ability"]["reading"]["direction"], "improving")
            self.assertEqual(result["modules"], {})
            self.assertEqual(result["inputs"]["history_snapshots"], 2)
        finally:
            for path in (history_path, output_path):
                if path.exists():
                    path.unlink()

    def test_ledger_accuracy_and_history_ability_stay_separate_for_shared_module(self):
        # A module present in both inputs must not blend accuracy (0-1) with
        # ability level (1-4): each belongs to its own trend series.
        ledger = [
            {"module": "reading", "total_items": 10, "correct_items": 5},
            {"module": "reading", "total_items": 10, "correct_items": 9},
        ]
        history = [
            {"modules": {"reading": [{"level": 4}]}},
            {"modules": {"reading": [{"level": 1}]}},
        ]

        trends = analyze_trends.analyze_trends(ledger=ledger, history=history)

        self.assertEqual(trends["modules"]["reading"]["direction"], "improving")
        self.assertEqual(trends["modules"]["reading"]["first"], 0.5)
        self.assertEqual(trends["modules"]["reading"]["last"], 0.9)
        self.assertEqual(trends["ability"]["reading"]["direction"], "declining")
        self.assertEqual(trends["ability"]["reading"]["first"], 4)
        self.assertEqual(trends["ability"]["reading"]["last"], 1)


if __name__ == "__main__":
    unittest.main()
