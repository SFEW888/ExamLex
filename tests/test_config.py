"""Tests for unified configuration management."""
import os
import unittest
from pathlib import Path
from unittest import mock

from skills.english_exam_ai_tutor.scripts.config import TutorConfig, DependencyReport


class TutorConfigTests(unittest.TestCase):
    def setUp(self):
        # Preserve HOME / USERPROFILE for Path.home() to work
        self.clean_env = {
            k: v for k, v in os.environ.items()
            if k not in ("SILICONFLOW_API_KEY",)
        }
        # Ensure HOME is always present for Path.home()
        if "HOME" not in self.clean_env and "USERPROFILE" in self.clean_env:
            self.clean_env["HOME"] = self.clean_env["USERPROFILE"]

    def test_defaults_produce_sensible_values(self):
        with mock.patch.dict(os.environ, self.clean_env, clear=True):
            cfg = TutorConfig()
            self.assertEqual(cfg.asr_backend, "auto")
            self.assertEqual(cfg.darwin_pass_score, 70.0)
            self.assertEqual(cfg.darwin_max_rounds, 3)
            self.assertEqual(cfg.darwin_touch_top_delta, 2.0)
            self.assertTrue(cfg.auto_cleanup)
            self.assertIsInstance(cfg.sessions_root, Path)

    def test_env_var_siliconflow_api_key_is_read(self):
        env = {**self.clean_env, "SILICONFLOW_API_KEY": "sk-test-123"}
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = TutorConfig()
            self.assertEqual(cfg.siliconflow_api_key, "sk-test-123")

    def test_cli_overrides_have_highest_priority(self):
        env = {**self.clean_env, "SILICONFLOW_API_KEY": "sk-env"}
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = TutorConfig(siliconflow_api_key="sk-cli")
            self.assertEqual(cfg.siliconflow_api_key, "sk-cli")

    def test_env_overrides_default(self):
        with mock.patch.dict(os.environ, self.clean_env, clear=True):
            cfg = TutorConfig(darwin_pass_score=80.0)
            self.assertEqual(cfg.darwin_pass_score, 80.0)

    def test_dependency_path_defaults_to_none(self):
        cfg = TutorConfig()
        self.assertIsNone(cfg.yt_dlp_path)
        self.assertIsNone(cfg.ffmpeg_path)
        self.assertIsNone(cfg.whisper_path)

    def test_dependency_path_can_be_set(self):
        cfg = TutorConfig(yt_dlp_path="/usr/local/bin/yt-dlp")
        self.assertEqual(cfg.yt_dlp_path, "/usr/local/bin/yt-dlp")

    def test_to_dict_excludes_none_values(self):
        cfg = TutorConfig()
        d = cfg.to_dict()
        self.assertIn("asr_backend", d)
        self.assertIn("darwin_pass_score", d)
        self.assertNotIn("yt_dlp_path", d)  # None values excluded

    def test_from_dict_roundtrip(self):
        cfg = TutorConfig(darwin_pass_score=75.0)
        d = cfg.to_dict()
        cfg2 = TutorConfig.from_dict(d)
        self.assertEqual(cfg2.darwin_pass_score, 75.0)


class DependencyReportTests(unittest.TestCase):
    def test_empty_report(self):
        r = DependencyReport()
        self.assertEqual(len(r.available), 0)
        self.assertEqual(len(r.missing), 0)
        self.assertEqual(len(r.install_hints), 0)

    def test_add_available_tool(self):
        r = DependencyReport()
        r.add("yt-dlp", available=True, path="/usr/bin/yt-dlp", install_hint="pip install yt-dlp")
        self.assertIn("yt-dlp", r.available)
        self.assertNotIn("yt-dlp", r.missing)

    def test_add_missing_tool(self):
        r = DependencyReport()
        r.add("ffmpeg", available=False, install_hint="brew install ffmpeg")
        self.assertIn("ffmpeg", r.missing)
        self.assertNotIn("ffmpeg", r.available)

    def test_all_available_returns_true(self):
        r = DependencyReport()
        r.add("a", available=True)
        r.add("b", available=True)
        self.assertTrue(r.all_available())

    def test_any_missing_returns_false(self):
        r = DependencyReport()
        r.add("a", available=True)
        r.add("b", available=False)
        self.assertFalse(r.all_available())


if __name__ == "__main__":
    unittest.main()
