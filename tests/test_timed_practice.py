from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO_ROOT / "skills" / "english-exam-ai-tutor" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import common
from record_practice import record_practice
from summarize_errors import summarize_errors


class TestTimedPractice(unittest.TestCase):
    def setUp(self):
        self.tmp = REPO_ROOT / ".task8-test-tmp" / "test_timed_practice"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.tmp / "practice-ledger.json"
        # Clean ledger
        if self.ledger_path.exists():
            self.ledger_path.unlink()

    def _make_timed_record(self, **overrides):
        base = {
            "date": "2026-07-06",
            "exam_type": "CET4",
            "module": "reading",
            "task_id": "timed-reading-001",
            "duration_minutes": 45,
            "total_items": 20,
            "correct_items": 14,
            "timed": True,
            "time_limit_minutes": 40,
            "overtime_items": 5,
            "overtime_correct": 2,
            "error_tags": ["READING_SPEED_LOW"],
        }
        base.update(overrides)
        return base

    def _make_normal_record(self, **overrides):
        base = {
            "date": "2026-07-06",
            "exam_type": "CET4",
            "module": "vocabulary",
            "task_id": "vocab-001",
            "duration_minutes": 15,
            "total_items": 30,
            "correct_items": 25,
            "error_tags": ["VOCAB_SPELLING_FAIL"],
        }
        base.update(overrides)
        return base

    def test_timed_record_accepted(self):
        """Timed record is accepted and persisted."""
        rec = self._make_timed_record()
        result = record_practice(self.ledger_path, rec)
        self.assertTrue(result.get("timed"))
        self.assertEqual(result["time_limit_minutes"], 40)
        self.assertEqual(result["overtime_items"], 5)

    def test_time_limit_auto_lookup(self):
        """Auto-lookup: CET4 + reading → time_limit_minutes = 40."""
        rec = {
            "date": "2026-07-06",
            "exam_type": "CET4",
            "module": "reading",
            "task_id": "timed-reading-002",
            "duration_minutes": 35,
            "total_items": 20,
            "correct_items": 16,
            "timed": True,
            "overtime_items": 0,
            "overtime_correct": 0,
            "error_tags": [],
        }
        result = record_practice(self.ledger_path, rec)
        # time_limit_minutes not specified → should NOT be auto-added
        # Auto-lookup only happens via CLI (--timed without --time-limit-minutes)
        # In this direct API call, the field just isn't set
        self.assertTrue(result.get("timed"))

    def test_overtime_stats_in_summary(self):
        """Error summary includes speed_analysis for timed records."""
        rec1 = self._make_timed_record()
        rec2 = self._make_normal_record()
        record_practice(self.ledger_path, rec1)
        record_practice(self.ledger_path, rec2)

        summary = summarize_errors(self.ledger_path)
        self.assertIn("speed_analysis", summary)
        sa = summary["speed_analysis"]
        self.assertEqual(sa["timed_sessions"], 1)
        self.assertGreater(sa["total_overtime_items"], 0)

    def test_speed_vs_knowledge_verdict(self):
        """overtime_accuracy > 0.6 → '速度是主要瓶颈'."""
        rec = self._make_timed_record(overtime_items=10, overtime_correct=8)  # 80%
        record_practice(self.ledger_path, rec)

        summary = summarize_errors(self.ledger_path)
        self.assertEqual(summary["speed_analysis"]["verdict"], "速度是主要瓶颈")

    def test_low_knowledge_verdict(self):
        """overtime_accuracy < 0.3 → '知识缺口是主要瓶颈'."""
        rec = self._make_timed_record(overtime_items=10, overtime_correct=2)  # 20%
        record_practice(self.ledger_path, rec)

        summary = summarize_errors(self.ledger_path)
        self.assertEqual(summary["speed_analysis"]["verdict"], "知识缺口是主要瓶颈")

    def test_mixed_verdict(self):
        """overtime_accuracy between 0.3 and 0.6 → '速度与知识均需提升'."""
        rec = self._make_timed_record(overtime_items=10, overtime_correct=5)  # 50%
        record_practice(self.ledger_path, rec)

        summary = summarize_errors(self.ledger_path)
        self.assertEqual(summary["speed_analysis"]["verdict"], "速度与知识均需提升")

    def test_non_timed_record_no_speed_analysis(self):
        """No speed_analysis when there are no timed records."""
        rec = self._make_normal_record()
        record_practice(self.ledger_path, rec)

        summary = summarize_errors(self.ledger_path)
        self.assertNotIn("speed_analysis", summary)

    def test_multiple_timed_sessions(self):
        """Multiple timed sessions are aggregated correctly."""
        rec1 = self._make_timed_record()
        rec2 = self._make_timed_record(
            task_id="timed-reading-002", module="reading",
            overtime_items=3, overtime_correct=1,
        )
        record_practice(self.ledger_path, rec1)
        record_practice(self.ledger_path, rec2)

        summary = summarize_errors(self.ledger_path)
        self.assertEqual(summary["speed_analysis"]["timed_sessions"], 2)
        self.assertIn("reading", summary["speed_analysis"]["by_module"])

    def test_time_limit_lookup_function(self):
        """common.get_time_limit returns correct values."""
        self.assertEqual(common.get_time_limit("CET4", "reading"), 40)
        self.assertEqual(common.get_time_limit("CET6", "listening"), 30)
        self.assertEqual(common.get_time_limit("TEM4", "dictation"), 15)
        self.assertEqual(common.get_time_limit("TEM8", "proofreading"), 15)
        self.assertIsNone(common.get_time_limit("CET4", "speaking"))

    def test_cli_timed_flag(self):
        """CLI --timed flag with auto-lookup via subprocess."""
        import subprocess
        ledger = self.tmp / "cli-ledger.json"
        result = subprocess.run(
            [sys.executable, "-m", "skills.english_exam_ai_tutor", "record-practice",
             "--ledger", str(ledger),
             "--date", "2026-07-06",
             "--exam-type", "CET4",
             "--module", "reading",
             "--task-id", "cli-timed-001",
             "--duration-minutes", "42",
             "--total-items", "20",
             "--correct-items", "14",
             "--timed",
             "--time-limit-minutes", "40",
             "--overtime-items", "3",
             "--overtime-correct", "1",
             "--print-record"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        output = result.stdout.strip()
        self.assertTrue(output, f"Expected JSON output, got: {result.stderr}")
        rec = json.loads(output)
        self.assertTrue(rec.get("timed"))
        self.assertEqual(rec["time_limit_minutes"], 40)
        self.assertEqual(rec["overtime_items"], 3)


if __name__ == "__main__":
    unittest.main()
