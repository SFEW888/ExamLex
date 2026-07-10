"""Tests for operational readiness checks."""
import unittest
from unittest import mock

from examlex.scripts.ops import (
    run_all_checks,
    check_environment,
    check_config,
    check_permissions,
    check_safety_limits,
    check_scheduler,
    OpsReport,
    CheckResult,
)
from examlex.scripts.config import TutorConfig


class OpsCheckTests(unittest.TestCase):
    def setUp(self):
        self.cfg = TutorConfig()

    def test_run_all_returns_report(self):
        report = run_all_checks(self.cfg)
        self.assertIsInstance(report, OpsReport)
        self.assertGreater(len(report.checks), 0)
        self.assertIn("pass", report.summary)

    def test_check_environment(self):
        result = check_environment(self.cfg)
        self.assertIsInstance(result, CheckResult)
        self.assertIn(result.status, ("pass", "warn", "fail"))

    def test_check_config_valid(self):
        result = check_config(self.cfg)
        self.assertEqual(result.status, "pass")

    def test_check_config_invalid_threshold(self):
        cfg = TutorConfig(darwin_pass_score=150)
        result = check_config(cfg)
        self.assertEqual(result.status, "fail")

    def test_check_permissions(self):
        result = check_permissions(self.cfg)
        self.assertEqual(result.status, "pass")

    def test_check_safety_limits(self):
        result = check_safety_limits(self.cfg)
        self.assertIn(result.status, ("pass", "warn"))

    def test_check_safety_limits_bad_values(self):
        cfg = TutorConfig(max_video_duration_seconds=100000, darwin_max_rounds=20)
        result = check_safety_limits(cfg)
        self.assertEqual(result.status, "warn")

    def test_check_scheduler(self):
        result = check_scheduler(self.cfg)
        self.assertEqual(result.status, "pass")
        self.assertIn("examlex cron-create", result.detail["recommendation"])
        self.assertNotIn("tutor" + " cron-create", result.detail["recommendation"])

    def test_report_all_pass(self):
        report = OpsReport(
            timestamp="2026-01-01", hostname="test", platform="test",
            python_version="3.13",
            checks=[CheckResult("test", "pass", "ok")],
            summary={"pass": 1, "warn": 0, "fail": 0, "skip": 0},
        )
        self.assertTrue(report.all_pass())

    def test_report_with_failure(self):
        report = OpsReport(
            timestamp="2026-01-01", hostname="test", platform="test",
            python_version="3.13",
            checks=[CheckResult("test", "fail", "bad")],
            summary={"pass": 0, "warn": 0, "fail": 1, "skip": 0},
        )
        self.assertFalse(report.all_pass())

    def test_cli_ops_runs(self):
        from examlex.scripts.cli_ops import main
        ret = main(["--json"])
        self.assertIn(ret, (0, 1))  # 0=all pass, 1=some warn/fail


class OpsJSONOutputTests(unittest.TestCase):
    """Verify ops-check --json produces valid output."""

    def test_json_output_is_valid(self):
        import json, io, sys
        from examlex.scripts.cli_ops import main

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            main(["--json"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        data = json.loads(output)
        self.assertIn("summary", data)
        self.assertIn("checks", data)
        self.assertIn("timestamp", data)


if __name__ == "__main__":
    unittest.main()
