import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from examlex import cli


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_documented_short_aliases_are_registered(self):
        for alias in ("vocab", "report", "validate", "commit"):
            with self.subTest(alias=alias):
                self.assertIn(alias, cli.ALL_COMMANDS)

    def test_help_uses_examlex_program_name(self):
        output = io.StringIO()
        with self.assertRaises(SystemExit) as raised, redirect_stdout(output):
            cli.main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("usage: examlex", output.getvalue())

    def test_bilingual_cli_references_cover_registered_commands(self):
        references = (
            PROJECT_ROOT / "cli-reference.md",
            PROJECT_ROOT / "zh-CN" / "cli-reference.md",
        )

        for reference in references:
            text = reference.read_text(encoding="utf-8")
            for command in cli.ALL_COMMANDS:
                with self.subTest(reference=reference.name, command=command):
                    self.assertIn(command, text)

    def test_validate_profile_command_dispatches(self):
        result = cli.main(["validate-profile", "--profile", "examples/sample-learner-profile.yaml"])

        self.assertEqual(result, 0)

    def test_daily_plan_command_dispatches(self):
        output = Path("test-artifacts") / "cli-daily-plan.json"
        output.parent.mkdir(exist_ok=True)
        try:
            result = cli.main(
                [
                    "daily-plan",
                    "--profile",
                    "examples/sample-learner-profile.yaml",
                    "--ability",
                    "examples/sample-ability-profile.yaml",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 0)
            self.assertTrue(output.exists())
        finally:
            if output.exists():
                output.unlink()

    def test_short_check_alias_accepts_positional_profile(self):
        result = cli.main(["check", "examples/sample-learner-profile.yaml"])

        self.assertEqual(result, 0)

    def test_short_plan_alias_accepts_positional_profile(self):
        output = Path("test-artifacts") / "cli-short-plan.json"
        output.parent.mkdir(exist_ok=True)
        try:
            result = cli.main(
                [
                    "plan",
                    "examples/sample-learner-profile.yaml",
                    "--ability",
                    "examples/sample-ability-profile.yaml",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 0)
            self.assertTrue(output.exists())
        finally:
            if output.exists():
                output.unlink()


if __name__ == "__main__":
    unittest.main()
