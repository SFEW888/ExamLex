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
            ignore=shutil.ignore_patterns(".git", ".worktrees", ".task8-test-tmp", "test-artifacts", "__pycache__", "*.pyc"),
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


if __name__ == "__main__":
    unittest.main()
