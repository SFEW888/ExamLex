"""Regression tests: malformed user/library JSON must never crash a whole command.

Each test feeds a structurally-wrong-but-valid-JSON input (null, a list where an
object is expected, a scalar where a list is expected, a string where a number is
expected, or an unhashable value) to a command that reads it, and asserts the
command degrades gracefully — a reported issue, a clean ValueError, or a skipped
entry — instead of raising an uncaught AttributeError/TypeError/KeyError.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from examlex.scripts import (
    analyze_trends,
    cleanup_sessions,
    generate_daily_plan,
    ingest_strategy,
    ops,
    validate_exam_artifact,
    validate_strategy,
    visualize,
)
from examlex.scripts.config import TutorConfig


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class MalformedInputHardeningTests(unittest.TestCase):
    # ---- ops.py ----

    def test_check_logs_tolerates_non_dict_pipeline_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write(root / "s1" / "pipeline_state.json", [1, 2, 3])
            _write(root / "s2" / "pipeline_state.json", None)
            cfg = TutorConfig(sessions_root=root)
            result = ops.check_logs(cfg)  # must not raise
            self.assertIn(result.status, ("pass", "warn"))

    def test_check_business_results_tolerates_non_dict_library(self):
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "lib.json"
            _write(library, ["not", "a", "dict"])
            result = ops.check_business_results(str(library))
            self.assertEqual("warn", result.status)
            self.assertIn("malformed", result.remedy)

    def test_check_business_results_tolerates_null_strategies(self):
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "lib.json"
            _write(library, {"strategies": None})
            result = ops.check_business_results(str(library))
            self.assertEqual("warn", result.status)
            self.assertIn("malformed", result.remedy)

    def test_check_dry_run_reports_failure_on_malformed_library(self):
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "lib.json"
            _write(library, [])  # a list reaches the ratchet step -> AttributeError
            result = ops.check_dry_run(TutorConfig(), str(library))
            # Broadened except turns the ratchet crash into a reported failure.
            self.assertEqual("fail", result.status)

    # ---- cleanup_sessions.py ----

    def test_scan_sessions_tolerates_non_dict_pipeline_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # 2-level date/session layout required by the scanner.
            _write(root / "2026-01-01" / "sess" / "pipeline_state.json", "just a string")
            stale = cleanup_sessions.find_stale_sessions(root, 1.0)  # must not raise
            self.assertEqual([], stale)

    # ---- analyze_trends.py ----

    def test_analyze_trends_tolerates_non_dict_ledger_records(self):
        ledger = [123, "x", None, {"module": "reading", "total_items": 10, "correct_items": 5}]
        result = analyze_trends.analyze_trends(ledger=ledger)  # must not raise
        self.assertEqual(4, result["inputs"]["ledger_records"])

    # ---- generate_daily_plan.py ----

    def test_generate_daily_plan_tolerates_non_dict_errors_and_scalar_vocab(self):
        profile = {"daily_time_budget_minutes": 30}
        ability_profile = {"modules": {}}
        # error_summary is a truthy non-dict (hits _priority_error AND the
        # review-urgent path); vocab_pool is a scalar (hits select_daily_vocab).
        plan = generate_daily_plan.generate_daily_plan(
            profile, ability_profile, error_summary=[1, 2], vocab_pool=5
        )
        self.assertIn("tasks", plan)

    # ---- visualize.py ----

    def test_generate_report_tolerates_malformed_ability_history(self):
        # Last element non-dict; and a string per-node level.
        ability_history = [
            {"modules": {"reading": [{"level": "high"}]}},
            "garbage-not-a-dict",
        ]
        html = visualize.generate_report(ability_history, [])  # must not raise
        self.assertIn("<!DOCTYPE html>", html)

    def test_generate_report_tolerates_malformed_error_summary(self):
        ability = [{"modules": {}}]
        # Non-dict by_tag entry with string numeric fields → coerced to 0.
        error_summary = {"by_tag": {"t": {"count": "lots", "percentage": "x", "review_urgency": "y"}}}
        html = visualize.generate_report(ability, [], error_summary=error_summary)
        self.assertIn("<table", html)
        # A wholly non-dict error_summary must also be tolerated.
        html2 = visualize.generate_report(ability, [], error_summary=["nope"])
        self.assertIn("No error data available.", html2)

    # ---- validate_strategy.py ----

    def test_validate_library_tolerates_unhashable_enum_member(self):
        library = {
            "strategies": [
                {
                    "strategy_id": "s1",
                    "title": "T",
                    "exam_types": [["CET4"]],  # unhashable member
                    "modules": ["reading"],
                    "content": "x" * 30,
                    "source_file": "s.md",
                    "added_at": "2026-01-01",
                }
            ]
        }
        report = validate_strategy.validate_library(library)  # must not raise
        self.assertGreaterEqual(report["summary"]["total_error"], 1)

    # ---- validate_exam_artifact.py ----

    def test_load_profiles_raises_clean_value_error_on_list(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = Path(temp) / "profiles.json"
            _write(profiles, [])  # a list, not an object
            with self.assertRaises(ValueError):
                validate_exam_artifact.load_profiles(profiles)

    def test_validate_answerbook_tolerates_non_dict_paper(self):
        profiles = validate_exam_artifact.load_profiles()
        answerbook = {
            "schema_version": 1,
            "artifact_type": "answerbook",
            "official_status": "simulation_not_official",
            "detail_level": "detailed",
            "paper_id": "p1",
            "exam_type": "CET4",
            "answers": [],
        }
        # paper is a list: the cross-check must be skipped, not crash.
        errors = validate_exam_artifact.validate_answerbook(answerbook, profiles, paper=[])
        self.assertIsInstance(errors, list)

    # ---- ingest_strategy.py ----

    def test_ingest_strategy_tolerates_unhashable_existing_strategy_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            library = root / "library.json"
            _write(library, {"strategies": [{"strategy_id": {"nested": "dict"}, "title": "bad"}]})
            source = root / "note.md"
            source.write_text(
                "Read the stem, locate the evidence sentence, compare each option to it.",
                encoding="utf-8",
            )
            result = ingest_strategy.ingest_strategy(
                file_path=source,
                library_path=library,
                exam_types=["CET4"],
                modules=["reading"],
            )  # must not raise on the unhashable existing id
            self.assertIsInstance(result["strategy_id"], str)


if __name__ == "__main__":
    unittest.main()
