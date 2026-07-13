from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from scripts import smoke_test_wheel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "smoke_test_wheel.py"


class WheelSmokeScriptTests(unittest.TestCase):
    def test_run_checked_decodes_utf8_output_on_windows(self):
        completed = subprocess.CompletedProcess([], 0, stdout="通过", stderr="")

        with mock.patch.object(smoke_test_wheel.subprocess, "run", return_value=completed) as run:
            result = smoke_test_wheel.run_checked(["examlex", "--help"], PROJECT_ROOT, {})

        self.assertEqual("通过", result.stdout)
        self.assertEqual("utf-8", run.call_args.kwargs["encoding"])
        self.assertEqual("replace", run.call_args.kwargs["errors"])

    def test_run_checked_does_not_echo_command_or_process_output_on_failure(self):
        private_value = "private local path and credential"
        completed = subprocess.CompletedProcess(
            [], 1, stdout=private_value, stderr=private_value
        )

        with mock.patch.object(smoke_test_wheel.subprocess, "run", return_value=completed):
            with self.assertRaises(RuntimeError) as raised:
                smoke_test_wheel.run_checked(
                    ["python", private_value], PROJECT_ROOT, {}
                )

        self.assertNotIn(private_value, str(raised.exception))

    def test_smoke_script_exposes_help(self):
        self.assertTrue(SMOKE_SCRIPT.is_file())

        result = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("wheel", result.stdout.lower())

    def test_smoke_script_checks_commands_and_packaged_resources(self):
        source = SMOKE_SCRIPT.read_text(encoding="utf-8")

        self.assertIn('"resume", "--help"', source)
        self.assertIn('"prompt-check", "--help"', source)
        self.assertIn('"tutor-prepare", "--help"', source)
        self.assertIn('"source-collect", "--help"', source)
        self.assertIn('"source-fetch", "--help"', source)
        self.assertIn('"source-list", "--collectable", "--json"', source)
        self.assertIn("'assets/schemas': root / 'assets' / 'schemas'", source)
        self.assertIn("'assets/templates': root / 'assets' / 'templates'", source)
        self.assertIn("'references': root / 'references'", source)
        self.assertIn("'tutor-role-contracts': root / 'references'", source)
        self.assertIn("'tutor-runtime': root / 'references'", source)
        self.assertIn("'source-collection': root / 'references'", source)
        self.assertIn("'source-catalog': root / 'assets' / 'data'", source)
        self.assertIn("load_role_contracts", source)
        self.assertIn("prepare_tutor_turn", source)
        self.assertIn("load_source_catalog", source)
        self.assertIn("'SKILL.md': root / 'SKILL.md'", source)
