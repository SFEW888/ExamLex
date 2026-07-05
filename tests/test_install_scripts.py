from __future__ import annotations

import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
import shutil

from scripts import install_claude, install_codex, install_cursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "skills" / "english-exam-ai-tutor"
TEMP_ROOT = PROJECT_ROOT / ".task8-test-tmp"


@contextmanager
def temp_dir():
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEMP_ROOT / f"install-{uuid.uuid4().hex}"
    path.mkdir()
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


class InstallScriptTests(unittest.TestCase):
    def test_dry_run_does_not_write_files(self):
        with temp_dir() as temp:
            dest = Path(temp) / "skills"

            result = install_codex.install_skill(SOURCE, dest, dry_run=True)

            self.assertTrue(result.dry_run)
            self.assertFalse((dest / "english-exam-ai-tutor").exists())

    def test_copies_skill_to_temp_destination(self):
        with temp_dir() as temp:
            dest = Path(temp) / "skills"

            result = install_claude.install_skill(SOURCE, dest)

            self.assertEqual(dest / "english-exam-ai-tutor", result.target)
            self.assertTrue((result.target / "SKILL.md").exists())
            self.assertTrue((result.target / "references" / "workflow.md").exists())

    def test_refuses_overwrite_without_force(self):
        with temp_dir() as temp:
            dest = Path(temp) / "skills"
            install_cursor.install_skill(SOURCE, dest)

            with self.assertRaisesRegex(FileExistsError, "--force"):
                install_cursor.install_skill(SOURCE, dest)

    def test_force_overwrites_existing_destination(self):
        with temp_dir() as temp:
            dest = Path(temp) / "skills"
            result = install_codex.install_skill(SOURCE, dest)
            marker = result.target / "obsolete.txt"
            marker.write_text("old", encoding="utf-8")

            install_codex.install_skill(SOURCE, dest, force=True)

            self.assertFalse(marker.exists())
            self.assertTrue((result.target / "SKILL.md").exists())

    def test_copy_excludes_pycache_and_pyc_files(self):
        with temp_dir() as temp:
            source = Path(temp) / "source" / "english-exam-ai-tutor"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: x\ndescription: Use when x.\n---\n", encoding="utf-8")
            pycache = source / "scripts" / "__pycache__"
            pycache.mkdir(parents=True)
            (pycache / "ignored.pyc").write_bytes(b"cache")
            (source / "scripts" / "kept.py").write_text("print('ok')\n", encoding="utf-8")
            (source / "scripts" / "ignored.pyc").write_bytes(b"cache")
            dest = Path(temp) / "dest"

            result = install_claude.install_skill(source, dest)

            self.assertTrue((result.target / "scripts" / "kept.py").exists())
            self.assertFalse((result.target / "scripts" / "__pycache__").exists())
            self.assertFalse((result.target / "scripts" / "ignored.pyc").exists())


if __name__ == "__main__":
    unittest.main()
