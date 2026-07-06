"""Tests for strategy ratchet mechanism."""
import json
import tempfile
import unittest
from pathlib import Path

from skills.english_exam_ai_tutor.scripts.optimizers.ratchet import (
    StrategyRatchet,
    RatchetDecision,
)


class RatchetBaselineTests(unittest.TestCase):
    def setUp(self):
        self.ratchet = StrategyRatchet()

    def test_baseline_sets_score_and_history(self):
        s = {"strategy_id": "cet4-reading-001", "title": "Test"}
        result = self.ratchet.baseline(s, 80.0)
        self.assertEqual(result["darwin_score"], 80.0)
        self.assertEqual(len(result["score_history"]), 1)
        self.assertEqual(result["score_history"][0]["status"], "baseline")
        self.assertEqual(result["score_history"][0]["version"], 1)

    def test_baseline_does_not_mutate_original(self):
        s = {"strategy_id": "cet4-reading-001"}
        self.ratchet.baseline(s, 75.0)
        self.assertNotIn("darwin_score", s)


class RatchetCompareTests(unittest.TestCase):
    def setUp(self):
        self.ratchet = StrategyRatchet()

    def test_improvement_keeps(self):
        old = {"strategy_id": "x", "darwin_score": 70.0}
        new = {"strategy_id": "x", "darwin_score": 80.0}
        result = self.ratchet.compare(old, new, 80.0)
        self.assertEqual(result.decision, RatchetDecision.KEEP)
        self.assertEqual(result.delta, 10.0)

    def test_regression_reverts(self):
        old = {"strategy_id": "x", "darwin_score": 80.0}
        new = {"strategy_id": "x", "darwin_score": 75.0}
        result = self.ratchet.compare(old, new, 75.0)
        self.assertEqual(result.decision, RatchetDecision.REVERT)
        self.assertEqual(result.delta, -5.0)

    def test_same_score_keeps(self):
        old = {"strategy_id": "x", "darwin_score": 75.0}
        new = {"strategy_id": "x", "darwin_score": 75.0}
        result = self.ratchet.compare(old, new, 75.0)
        self.assertEqual(result.decision, RatchetDecision.KEEP)


class TouchTopTests(unittest.TestCase):
    def setUp(self):
        self.ratchet = StrategyRatchet(touch_top_delta=2.0)

    def test_no_stop_with_few_rounds(self):
        history = [
            {"version": 1, "score": 70, "delta": 0, "status": "baseline"},
            {"version": 2, "score": 71, "delta": 1.0, "status": "keep"},
        ]
        self.assertFalse(self.ratchet.should_stop(history))

    def test_touch_top_stops(self):
        history = [
            {"version": 1, "score": 70, "delta": 0, "status": "baseline"},
            {"version": 2, "score": 71.5, "delta": 1.5, "status": "keep"},
            {"version": 3, "score": 73.0, "delta": 1.5, "status": "keep"},
            {"version": 4, "score": 73.8, "delta": 0.8, "status": "keep"},
        ]
        self.assertTrue(self.ratchet.should_stop(history))


class AtomicSaveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_atomic_save_creates_file(self):
        path = Path(self.tmp) / "test.json"
        StrategyRatchet.atomic_save({"strategies": []}, path)
        self.assertTrue(path.exists())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["strategies"], [])

    def test_atomic_save_creates_backup(self):
        path = Path(self.tmp) / "lib.json"
        path.write_text('{"strategies": [{"id": 1}]}', encoding="utf-8")
        StrategyRatchet.atomic_save({"strategies": [{"id": 2}]}, path)
        bak = Path(self.tmp) / "lib.json.bak"
        self.assertTrue(bak.exists())

    def test_atomic_save_overwrites(self):
        path = Path(self.tmp) / "lib2.json"
        path.write_text('{"strategies": [1]}', encoding="utf-8")
        StrategyRatchet.atomic_save({"strategies": [2, 3]}, path)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["strategies"]), 2)


if __name__ == "__main__":
    unittest.main()
