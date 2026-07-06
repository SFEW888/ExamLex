import unittest
from pathlib import Path

from skills.english_exam_ai_tutor import cli


class CliTests(unittest.TestCase):
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
