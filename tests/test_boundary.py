"""Boundary and edge-case tests."""

import json
import tempfile
import unittest
from pathlib import Path

from skills.english_exam_ai_tutor.scripts.validators.format_checker import FormatChecker
from skills.english_exam_ai_tutor.scripts.validators.darwin_structure import DarwinStructureScorer
from skills.english_exam_ai_tutor.scripts.optimizers.ratchet import StrategyRatchet
from skills.english_exam_ai_tutor.scripts.extractors.url_resolver import resolve_input, InputType


class EmptyInputTests(unittest.TestCase):
    def setUp(self):
        self.checker = FormatChecker()

    def test_empty_strategy_dict(self):
        report = self.checker.validate({})
        self.assertFalse(report.passed)

    def test_strategy_with_only_id(self):
        report = self.checker.validate({"strategy_id": "cet4-reading-test-001"})
        self.assertFalse(report.passed)

    def test_empty_content_short(self):
        report = self.checker.validate({
            "strategy_id": "cet4-reading-test-001", "title": "T",
            "content": "ab", "steps": [], "source_file": "x.txt",
            "exam_types": ["CET4"], "modules": ["reading"],
        })
        self.assertFalse(report.passed)

    def test_none_input_resolver(self):
        self.assertEqual(resolve_input(""), InputType.UNKNOWN)

    def test_whitespace_only_resolver(self):
        self.assertEqual(resolve_input("   "), InputType.UNKNOWN)

    def test_numeric_only_resolver(self):
        self.assertEqual(resolve_input("12345"), InputType.PERSON_NAME)


class LargeInputTests(unittest.TestCase):
    def setUp(self):
        self.checker = FormatChecker()
        self.scorer = DarwinStructureScorer()

    def test_very_long_content(self):
        content = "This is a test content. " * 5000
        s = {
            "strategy_id": "cet4-reading-big-001", "title": "Big Strategy",
            "content": content, "steps": ["1. Step one", "2. Step two"],
            "source_file": "big.txt",
            "exam_types": ["CET4", "CET6"], "modules": ["reading"],
        }
        report = self.checker.validate(s)
        self.assertTrue(report.passed)
        score = self.scorer.score(s)
        self.assertIsNotNone(score.total)

    def test_many_steps(self):
        steps = [f"{i}. Step number {i} with details" for i in range(1, 51)]
        s = {
            "strategy_id": "cet4-reading-test-001", "title": "Many Steps",
            "content": "A strategy with many steps" * 5,
            "steps": steps, "source_file": "many.txt",
            "exam_types": ["CET4"], "modules": ["reading"],
        }
        report = self.checker.validate(s)
        self.assertTrue(report.passed)

    def test_very_long_title(self):
        s = {
            "strategy_id": "cet4-reading-test-001",
            "title": "A" * 500,
            "content": "test content with enough length to pass minimum requirements check",
            "steps": ["1. Step"], "source_file": "x.txt",
            "exam_types": ["CET4"], "modules": ["reading"],
        }
        report = self.checker.validate(s)
        self.assertTrue(report.passed)


class InvalidDataTests(unittest.TestCase):
    def setUp(self):
        self.checker = FormatChecker()

    def test_sql_injection_in_id_rejected(self):
        s = {
            "strategy_id": "cet4-reading-test-001'; DROP TABLE strategies;--",
            "title": "Test",
            "content": "test content with enough length to pass minimum check",
            "steps": ["1. Step"], "source_file": "x.txt",
            "exam_types": ["CET4"], "modules": ["reading"],
        }
        report = self.checker.validate(s)
        self.assertFalse(report.passed)

    def test_path_traversal_in_source_file_accepted_with_warning(self):
        s = {
            "strategy_id": "cet4-reading-traverse-001", "title": "Test",
            "content": "A" * 30, "steps": ["1. Step"],
            "source_file": "../../../etc/passwd",
            "exam_types": ["CET4"], "modules": ["reading"],
        }
        report = self.checker.validate(s)
        self.assertTrue(report.passed)

    def test_script_tag_in_title_accepted(self):
        s = {
            "strategy_id": "cet4-reading-test-001",
            "title": "<script>alert('xss')</script>",
            "content": "A" * 30, "steps": ["1. Step"],
            "source_file": "x.txt",
            "exam_types": ["CET4"], "modules": ["reading"],
        }
        report = self.checker.validate(s)
        self.assertTrue(report.passed)


class RatchetEdgeTests(unittest.TestCase):
    def setUp(self):
        self.ratchet = StrategyRatchet()

    def test_negative_old_score(self):
        old = {"strategy_id": "x", "darwin_score": -5.0}
        new = {"strategy_id": "x", "darwin_score": 70.0}
        result = self.ratchet.compare(old, new, 70.0)
        self.assertEqual(result.delta, 75.0)

    def test_zero_baseline(self):
        s = {"strategy_id": "x"}
        result = self.ratchet.baseline(s, 0.0)
        self.assertEqual(result["darwin_score"], 0.0)

    def test_score_above_100(self):
        s = {"strategy_id": "x"}
        result = self.ratchet.baseline(s, 150.0)
        self.assertEqual(result["darwin_score"], 150.0)

    def test_empty_history_no_stop(self):
        self.assertFalse(self.ratchet.should_stop([]))

    def test_single_entry_no_stop(self):
        h = [{"version": 1, "score": 70, "delta": 0, "status": "baseline"}]
        self.assertFalse(self.ratchet.should_stop(h))


class ResolverEdgeTests(unittest.TestCase):
    def test_file_protocol_url(self):
        # file:// URLs are not HTTP — treated as unknown
        result = resolve_input("file:///etc/passwd")
        self.assertIn(result, (InputType.URL_UNKNOWN, InputType.PERSON_NAME))

    def test_long_url(self):
        url = "https://www.bilibili.com/video/" + "A" * 1000
        self.assertEqual(resolve_input(url), InputType.URL_VIDEO)

    def test_url_with_unicode_params(self):
        self.assertEqual(
            resolve_input("https://www.bilibili.com/video/BV1xx?p=1&t=30"),
            InputType.URL_VIDEO,
        )

    def test_whitespace_around_url(self):
        self.assertEqual(
            resolve_input("  https://www.youtube.com/watch?v=abc  "),
            InputType.URL_VIDEO,
        )


if __name__ == "__main__":
    unittest.main()
