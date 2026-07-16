from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from examlex.scripts import monitor_capacity, strategy_store


class CapacityMonitorTests(unittest.TestCase):
    def test_monitor_prunes_regenerable_artifacts_but_preserves_strategy_data(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            sessions = root / "sessions"
            session = sessions / "2026-01-01" / "old-session"
            session.mkdir(parents=True)
            (session / "pipeline_state.json").write_text(
                json.dumps(
                    {
                        "session_id": "old-session",
                        "stage": "committed",
                        "updated_at": "2026-01-01T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            transcript = session / "transcript.txt"
            transcript.write_bytes(b"regenerable transcript")
            immutable = session / "artifact.txt"
            immutable.write_text("keep", encoding="utf-8")

            library_path = root / "strategy-library.json"
            library = self._duplicate_library()
            strategy_store.atomic_save_strategy_library(library, library_path)
            original_strategy_bytes = library_path.read_bytes()
            status_file = root / "monitor.json"

            result = monitor_capacity.run_capacity_monitor(
                sessions_root=sessions,
                strategy_library_path=library_path,
                retention_hours=1,
                max_reproducible_artifact_bytes=1,
                strategy_library_warning_bytes=1,
                status_file=status_file,
            )

            self.assertFalse(transcript.exists())
            self.assertTrue(immutable.exists())
            self.assertEqual(original_strategy_bytes, library_path.read_bytes())
            self.assertTrue(result["strategy_library"]["threshold_reached"])
            self.assertFalse(result["automatic_strategy_deletion"])
            warning_file = Path(result["warning_file"])
            warning = json.loads(warning_file.read_text(encoding="utf-8"))
            self.assertGreater(len(warning["strategy_library"]["duplicate_candidates"]), 0)
            self.assertTrue(status_file.exists())

    def test_windows_notification_is_attempted_only_after_threshold(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            library_path = root / "strategies.json"
            strategy_store.atomic_save_strategy_library(
                self._duplicate_library(), library_path
            )
            with mock.patch.object(
                monitor_capacity, "_windows_toast", return_value=True
            ) as toast:
                result = monitor_capacity.run_capacity_monitor(
                    sessions_root=root / "sessions",
                    strategy_library_path=library_path,
                    retention_hours=168,
                    max_reproducible_artifact_bytes=1024,
                    strategy_library_warning_bytes=1,
                    status_file=root / "status.json",
                    notify_windows=True,
                )
            toast.assert_called_once()
            self.assertTrue(result["notification"]["sent"])

    @staticmethod
    def _duplicate_library() -> dict:
        return {
            "strategies": [
                {
                    "strategy_id": "one",
                    "title": "Locate evidence",
                    "content": "Read the stem and locate the evidence.",
                    "exam_types": ["CET4"],
                    "modules": ["reading"],
                },
                {
                    "strategy_id": "two",
                    "title": "Locate evidence again",
                    "content": " read the stem AND locate the evidence. ",
                    "exam_types": ["CET4"],
                    "modules": ["reading"],
                },
            ]
        }

    @staticmethod
    def _temporary_dir():
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()
