from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
import shutil

from scripts import install_claude, install_codex, install_cursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "skills" / "examlex"
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
    def test_copied_main_skill_runs_bundled_cli_without_repository(self):
        with temp_dir() as temp:
            dest = Path(temp) / "skills"
            result = install_codex.install_skill(SOURCE, dest)
            environment = os.environ.copy()
            environment.pop("PYTHONPATH", None)
            environment["PYTHONNOUSERSITE"] = "1"

            completed = subprocess.run(
                [sys.executable, str(result.target / "run.py"), "--help"],
                cwd=temp,
                env=environment,
                text=True,
                capture_output=True,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("usage: examlex", completed.stdout)

    def test_posix_entrypoints_are_executable_and_forced_to_lf(self):
        indexed = subprocess.check_output(
            ["git", "ls-files", "-s", "--", "install.sh", "bin/examlex"],
            cwd=PROJECT_ROOT,
            text=True,
        )
        attributes = (PROJECT_ROOT / ".gitattributes").read_text(encoding="utf-8")

        self.assertEqual(2, indexed.count("100755"), indexed)
        self.assertIn("*.sh text eol=lf", attributes)
        self.assertIn("bin/examlex text eol=lf", attributes)

    def test_cursor_default_destination_is_skills_directory(self):
        self.assertEqual(
            install_cursor.default_dest(), Path.home() / ".cursor" / "skills"
        )

    def test_wrappers_use_safe_cursor_project_path_and_no_force_default(self):
        powershell = (PROJECT_ROOT / "install.ps1").read_text(encoding="utf-8")
        shell = (PROJECT_ROOT / "install.sh").read_text(encoding="utf-8")

        self.assertIn('[switch]$Force', powershell)
        self.assertNotIn("if (-not $NoForce)", powershell)
        self.assertIn('.cursor\\skills', powershell)
        self.assertIn("force=false", shell)
        self.assertIn('.cursor/skills', shell)

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper test requires Windows")
    def test_powershell_wrapper_rejects_python_3_9_before_install(self):
        with temp_dir() as temp:
            fake_python = Path(temp) / "python.cmd"
            fake_python.write_text(
                '@echo off\r\nif "%1"=="-c" echo 3.9.18\r\nexit /b 0\r\n',
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PATH"] = temp
            powershell = (
                Path(os.environ.get("SystemRoot", r"C:\Windows"))
                / "System32/WindowsPowerShell/v1.0/powershell.exe"
            )

            result = subprocess.run(
                [
                    str(powershell),
                    "-NoProfile",
                    "-File",
                    str(PROJECT_ROOT / "install.ps1"),
                    "cursor",
                    "-DryRun",
                ],
                cwd=temp,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3.10+ is required", result.stderr + result.stdout)

    def test_dry_run_does_not_write_files(self):
        with temp_dir() as temp:
            dest = Path(temp) / "skills"

            result = install_codex.install_skill(SOURCE, dest, dry_run=True)

            self.assertTrue(result.dry_run)
            self.assertFalse((dest / "examlex").exists())

    def test_copies_skill_to_temp_destination(self):
        with temp_dir() as temp:
            dest = Path(temp) / "skills"

            result = install_claude.install_skill(SOURCE, dest)

            self.assertEqual(dest / "examlex", result.target)
            self.assertTrue((result.target / "SKILL.md").exists())
            self.assertTrue((result.target / "references" / "workflow.md").exists())

    def test_installs_all_default_skills_from_skills_root(self):
        with temp_dir() as temp:
            dest = Path(temp) / "skills"

            results = install_claude.install_skills(PROJECT_ROOT / "skills", dest, dry_run=True)

            installed_names = {result.target.name for result in results}
            self.assertIn("examlex", installed_names)
            self.assertIn("grammar-corrector", installed_names)
            self.assertIn("learning-planner", installed_names)

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

    def test_force_refuses_destination_that_aliases_source_parent(self):
        with temp_dir() as temp:
            source = Path(temp) / "skills" / "examlex"
            source.mkdir(parents=True)
            marker = source / "SKILL.md"
            marker.write_text("---\nname: x\ndescription: Use when x.\n---\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Unsafe install target"):
                install_claude.install_skill(source, source.parent, force=True)

            self.assertTrue(marker.exists())

    def test_copy_excludes_pycache_and_pyc_files(self):
        with temp_dir() as temp:
            source = Path(temp) / "source" / "examlex"
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

    def test_codex_installer_runs_as_standalone_cli_dry_run_json(self):
        dest = PROJECT_ROOT / "test-artifacts" / "task8-cli-codex"

        result = subprocess.run(
            [
                sys.executable,
                "scripts/install_codex.py",
                "--source",
                "skills/examlex",
                "--dest",
                str(dest),
                "--dry-run",
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)

        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["copied"])
        self.assertFalse((dest / "examlex").exists())

    def test_cursor_installer_runs_as_standalone_cli_dry_run_json(self):
        dest = PROJECT_ROOT / "test-artifacts" / "task8-cli-cursor"

        result = subprocess.run(
            [
                sys.executable,
                "scripts/install_cursor.py",
                "--source",
                "skills/examlex",
                "--dest",
                str(dest),
                "--dry-run",
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)

        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["copied"])
        self.assertFalse((dest / "examlex").exists())


if __name__ == "__main__":
    unittest.main()
