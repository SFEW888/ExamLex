"""Tests for operational readiness checks."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from examlex.scripts.ops import (
    run_all_checks,
    check_environment,
    check_config,
    check_permissions,
    check_network,
    check_dry_run,
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
        report = run_all_checks(self.cfg, include_network=False)
        self.assertIsInstance(report, OpsReport)
        self.assertGreater(len(report.checks), 0)
        self.assertIn("pass", report.summary)
        self.assertEqual("<redacted>", report.hostname)

    def test_ops_report_does_not_expose_local_machine_identity_or_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = TutorConfig(sessions_root=Path(temp) / "private-sessions")
            report = run_all_checks(cfg, include_network=False)

        rendered = json.dumps(
            {
                "hostname": report.hostname,
                "checks": [check.detail for check in report.checks],
            }
        )
        self.assertNotIn(temp, rendered)
        self.assertNotIn(str(Path.cwd()), rendered)
        self.assertEqual("<redacted>", report.hostname)

    @mock.patch("examlex.scripts.ops.check_network")
    def test_offline_report_skips_live_network_checks(self, mock_network):
        report = run_all_checks(self.cfg, include_network=False)

        network = next(check for check in report.checks if check.name == "network")
        self.assertEqual("skip", network.status)
        self.assertTrue(network.detail["offline"])
        mock_network.assert_not_called()

    @mock.patch("examlex.scripts.ops.build_opener")
    @mock.patch("examlex.scripts.ops.urlopen")
    @mock.patch.dict("os.environ", {"SILICONFLOW_API_KEY": "sk-test-value"})
    def test_network_check_does_not_echo_transport_errors(
        self, mock_urlopen, mock_build_opener
    ):
        private_detail = "private proxy credentials"
        mock_urlopen.side_effect = RuntimeError(private_detail)
        mock_build_opener.return_value.open.side_effect = RuntimeError(private_detail)

        result = check_network()

        rendered = json.dumps(result.detail)
        self.assertNotIn(private_detail, rendered)
        self.assertEqual("unreachable", result.detail["bilibili"])
        self.assertEqual("unreachable", result.detail["siliconflow_api"])

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

    def test_dry_run_keeps_real_strategy_library_byte_stable(self):
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "strategy-library.json"
            original = b'{  "strategies" : [ ] }\r\n'
            library.write_bytes(original)

            result = check_dry_run(self.cfg, str(library))

            self.assertEqual("pass", result.status, result.remedy)
            self.assertEqual(original, library.read_bytes())

    @mock.patch("examlex.scripts.ops.platform.system", return_value="Windows")
    def test_check_scheduler_windows_has_actionable_recommendation(self, _mock_system):
        result = check_scheduler(self.cfg)
        self.assertEqual(result.status, "pass")
        self.assertIn("Task Scheduler", result.detail["recommendation"])
        self.assertIn("examlex", result.detail["recommendation"])
        self.assertNotIn("cron-create", result.detail["recommendation"])

    @mock.patch("examlex.scripts.ops.shutil.which", return_value="/usr/bin/crontab")
    @mock.patch("examlex.scripts.ops.platform.system", return_value="Linux")
    def test_check_scheduler_linux_has_actionable_recommendation(
        self, _mock_system, _mock_which
    ):
        result = check_scheduler(self.cfg)
        self.assertEqual(result.status, "pass")
        self.assertTrue(result.detail["cron_available"])
        self.assertIn("crontab", result.detail["recommendation"])
        self.assertIn("examlex", result.detail["recommendation"])
        self.assertNotIn("cron-create", result.detail["recommendation"])

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
        ret = main(["--json", "--offline"])
        self.assertIn(ret, (0, 1))  # 0=all pass, 1=some warn/fail


class OpsJSONOutputTests(unittest.TestCase):
    """Verify ops-check --json produces valid output."""

    def test_json_output_is_valid(self):
        from examlex.scripts.cli_ops import main

        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            main(["--json", "--offline"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        data = json.loads(output)
        self.assertIn("summary", data)
        self.assertIn("checks", data)
        self.assertIn("timestamp", data)

    def test_json_output_is_portable_on_non_utf8_windows_console(self):
        from examlex.scripts.cli_ops import main

        report = OpsReport(
            timestamp="2026-07-11T00:00:00+00:00",
            hostname="test host",
            platform="Windows",
            python_version="3.10",
            checks=[
                CheckResult(
                    name="environment",
                    status="pass",
                    message="Chinese test message: \u4e2d\u6587",
                    detail={"path": "C:\\\\Users\\\\test"},
                )
            ],
            summary={"pass": 1, "warn": 0, "fail": 0, "skip": 0},
        )

        raw_output = io.BytesIO()
        cp1252_stdout = io.TextIOWrapper(raw_output, encoding="cp1252", newline="")
        with mock.patch(
            "examlex.scripts.cli_ops.run_all_checks", return_value=report
        ), mock.patch("sys.stdout", cp1252_stdout):
            return_code = main(["--json"])
            cp1252_stdout.flush()

        output = raw_output.getvalue().decode("cp1252")
        self.assertEqual(return_code, 0)
        self.assertIn("checks", json.loads(output))
        self.assertIn("\\u", output)


if __name__ == "__main__":
    unittest.main()
