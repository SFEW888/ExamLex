"""Tests for session and artifact management."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from examlex.scripts.session import SessionManager, Session


class SessionManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.sessions_root = Path(self.tmp) / "sessions"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_returns_session_with_id_and_dirs(self):
        mgr = SessionManager(self.sessions_root)
        session = mgr.create(source_type="video")
        self.assertIsNotNone(session.session_id)
        self.assertTrue(session.artifacts_dir.exists())
        self.assertEqual(session.source_type, "video")
        self.assertEqual(session.current_stage, "init")

    def test_create_writes_pipeline_state(self):
        mgr = SessionManager(self.sessions_root)
        session = mgr.create(source_type="book")
        state_path = session.artifacts_dir / "pipeline_state.json"
        self.assertTrue(state_path.exists())
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["stage"], "init")
        self.assertEqual(state["source_type"], "book")

    def test_checkpoint_updates_stage_and_writes(self):
        mgr = SessionManager(self.sessions_root)
        session = mgr.create(source_type="video")
        session.checkpoint("extract", sub_stage="downloading")
        state_path = session.artifacts_dir / "pipeline_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["stage"], "extract")
        self.assertEqual(state["sub_stage"], "downloading")

    def test_resume_returns_existing_session(self):
        mgr = SessionManager(self.sessions_root)
        created = mgr.create(source_type="book")
        created.checkpoint("extract")
        session_id = created.session_id

        resumed = mgr.resume(session_id)
        self.assertEqual(resumed.session_id, session_id)
        self.assertEqual(resumed.current_stage, "extract")

    def test_resume_nonexistent_raises(self):
        mgr = SessionManager(self.sessions_root)
        with self.assertRaises(FileNotFoundError):
            mgr.resume("nonexistent-id")

    def test_resume_info_returns_structured_guide(self):
        mgr = SessionManager(self.sessions_root)
        session = mgr.create(source_type="video")
        session.checkpoint("extract", sub_stage="asr_failed")

        info = session.resume_info()
        self.assertEqual(info["session_id"], session.session_id)
        self.assertEqual(info["current_stage"], "extract")
        self.assertEqual(info["sub_stage"], "asr_failed")
        self.assertIn("next_action", info)

    def test_full_path_idempotent_checkpoint(self):
        mgr = SessionManager(self.sessions_root)
        session = mgr.create(source_type="text")
        # check pointing same stage twice should not fail
        session.checkpoint("distill")
        session.checkpoint("distill")
        self.assertEqual(session.current_stage, "distill")


if __name__ == "__main__":
    unittest.main()
