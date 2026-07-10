"""Tests for Darwin structure scoring."""
import unittest

from examlex.scripts.validators.darwin_structure import (
    DarwinStructureScorer,
    StructureScore,
)

_VALID_STRATEGY = {
    "strategy_id": "cet4-reading-speed-001",
    "title": "四级阅读快速定位法",
    "exam_types": ["CET4"],
    "modules": ["reading"],
    "content": "在阅读文章时，先用30秒扫描题干关键词。如果遇到生词则跳过继续往下读。例如遇到'ubiquitous'可以先跳过。",
    "steps": ["1. 扫描题干圈出关键词", "2. 按题号顺序定位原文", "3. 比对选项排除干扰"],
    "source_file": "bilibili-cet4-reading.txt",
    "source_url": "https://bilibili.com/video/BV1xx",
    "added_at": "2026-07-06",
    "tags": ["reading", "speed"],
    "ria_structure": {
        "r_reading": "先看题干再读文章",
        "i_interpretation": "预读建立搜索目标",
        "a1_past": "考生用此法缩短时间",
        "a2_trigger": "阅读慢时触发",
        "e_execution": ["1. 扫描题干30秒", "2. 圈关键词", "3. 定位原文"],
        "b_boundary": "不适用于文学类文章和深度推理题",
    },
}


class DarwinStructureTests(unittest.TestCase):
    def setUp(self):
        self.scorer = DarwinStructureScorer()

    def test_valid_strategy_scores_above_threshold(self):
        score = self.scorer.score(_VALID_STRATEGY)
        self.assertIsInstance(score, StructureScore)
        self.assertEqual(len(score.dimensions), 6)
        self.assertTrue(score.total > 0)
        # A well-formed strategy should pass
        self.assertTrue(score.passed)

    def test_minimal_strategy_scores_low(self):
        minimal = {
            "strategy_id": "x",
            "title": "",
            "content": "x" * 25,
        }
        score = self.scorer.score(minimal)
        self.assertLess(score.total, 30)

    def test_missing_boundary_penalizes(self):
        s = {**_VALID_STRATEGY,
             "ria_structure": {**_VALID_STRATEGY["ria_structure"], "b_boundary": ""}}
        score = self.scorer.score(s)
        dim3 = [d for d in score.dimensions if d.name == "dim3_failure_encoding"][0]
        self.assertGreater(len(dim3.issues), 0)

    def test_no_steps_penalizes_workflow(self):
        s = {**_VALID_STRATEGY, "steps": []}
        score = self.scorer.score(s)
        dim2 = [d for d in score.dimensions if d.name == "dim2_workflow_clarity"][0]
        self.assertGreater(len(dim2.issues), 0)

    def test_all_dimensions_have_valid_raw_range(self):
        score = self.scorer.score(_VALID_STRATEGY)
        for d in score.dimensions:
            self.assertGreaterEqual(d.raw, 1)
            self.assertLessEqual(d.raw, 10)

    def test_total_is_weighted_sum(self):
        score = self.scorer.score(_VALID_STRATEGY)
        expected = sum(d.weighted for d in score.dimensions)
        self.assertAlmostEqual(score.total, expected, places=1)


if __name__ == "__main__":
    unittest.main()
