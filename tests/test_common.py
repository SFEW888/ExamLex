from __future__ import annotations

import json
import os
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from examlex.scripts import common
from examlex.scripts.file_lock import exclusive_file_lock


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CommonPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.root = PROJECT_ROOT / "test-artifacts" / f"common-{uuid.uuid4().hex}"
        self.root.mkdir(parents=True)

    def tearDown(self):
        for path in sorted(self.root.glob("*"), reverse=True):
            path.unlink(missing_ok=True)
        self.root.rmdir()

    def test_atomic_save_preserves_original_when_replace_fails(self):
        target = self.root / "records.json"
        target.write_text('[{"id":"original"}]\n', encoding="utf-8")

        with patch("pathlib.Path.replace", side_effect=OSError("simulated failure")):
            with self.assertRaisesRegex(OSError, "simulated failure"):
                common.atomic_save_data(target, [{"id": "replacement"}])

        self.assertEqual([{"id": "original"}], json.loads(target.read_text("utf-8")))
        self.assertEqual([], list(self.root.glob("*.tmp")))

    def test_lock_times_out_when_live_lock_is_held(self):
        target = self.root / "records.json"
        with exclusive_file_lock(target):
            with self.assertRaisesRegex(TimeoutError, "Timed out waiting for file lock"):
                with exclusive_file_lock(target, timeout_seconds=0.02):
                    self.fail("nested lock unexpectedly acquired")

    def test_stale_lock_is_recovered(self):
        target = self.root / "records.json"
        lock_path = target.with_name(target.name + ".lock")
        lock_path.write_text("stale", encoding="utf-8")
        old = time.time() - 120
        os.utime(lock_path, (old, old))

        with exclusive_file_lock(target, stale_after_seconds=60):
            self.assertTrue(lock_path.exists())

        self.assertFalse(lock_path.exists())

    def test_old_lock_owned_by_live_process_is_not_reclaimed(self):
        target = self.root / "records.json"
        lock_path = target.with_name(target.name + ".lock")
        token = f"{os.getpid()}:still-live"
        lock_path.write_text(token, encoding="utf-8")
        old = time.time() - 120
        os.utime(lock_path, (old, old))

        with self.assertRaisesRegex(TimeoutError, "Timed out waiting for file lock"):
            with exclusive_file_lock(
                target,
                timeout_seconds=0.02,
                stale_after_seconds=0.001,
            ):
                self.fail("live process lock was reclaimed")

        self.assertEqual(token, lock_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
