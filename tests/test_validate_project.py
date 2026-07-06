from __future__ import annotations

import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

from scripts import validate_repo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = Path("skills") / "english-exam-ai-tutor"
TEMP_ROOT = PROJECT_ROOT / ".task8-test-tmp"


@contextmanager
def copy_project():
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    tempdir = TEMP_ROOT / f"repo-{uuid.uuid4().hex}"
    target = tempdir / "repo"
    try:
        shutil.copytree(
            PROJECT_ROOT,
            target,
            ignore=shutil.ignore_patterns(".git", ".worktrees", ".task8-test-tmp", ".tmp-test", "test-artifacts", "__pycache__", "*.pyc"),
        )
        yield str(tempdir)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


class ValidateProjectTests(unittest.TestCase):
    def test_current_repo_is_valid_without_readme_warning(self):
        result = validate_repo.validate_project(PROJECT_ROOT)

        self.assertEqual([], result.errors)
        self.assertEqual([], result.warnings)

    def test_reports_missing_required_portable_directory(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            shutil.rmtree(root / SKILL_DIR / "assets")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("assets" in error for error in result.errors))

    def test_detects_forbidden_private_prompt_sentence(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            skill = root / SKILL_DIR / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8")
                + "\n"
                + " ".join(("Act as a strict", "but helpful English", "grammar teacher"))
                + "\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("forbidden private prompt" in error for error in result.errors))

    def test_detects_metadata_issue(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            skill = root / SKILL_DIR / "SKILL.md"
            skill.write_text(
                "---\nname: english-exam-ai-tutor\ndescription: Supports exams.\n---\n\n# Skill\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("description" in error and "Use when" in error for error in result.errors))

    def test_detects_mirror_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            script = root / "skills" / "english_exam_ai_tutor" / "scripts" / "record_practice.py"
            script.write_text(script.read_text(encoding="utf-8") + "\n# mismatch\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("mirror mismatch" in error for error in result.errors))

    def test_detects_missing_github_health_file(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "SECURITY.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing GitHub health file: SECURITY.md" in error for error in result.errors))

    def test_detects_missing_github_issue_template(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing GitHub issue template" in error for error in result.errors))

    def test_detects_missing_ci_workflow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".github" / "workflows" / "ci.yml").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing GitHub workflow" in error for error in result.errors))

    def test_detects_missing_editorconfig(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".editorconfig").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing project quality file: .editorconfig" in error for error in result.errors))

    def test_detects_missing_env_example(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".env.example").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing project quality file: .env.example" in error for error in result.errors))

    def test_detects_missing_public_install_entrypoint(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "install.sh").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing required root file: install.sh" in error for error in result.errors))

    def test_detects_missing_root_skill_for_one_line_installers(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "SKILL.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing required root file: SKILL.md" in error for error in result.errors))

    def test_detects_missing_cli_reference(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "cli-reference.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing required root file: cli-reference.md" in error for error in result.errors))

    def test_detects_missing_tutor_bash_wrapper(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "bin" / "tutor").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing user CLI wrapper: bin/tutor" in error for error in result.errors))

    def test_detects_missing_tutor_powershell_wrapper(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "bin" / "tutor.ps1").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing user CLI wrapper: bin/tutor.ps1" in error for error in result.errors))

    def test_detects_missing_quality_documentation(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "docs" / "getting-started.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing quality documentation" in error for error in result.errors))

    def test_detects_missing_codeql_workflow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".github" / "workflows" / "codeql.yml").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing GitHub workflow" in error for error in result.errors))

    def test_detects_missing_readme_quality_section(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text("# English Exam AI Tutor\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("README.md must include" in error for error in result.errors))

    def test_detects_readme_without_public_skill_install_flow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            text = readme.read_text(encoding="utf-8")
            text = text.replace("$HOME\\.agents\\skills", "$HOME\\agents\\skills")
            text = text.replace("$HOME\\.claude\\skills", "$HOME\\claude\\skills")
            text = text.replace(".agents\\skills", "agents\\skills")
            text = text.replace(".claude\\skills", "claude\\skills")
            readme.write_text(text, encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("README.md Quick Start must explain Skill installation" in error for error in result.errors))

    def test_detects_readme_without_agent_skill_invocation_flow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            text = readme.read_text(encoding="utf-8")
            text = text.replace("/grammar-corrector", "/grammar-check")
            readme.write_text(text, encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("README.md must explain Agent Skill invocation" in error for error in result.errors))

    def test_detects_dollar_style_readme_skill_invocation(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\n" + "$" + "grammar-corrector\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("slash Skill invocation" in error for error in result.errors))

    def test_detects_dollar_style_skill_invocation_outside_readme(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            usage = root / "docs" / "usage.md"
            usage.write_text(usage.read_text(encoding="utf-8") + "\n" + "$" + "learning-planner\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("forbidden dollar-style Skill call" in error for error in result.errors))

    def test_detects_missing_shortcut_skill(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            shutil.rmtree(root / "skills" / "grammar-corrector")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing shortcut Skill" in error for error in result.errors))

    def test_detects_shortcut_skill_metadata_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            shortcut = root / "skills" / "grammar-corrector" / "SKILL.md"
            shortcut.write_text("---\nname: grammar-check\ndescription: Supports grammar.\n---\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Shortcut Skill grammar-corrector" in error for error in result.errors))

    def test_detects_local_machine_path_in_public_docs(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\nD:\\Codex_project\\英语\\english-exam-ai-tutor\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("public documentation must not include local machine path" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
