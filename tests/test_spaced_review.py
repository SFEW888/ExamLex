from __future__ import annotations

import datetime
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO_ROOT / "skills" / "english-exam-ai-tutor" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import common
from summarize_errors import summarize_errors, compute_review_urgency
from record_practice import record_practice
from generate_daily_plan import generate_daily_plan


class TestSpacedReview(unittest.TestCase):
    def setUp(self):
        self.tmp = REPO_ROOT / ".task8-test-tmp" / "test_spaced_review"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.tmp / "practice-ledger.json"
        if self.ledger_path.exists():
            self.ledger_path.unlink()

    def _make_record(self, date: str, tags: list[str]):
        return {
            "date": date,
            "exam_type": "CET4",
            "module": "writing",
            "task_id": f"task-{date}",
            "duration_minutes": 30,
            "total_items": 10,
            "correct_items": 7,
            "error_tags": tags,
        }

    def test_urgency_zero_for_never_seen_tag(self):
        """A tag never seen returns urgency 0."""
        rec = self._make_record("2026-07-01", ["VOCAB_SPELLING_FAIL"])
        record_practice(self.ledger_path, rec)
        _, urgency = compute_review_urgency(
            "WRITING_TASK_RESPONSE_WEAK",
            [rec],
            datetime.date(2026, 7, 6),
        )
        self.assertEqual(urgency, 0.0)

    def test_urgency_increases_with_days(self):
        """More days since last practice → higher urgency."""
        today = datetime.date(2026, 7, 6)
        rec_old = self._make_record("2026-06-06", ["VOCAB_SPELLING_FAIL"])  # 30 days
        rec_new = self._make_record("2026-07-05", ["WRITING_ARTICLE_OMISSION"])  # 1 day

        _, urg_old = compute_review_urgency("VOCAB_SPELLING_FAIL", [rec_old], today)
        _, urg_new = compute_review_urgency("WRITING_ARTICLE_OMISSION", [rec_new], today)
        self.assertGreater(urg_old, urg_new,
                           f"30d urgency ({urg_old}) should > 1d urgency ({urg_new})")

    def test_severity_weight_matters(self):
        """Higher severity weight → higher urgency (same days, not capped)."""
        today = datetime.date(2026, 7, 6)
        # Use recent dates so urgency isn't capped at 1.0
        # WRITING_TASK_RESPONSE_WEAK: 0.9, VOCAB_SPELLING_FAIL: 0.5
        rec1 = self._make_record("2026-07-02", ["WRITING_TASK_RESPONSE_WEAK"])  # 4 days ago
        rec2 = self._make_record("2026-07-02", ["VOCAB_SPELLING_FAIL"])          # 4 days ago
        _, urg_high = compute_review_urgency("WRITING_TASK_RESPONSE_WEAK", [rec1], today)
        _, urg_low = compute_review_urgency("VOCAB_SPELLING_FAIL", [rec2], today)
        self.assertGreater(urg_high, urg_low,
                           f"0.9 weight ({urg_high}) should > 0.5 weight ({urg_low})")

    def test_urgency_capped_at_one(self):
        """Extreme case: urgency never exceeds 1.0."""
        today = datetime.date(2026, 7, 6)
        # Very old record with high severity, repeated daily
        records = []
        for d in range(1, 31):
            records.append(self._make_record(
                f"2026-06-{d:02d}", ["WRITING_TASK_RESPONSE_WEAK"]
            ))
        _, urgency = compute_review_urgency("WRITING_TASK_RESPONSE_WEAK", records, today)
        self.assertLessEqual(urgency, 1.0)

    def test_plan_includes_urgent_review(self):
        """Error summary with high urgency → plan includes spaced review task."""
        for d in range(10, 20):
            rec = self._make_record(f"2026-06-{d:02d}", ["WRITING_TASK_RESPONSE_WEAK"])
            record_practice(self.ledger_path, rec)

        summary = summarize_errors(self.ledger_path)
        profile = {"learner_id": "test", "exam_type": "CET4", "daily_time_budget_minutes": 60}
        ability = {"modules": {}}
        plan = generate_daily_plan(profile, ability, error_summary=summary)

        review_tasks = [t for t in plan["tasks"] if "spaced review" in t.get("reason", "")]
        self.assertGreater(len(review_tasks), 0,
                           f"Expected spaced review tasks, got tasks: {plan['tasks']}")

    def test_summary_includes_review_urgency(self):
        """summarize_errors output includes review_urgency in by_tag."""
        rec = self._make_record("2026-06-20", ["WRITING_ARTICLE_OMISSION"])
        record_practice(self.ledger_path, rec)

        summary = summarize_errors(self.ledger_path)
        self.assertIn("WRITING_ARTICLE_OMISSION", summary["by_tag"])
        tag_data = summary["by_tag"]["WRITING_ARTICLE_OMISSION"]
        self.assertIn("review_urgency", tag_data)
        self.assertIn("last_practice_date", tag_data)

    def test_plan_min_guaranteed_time(self):
        """Spaced review task gets at least MIN_TASK_MINUTES if urgent."""
        for d in range(1, 15):
            rec = self._make_record(f"2026-06-{d:02d}", ["WRITING_TASK_RESPONSE_WEAK"])
            record_practice(self.ledger_path, rec)

        summary = summarize_errors(self.ledger_path)
        profile = {"learner_id": "test", "exam_type": "CET4", "daily_time_budget_minutes": 60}
        ability = {"modules": {}}
        plan = generate_daily_plan(profile, ability, error_summary=summary)

        for t in plan["tasks"]:
            if "spaced review" in t.get("reason", ""):
                self.assertGreaterEqual(t["minutes"], 10)


if __name__ == "__main__":
    unittest.main()
