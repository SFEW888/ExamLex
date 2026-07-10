"""Tests for format checker."""
import unittest

from examlex.scripts.validators.format_checker import FormatChecker


_VALID_STRATEGY = {
    "strategy_id": "cet4-reading-speed-001",
    "title": "四级阅读快速定位法",
    "exam_types": ["CET4"],
    "modules": ["reading"],
    "content": "在阅读文章时，先用30秒扫描题干关键词，然后按顺序定位原文对应段落。每道题控制在2分钟内完成。" * 3,
    "steps": ["1. 扫描题干，圈出关键词", "2. 按题号顺序定位原文段落", "3. 比对选项与原文，排除干扰项"],
    "source_file": "bilibili-cet4-reading.txt",
    "added_at": "2026-07-06",
    "distillation_method": "video",
    "ria_structure": {
        "r_reading": "先看题干再读文章，节省时间且提高正确率",
        "i_interpretation": "预读题干建立搜索目标，避免盲目通读",
        "a1_past": "某考生用此法将阅读从18分钟/篇缩短到12分钟",
        "a2_trigger": "阅读速度慢、反复回读、定位不准时触发",
        "e_execution": ["1. 扫描所有题干30秒", "2. 圈出每题关键词", "3. 逐题定位原文"],
        "b_boundary": "不适用于需要深度理解的文学类文章和推理题",
    },
}


class FormatCheckerTests(unittest.TestCase):
    def setUp(self):
        self.checker = FormatChecker()

    def test_valid_strategy_passes(self):
        report = self.checker.validate(_VALID_STRATEGY)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.errors), 0)

    def test_missing_strategy_id_fails(self):
        s = {**_VALID_STRATEGY, "strategy_id": ""}
        report = self.checker.validate(s)
        self.assertFalse(report.passed)

    def test_invalid_strategy_id_format(self):
        s = {**_VALID_STRATEGY, "strategy_id": "bad-format"}
        report = self.checker.validate(s)
        self.assertFalse(report.passed)

    def test_missing_title(self):
        s = {**_VALID_STRATEGY, "title": ""}
        report = self.checker.validate(s)
        self.assertFalse(report.passed)

    def test_content_too_short(self):
        s = {**_VALID_STRATEGY, "content": "short"}
        report = self.checker.validate(s)
        self.assertFalse(report.passed)

    def test_steps_without_numbering_warns(self):
        s = {**_VALID_STRATEGY, "steps": ["do something", "then something else"]}
        report = self.checker.validate(s)
        self.assertTrue(report.passed)  # steps not required to pass
        self.assertTrue(any("numbering" in w.message.lower() for w in report.warnings))

    def test_missing_exam_types(self):
        s = {**_VALID_STRATEGY, "exam_types": []}
        report = self.checker.validate(s)
        self.assertFalse(report.passed)

    def test_missing_modules(self):
        s = {**_VALID_STRATEGY, "modules": []}
        report = self.checker.validate(s)
        self.assertFalse(report.passed)

    def test_missing_ria_segments(self):
        s = {**_VALID_STRATEGY, "ria_structure": {"r_reading": "x"}}
        report = self.checker.validate(s)
        self.assertFalse(report.passed)

    def test_vague_phrasing_warns(self):
        s = {**_VALID_STRATEGY,
             "content": "建议可以考虑根据情况灵活把握，建议使用此法，可以考虑尝试"}
        report = self.checker.validate(s)
        self.assertTrue(any("vague" in w.message.lower() for w in report.warnings))


if __name__ == "__main__":
    unittest.main()
