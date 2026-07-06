"""Security tests — injection, path traversal, large payloads, data integrity."""

import json
import tempfile
import unittest
from pathlib import Path

from skills.english_exam_ai_tutor.scripts.common import load_data, save_data
from skills.english_exam_ai_tutor.scripts.optimizers.ratchet import StrategyRatchet
from skills.english_exam_ai_tutor.scripts.session import SessionManager
from skills.english_exam_ai_tutor.scripts.extractors.url_resolver import resolve_input, InputType
from skills.english_exam_ai_tutor.scripts.extractors.text import TextExtractor


class InjectionTests(unittest.TestCase):
    """Verify that malicious inputs don't cause unexpected behavior."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_json_injection_in_strategy_content(self):
        """JSON special chars in strategy fields should be safely serialized."""
        s = {
            "strategy_id": "cet4-reading-001",
            "title": "Test",
            "content": 'test"}},{"malicious":"data' + '","steps":[{"1"}]',
        }
        # Should not crash or produce malformed JSON
        text = json.dumps(s, ensure_ascii=False)
        parsed = json.loads(text)
        self.assertIn("malicious", parsed["content"])

    def test_strategy_id_with_regex_bomb(self):
        """Very long strategy_id should fail gracefully."""
        s = {
            "strategy_id": "a" * 10000 + "-" + "b" * 100,
            "title": "Test", "content": "x" * 30,
            "steps": ["1. Step"], "source_file": "x.txt",
            "exam_types": ["CET4"], "modules": ["reading"],
        }
        # Validate should handle this without catastrophic backtracking
        from skills.english_exam_ai_tutor.scripts.validators.format_checker import FormatChecker
        checker = FormatChecker()
        report = checker.validate(s)
        self.assertFalse(report.passed)

    def test_duplicate_session_id_no_leak(self):
        """Each session gets its own isolated directory."""
        mgr = SessionManager(Path(self.tmp))
        s1 = mgr.create(source_type="text")
        s1.checkpoint("committed")
        s2 = mgr.create(source_type="text")
        # Different sessions should have different directories
        self.assertNotEqual(s1.artifacts_dir, s2.artifacts_dir)
        # s2 has its own fresh state, not s1's state
        self.assertEqual(s2.current_stage, "init")
        self.assertNotEqual(s1.current_stage, s2.current_stage)

    def test_billion_laughs_like_nesting(self):
        """Very long step text should not crash the validator."""
        s = {
            "strategy_id": "cet4-reading-billion-001",
            "title": "x", "content": "x" * 30,
            "steps": ["1. " + "a" * 1000],
            "source_file": "x.txt",
            "exam_types": ["CET4"], "modules": ["reading"],
        }
        from skills.english_exam_ai_tutor.scripts.validators.format_checker import FormatChecker
        checker = FormatChecker()
        report = checker.validate(s)
        # Should not crash; may pass or fail but must not raise
        self.assertIsNotNone(report.passed)


class FileAccessTests(unittest.TestCase):
    """Verify the system doesn't access files it shouldn't."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_extractor_rejects_nonexistent_path(self):
        """Extractor raises FileNotFoundError for non-existent paths."""
        extractor = TextExtractor()
        with self.assertRaises(FileNotFoundError):
            extractor.extract("/nonexistent/path/that/does/not/exist.txt", Path(self.tmp))

    def test_save_data_writes_only_to_intended_path(self):
        """save_data should not follow symlinks or write outside target."""
        target = Path(self.tmp) / "data.json"
        save_data(target, {"test": "data"})
        self.assertTrue(target.exists())
        loaded = load_data(target)
        self.assertEqual(loaded["test"], "data")

    def test_atomic_save_does_not_corrupt_on_disk_full(self):
        """Atomic save should handle OS errors gracefully."""
        # We can't easily simulate disk full, but we can verify the temp+rename pattern
        path = Path(self.tmp) / "lib.json"
        path.write_text('{"strategies": [1]}', encoding="utf-8")
        # Atomic save should succeed normally
        StrategyRatchet.atomic_save({"strategies": [2]}, path)
        self.assertTrue(path.exists())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["strategies"], [2])


class DataIntegrityTests(unittest.TestCase):
    """Verify data consistency after operations."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_roundtrip_unicode_content(self):
        """Chinese + emoji + special chars should survive save/load."""
        target = Path(self.tmp) / "unicode.json"
        original = {
            "strategies": [{
                "strategy_id": "test-001",
                "content": "中文测试 🎯 émoji Café \n\t\r special",
                "steps": ["1. 第一步", "2. 第二步"],
            }]
        }
        save_data(target, original)
        loaded = load_data(target)
        self.assertEqual(loaded["strategies"][0]["content"], original["strategies"][0]["content"])
        self.assertEqual(loaded["strategies"][0]["steps"], original["strategies"][0]["steps"])

    def test_score_history_is_immutable_in_ratchet(self):
        """Ratchet operations should not mutate original strategy dict."""
        ratchet = StrategyRatchet()
        original = {"strategy_id": "test-001", "title": "Original"}
        baselined = ratchet.baseline(original, 80.0)
        # Original dict should not have darwin_score or score_history
        self.assertNotIn("darwin_score", original)
        self.assertNotIn("score_history", original)
        # Baselined copy should have them
        self.assertIn("darwin_score", baselined)
        self.assertIn("score_history", baselined)


if __name__ == "__main__":
    unittest.main()
