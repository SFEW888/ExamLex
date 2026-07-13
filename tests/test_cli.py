import io
import json
import shutil
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from examlex import cli
from examlex.scripts.session import SessionManager


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_resume_command_returns_existing_session_guidance(self):
        sessions_root = Path("test-artifacts") / "cli-resume-sessions"
        shutil.rmtree(sessions_root, ignore_errors=True)
        try:
            session = SessionManager(sessions_root).create(source_type="video")
            session.checkpoint("extract", sub_stage="downloaded")
            output = io.StringIO()

            with redirect_stdout(output):
                result = cli.main([
                    "resume",
                    session.session_id,
                    "--sessions-root",
                    str(sessions_root),
                    "--json",
                ])

            self.assertEqual(0, result)
            payload = json.loads(output.getvalue())
            self.assertEqual("extract", payload["current_stage"])
            self.assertEqual("downloaded", payload["sub_stage"])
        finally:
            shutil.rmtree(sessions_root, ignore_errors=True)

    def test_english_cli_examples_match_runtime_signatures(self):
        text = (PROJECT_ROOT / "cli-reference.md").read_text(encoding="utf-8")

        self.assertIn("validate-profile --profile <profile>", text)
        self.assertNotIn("--score <number>", text)
        self.assertIn(
            "writing-version --file <versions.json> --writing-id <writing-id> --text <essay>",
            text,
        )
        self.assertNotIn("text|book|video|person|manual", text)

    def test_bilingual_workflows_pass_the_strategy_library_to_planning(self):
        for path in (
            PROJECT_ROOT / "skills/examlex/references/workflow.md",
            PROJECT_ROOT / "zh-CN/skill/references/workflow.md",
        ):
            with self.subTest(path=path):
                self.assertIn("--strategies strategy-library.json", path.read_text(encoding="utf-8"))

    def test_bilingual_docs_describe_controlled_growth_and_review_only_duplicates(self):
        english = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (PROJECT_ROOT / "zh-CN" / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "Local strategy data grows in a controlled way as effective new material is added",
            english,
        )
        self.assertIn("本地策略数据会随有效新资料受控增长", chinese)
        for text in (english, chinese):
            self.assertIn("168", text)
            self.assertIn("4 GiB", text)
            self.assertIn("100 MiB", text)
            self.assertIn("--duplicates", text)

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
