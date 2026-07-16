from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from examlex.scripts import sync_mirror


class ThinPackageTests(unittest.TestCase):
    def test_check_reports_and_sync_removes_mirrored_scripts(self):
        with tempfile.TemporaryDirectory(dir=self._artifact_root()) as temp:
            root = Path(temp)
            skill = root / "skills" / "examlex"
            package = root / "examlex"
            (skill / "scripts").mkdir(parents=True)
            extra = package / "scripts" / "duplicated.py"
            extra.parent.mkdir(parents=True)
            extra.write_text("VALUE = 1\n", encoding="utf-8")

            with mock.patch.object(sync_mirror, "SKILL_ROOT", skill), mock.patch.object(
                sync_mirror, "PACKAGE_ROOT", package
            ):
                issues = sync_mirror.sync_scripts(check_only=True)
                self.assertTrue(any("extra mirrored script" in item for item in issues))
                sync_mirror.sync_scripts(check_only=False)

            self.assertFalse(extra.exists())
            bridge = package / "scripts" / "__init__.py"
            self.assertEqual(sync_mirror.SCRIPT_INIT, bridge.read_text(encoding="utf-8"))

    def test_sync_removes_resource_copies_and_repairs_wrappers(self):
        with tempfile.TemporaryDirectory(dir=self._artifact_root()) as temp:
            root = Path(temp)
            skill = root / "skills" / "examlex"
            package = root / "examlex"
            skill.mkdir(parents=True)
            duplicated = package / "assets" / "data.json"
            duplicated.parent.mkdir(parents=True)
            duplicated.write_text("{}", encoding="utf-8")

            with mock.patch.object(sync_mirror, "SKILL_ROOT", skill), mock.patch.object(
                sync_mirror, "PACKAGE_ROOT", package
            ):
                sync_mirror.sync_cli(check_only=False)
                sync_mirror.sync_resources(check_only=False)

            self.assertFalse((package / "assets").exists())
            self.assertEqual(
                sync_mirror.CLI_WRAPPER,
                (package / "cli.py").read_text(encoding="utf-8"),
            )

    @staticmethod
    def _artifact_root() -> Path:
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        return root


if __name__ == "__main__":
    unittest.main()
