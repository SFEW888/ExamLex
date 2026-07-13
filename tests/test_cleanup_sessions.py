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

from examlex.scripts.session import Session


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

    def test_archive_revalidates_after_a_checkpoint_changes_candidate(self):
        module = self.require_module()
        source = self.write_session(
            "became-active", stage="extract", updated_at="2026-07-01T00:00:00+00:00"
        )
        candidates = module.find_stale_sessions(
            self.sessions_root, older_than_hours=24, now=self.now
        )
        session = Session("became-active", source, "video", current_stage="extract")
        session.checkpoint("distill")

        result = module.archive_stale_sessions(
            candidates, self.sessions_root, self.archive_root
        )

        self.assertTrue(source.exists())
        self.assertEqual([], result.archived)
        self.assertEqual(1, len(result.failures))
        self.assertIn("changed", result.failures[0])

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

    def test_prune_terminal_artifacts_removes_only_reproducible_files(self):
        module = self.require_module()
        source = self.write_session(
            "committed", stage="committed", updated_at="2026-07-01T00:00:00+00:00"
        )
        removable = {
            "full_text.txt": b"full source text",
            "audio.mp3": b"audio bytes",
            "transcript.txt": b"transcript",
            "transcript.whisper.json": b"{}",
        }
        for name, payload in removable.items():
            (source / name).write_bytes(payload)
        chapters = source / "chapters"
        chapters.mkdir()
        (chapters / "chapter-1.txt").write_bytes(b"chapter")
        (source / "distilled.json").write_text('{"strategies": []}', encoding="utf-8")

        candidates = module.find_stale_sessions(
            self.sessions_root,
            older_than_hours=24,
            now=self.now,
            stages=module.PRUNABLE_STAGES,
        )
        result = module.prune_terminal_artifacts(candidates, self.sessions_root)

        self.assertEqual([], result.failures)
        self.assertGreaterEqual(result.bytes_reclaimed, sum(map(len, removable.values())))
        for name in removable:
            self.assertFalse((source / name).exists())
        self.assertFalse(chapters.exists())
        self.assertTrue((source / "pipeline_state.json").exists())
        self.assertTrue((source / "distilled.json").exists())
        self.assertTrue((source / "artifact.txt").exists())

    def test_prune_terminal_artifacts_cli_is_dry_run_by_default(self):
        module = self.require_module()
        source = self.write_session(
            "committed-dry-run",
            stage="committed",
            updated_at="2020-01-01T00:00:00+00:00",
        )
        full_text = source / "full_text.txt"
        full_text.write_text("large extracted text", encoding="utf-8")
        output = StringIO()

        with redirect_stdout(output):
            exit_code = module.main(
                [
                    "--sessions-root",
                    str(self.sessions_root),
                    "--older-than-hours",
                    "24",
                    "--prune-terminal-artifacts",
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(0, exit_code)
        self.assertFalse(payload["applied"])
        self.assertEqual("prune-terminal-artifacts", payload["operation"])
        self.assertEqual(1, payload["candidate_count"])
        self.assertTrue(full_text.exists())

    def test_retention_policy_prunes_expired_then_oldest_until_under_limit(self):
        module = self.require_module()
        expired = self.write_session(
            "expired",
            stage="committed",
            updated_at="2026-07-01T00:00:00+00:00",
        )
        oldest = self.write_session(
            "oldest",
            stage="committed",
            updated_at="2026-07-09T00:00:00+00:00",
            date="2026-07-09",
        )
        newest = self.write_session(
            "newest",
            stage="committed",
            updated_at="2026-07-09T12:00:00+00:00",
            date="2026-07-09",
        )
        (expired / "full_text.txt").write_bytes(b"old!")
        (oldest / "audio.mp3").write_bytes(b"1234567")
        (newest / "transcript.txt").write_bytes(b"7654321")

        result = module.apply_retention_policy(
            self.sessions_root,
            retention_hours=168,
            max_reproducible_artifact_bytes=7,
            now=self.now,
        )

        self.assertEqual([], result.failures)
        self.assertEqual(18, result.bytes_before)
        self.assertEqual(7, result.bytes_after)
        self.assertEqual(["expired", "oldest"], result.selected_sessions)
        self.assertFalse((expired / "full_text.txt").exists())
        self.assertFalse((oldest / "audio.mp3").exists())
        self.assertTrue((newest / "transcript.txt").exists())
        for session in (expired, oldest, newest):
            self.assertTrue((session / "pipeline_state.json").exists())
            self.assertTrue((session / "artifact.txt").exists())

    def test_retention_policy_keeps_recent_artifacts_below_limit(self):
        module = self.require_module()
        session = self.write_session(
            "recent",
            stage="committed",
            updated_at="2026-07-09T12:00:00+00:00",
            date="2026-07-09",
        )
        transcript = session / "transcript.txt"
        transcript.write_bytes(b"small")

        result = module.apply_retention_policy(
            self.sessions_root,
            retention_hours=168,
            max_reproducible_artifact_bytes=10,
            now=self.now,
        )

        self.assertEqual([], result.selected_sessions)
        self.assertEqual(5, result.bytes_before)
        self.assertEqual(5, result.bytes_after)
        self.assertTrue(transcript.exists())
