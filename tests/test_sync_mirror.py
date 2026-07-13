from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from examlex.scripts import sync_mirror


class SyncMirrorTests(unittest.TestCase):
    def test_check_reports_and_sync_removes_extra_generated_script(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills" / "examlex"
            package = root / "examlex"
            source_script = skill / "scripts" / "kept.py"
            generated_script = package / "scripts" / "kept.py"
            extra_script = package / "scripts" / "manual-only.py"
            source_script.parent.mkdir(parents=True)
            generated_script.parent.mkdir(parents=True)
            source_script.write_text("VALUE = 1\n", encoding="utf-8")
            generated_script.write_text("VALUE = 1\n", encoding="utf-8")
            extra_script.write_text("VALUE = 2\n", encoding="utf-8")

            with mock.patch.object(sync_mirror, "SKILL_ROOT", skill), mock.patch.object(
                sync_mirror,
                "PACKAGE_ROOT",
                package,
            ):
                mismatches = sync_mirror.sync_scripts(check_only=True)
                self.assertIn("extra script: manual-only.py", mismatches)
                self.assertTrue(extra_script.exists())

                sync_mirror.sync_scripts(check_only=False)

            self.assertFalse(extra_script.exists())
            self.assertEqual("VALUE = 1\n", generated_script.read_text(encoding="utf-8"))

    def test_sync_copies_missing_generated_script(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills" / "examlex"
            package = root / "examlex"
            source_script = skill / "scripts" / "new.py"
            source_script.parent.mkdir(parents=True)
            source_script.write_text("VALUE = 3\n", encoding="utf-8")

            with mock.patch.object(sync_mirror, "SKILL_ROOT", skill), mock.patch.object(
                sync_mirror,
                "PACKAGE_ROOT",
                package,
            ):
                sync_mirror.sync_scripts(check_only=False)

            self.assertEqual(
                "VALUE = 3\n",
                (package / "scripts" / "new.py").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
