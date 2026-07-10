from __future__ import annotations

import importlib
import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = PROJECT_ROOT / ".task8-test-tmp"

cleanup_sessions = (
    importlib.import_module("examlex.scripts.cleanup_sessions")
    if importlib.util.find_spec("examlex.scripts.cleanup_sessions")
    else None
)


class CleanupSessionsTests(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.sessions_root = self.base / "sessions"
        self.archive_root = self.base / "session-archive"
        self.now = datetime(2026, 7, 10, tzinfo=timezone.utc)

    def require_module(self):
        self.assertIsNotNone(cleanup_sessions, "cleanup_sessions module must exist")
        return cleanup_sessions

    def write_session(
        self,
        session_id: str,
        *,
        stage: str,
        updated_at: str,
        date: str = "2026-07-01",
    ) -> Path:
        session_dir = self.sessions_root / date / session_id
        session_dir.mkdir(parents=True)
        (session_dir / "artifact.txt").write_text("preserve me", encoding="utf-8")
        (session_dir / "pipeline_state.json").write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "stage": stage,
                    "updated_at": updated_at,
                }
            ),
            encoding="utf-8",
        )
        return session_dir

    def test_find_stale_sessions_excludes_terminal_and_invalid_states(self):
        module = self.require_module()
        self.write_session("stale-init", stage="init", updated_at="2026-07-01T00:00:00+00:00")
        self.write_session("stale-extract", stage="extract", updated_at="2026-07-02T00:00:00+00:00")
        self.write_session("committed", stage="committed", updated_at="2026-07-01T00:00:00+00:00")
        self.write_session("failed", stage="failed", updated_at="2026-07-01T00:00:00+00:00")
        self.write_session("invalid", stage="init", updated_at="not-a-time")

        candidates = module.find_stale_sessions(
            self.sessions_root, older_than_hours=24, now=self.now
        )

        self.assertEqual(["stale-extract", "stale-init"], sorted(c.session_id for c in candidates))

    def test_find_stale_sessions_ignores_state_outside_date_session_shape(self):
        module = self.require_module()
        self.sessions_root.mkdir(parents=True)
        (self.sessions_root / "pipeline_state.json").write_text(
            json.dumps(
                {
                    "session_id": "root-state",
                    "stage": "init",
                    "updated_at": "2020-01-01T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )

        candidates = module.find_stale_sessions(
            self.sessions_root, older_than_hours=24, now=self.now
        )

        self.assertEqual([], candidates)

    def test_archive_preserves_files_and_removes_empty_date_directory(self):
        module = self.require_module()
        source = self.write_session(
            "stale", stage="extract", updated_at="2026-07-01T00:00:00+00:00"
        )
        candidates = module.find_stale_sessions(
            self.sessions_root, older_than_hours=24, now=self.now
        )

        result = module.archive_stale_sessions(
            candidates, self.sessions_root, self.archive_root
        )

        target = self.archive_root / "2026-07-01" / "stale"
        self.assertFalse(source.exists())
        self.assertEqual("preserve me", (target / "artifact.txt").read_text(encoding="utf-8"))
        self.assertEqual([str(target)], result.archived)
        self.assertEqual([], result.failures)
        self.assertFalse((self.sessions_root / "2026-07-01").exists())

    def test_archive_refuses_to_overwrite_existing_target(self):
        module = self.require_module()
        source = self.write_session(
            "collision", stage="init", updated_at="2026-07-01T00:00:00+00:00"
        )
        target = self.archive_root / "2026-07-01" / "collision"
        target.mkdir(parents=True)
        candidates = module.find_stale_sessions(
            self.sessions_root, older_than_hours=24, now=self.now
        )

        result = module.archive_stale_sessions(
            candidates, self.sessions_root, self.archive_root
        )

        self.assertTrue(source.exists())
        self.assertEqual([], result.archived)
        self.assertEqual(1, len(result.failures))
        self.assertIn("already exists", result.failures[0])

    def test_cli_defaults_to_dry_run_for_explicit_root(self):
        module = self.require_module()
        source = self.write_session(
            "dry-run", stage="init", updated_at="2020-01-01T00:00:00+00:00"
        )
        output = StringIO()

        with redirect_stdout(output):
            exit_code = module.main(
                ["--sessions-root", str(self.sessions_root), "--older-than-hours", "24"]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(0, exit_code)
        self.assertTrue(source.exists())
        self.assertFalse(payload["applied"])
        self.assertEqual(1, payload["candidate_count"])
