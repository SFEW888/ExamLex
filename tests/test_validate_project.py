from __future__ import annotations

import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

from scripts import validate_repo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = Path("skills") / "examlex"
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
    def test_detects_missing_chinese_document_counterpart(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "zh-CN" / "docs" / "roadmap.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any(
                "missing Chinese documentation counterpart" in error
                and "zh-CN/docs/roadmap.md" in error
                for error in result.errors
            )
        )

    def test_detects_external_url_in_published_markdown(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            marker = "https" + "://example.invalid/source"
            readme.write_text(
                readme.read_text(encoding="utf-8") + f"\n{marker}\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("external URL" in error for error in result.errors))

    def test_detects_broken_local_markdown_link(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\n[missing](docs/not-present.md)\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("broken local Markdown link" in error for error in result.errors)
        )

    def test_unpublished_documentation_is_local_only(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        zh_readme = (PROJECT_ROOT / "zh-CN" / "README.md").read_text(encoding="utf-8")
        env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

        self.assertIn("unpublished", readme.lower())
        self.assertIn("尚未发布", zh_readme)
        for text in (readme, zh_readme):
            self.assertNotIn("your-org", text)
            self.assertNotIn("github.com/", text)
        self.assertIn("SILICONFLOW_API_KEY=", env_example)
        self.assertIn("EXAMLEX_PYTHON=python", env_example)
        self.assertNotIn("EXAMLEX_PROMPT_MODE", env_example)

    def test_detects_remote_install_placeholder(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nyour-org/examlex\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("remote install placeholder" in e for e in result.errors))

    def test_current_repo_uses_examlex_identity(self):
        result = validate_repo.validate_project(PROJECT_ROOT)

        self.assertEqual([], result.errors)
        self.assertTrue((PROJECT_ROOT / "examlex" / "__init__.py").is_file())
        self.assertTrue((PROJECT_ROOT / "skills" / "examlex" / "SKILL.md").is_file())

    def test_detects_legacy_product_identifier(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            legacy = "english" + "-exam-ai-tutor"
            (root / "legacy-product-name.txt").write_text(legacy, encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("legacy product identifier" in error for error in result.errors)
        )

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
                "---\nname: examlex\ndescription: Supports exams.\n---\n\n# Skill\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("description" in error and "Use when" in error for error in result.errors))

    def test_detects_mirror_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            script = root / "skills" / "examlex" / "scripts" / "record_practice.py"
            script.write_text(script.read_text(encoding="utf-8") + "\n# mismatch\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("mirror mismatch" in error for error in result.errors))

    def test_detects_resource_mirror_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            package_asset = root / "examlex" / "assets" / "data" / "vocab-test-words.json"
            package_asset.parent.mkdir(parents=True, exist_ok=True)
            package_asset.write_text("{}\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("resource mirror mismatch" in error for error in result.errors)
        )

    def test_importable_package_contains_skill_references(self):
        package_reference = (
            PROJECT_ROOT / "examlex" / "references" / "darwin-rubric.md"
        )

        self.assertTrue(package_reference.is_file(), str(package_reference))

    def test_detects_reference_mirror_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            package_reference = (
                root / "examlex" / "references" / "darwin-rubric.md"
            )
            package_reference.write_text("# mismatch\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any(
                "resource mirror mismatch: references/darwin-rubric.md" in error
                for error in result.errors
            )
        )

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

    def test_detects_missing_examlex_bash_wrapper(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "bin" / "examlex").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing user CLI wrapper: bin/examlex" in error for error in result.errors))

    def test_detects_missing_examlex_powershell_wrapper(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "bin" / "examlex.ps1").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing user CLI wrapper: bin/examlex.ps1" in error for error in result.errors))

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
            readme.write_text("# ExamLex\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("README.md must include" in error for error in result.errors))

    def test_detects_readme_without_public_skill_install_flow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            text = readme.read_text(encoding="utf-8")
            text = text.replace("python -m pip install -e .", "python -m pip --version")
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
            readme.write_text(readme.read_text(encoding="utf-8") + "\nD:\\Codex_project\\英语\\examlex\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("public documentation must not include local machine path" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
