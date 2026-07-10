"""Simulated user onboarding — first-time experience from clone to first strategy."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from examlex.scripts.config import TutorConfig, DependencyReport
from examlex.scripts.session import SessionManager
from examlex.scripts.extractors.text import TextExtractor
from examlex.scripts.extractors.url_resolver import resolve_input, InputType
from examlex.scripts.validators.format_checker import FormatChecker
from examlex.scripts.validators.darwin_structure import DarwinStructureScorer
from examlex.scripts.optimizers.ratchet import StrategyRatchet
from examlex.scripts.common import load_data, save_data


class UserOnboardingTests(unittest.TestCase):
    """Simulate a new user's journey from scratch."""

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.project = Path(self.home) / "examlex"
        self.project.mkdir()
        self.library = self.project / "strategy-library.json"

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def test_step1_check_deps(self):
        """User runs check-deps to see what's available."""
        cfg = TutorConfig()
        report = cfg.check_all_dependencies()
        self.assertIsInstance(report, DependencyReport)
        # At minimum, should produce a report (some tools may be missing)
        self.assertIsInstance(report.all_available(), bool)

    def test_step2_create_first_strategy_text(self):
        """User writes a simple strategy and ingests it."""
        # Simulate user writing a strategy file
        strategy_file = self.project / "my-strategy.md"
        strategy_file.write_text("""# CET4 阅读快速定位法

## 核心方法
先看题干再读文章，利用关键词快速定位答案区间。

## 执行步骤
1. 扫描所有题干，圈出关键词
2. 按题号顺序到原文定位
3. 比对选项与原文，排除干扰项
4. 不确定的题先标记，后续回查

## 注意事项
如果遇到生词超过5个的段落，先跳过读下一段再回看。
对于主旨题，不要用定位法，要通读首尾段。
""", encoding="utf-8")

        # Extract
        extractor = TextExtractor()
        artifacts = self.project / "artifacts"
        result = extractor.extract(str(strategy_file), artifacts)
        self.assertIn("full_text", result.artifacts)
        self.assertTrue(result.artifacts["full_text"].exists())

        # Read and distill (simplified — real flow uses Agent)
        text = result.artifacts["full_text"].read_text(encoding="utf-8")
        self.assertIn("关键词", text)

    def test_step3_validate_strategy(self):
        """User validates a strategy after distillation."""
        strategy = {
            "strategy_id": "cet4-reading-locate-001",
            "title": "CET4阅读快速定位法",
            "exam_types": ["CET4", "CET6"],
            "modules": ["reading"],
            "content": "先看题干再读文章。如果遇到生词超过5个的段落则先跳过。对于主旨题则改用通读首尾段法。",
            "steps": [
                "1. 扫描所有题干，圈出关键词（限时30秒）",
                "2. 按题号顺序到原文定位关键句",
                "3. 比对选项与原文，排除明显错误选项",
                "4. 不确定的题先标记，全部做完后回查",
            ],
            "source_file": "my-strategy.md",
            "distillation_method": "direct",
            "added_at": "2026-07-06",
        }
        checker = FormatChecker()
        report = checker.validate(strategy)
        self.assertTrue(report.passed, f"Errors: {report.errors}")

    def test_step4_darwin_score(self):
        """User checks the quality score of their strategy."""
        strategy = {
            "strategy_id": "cet4-reading-locate-001",
            "title": "CET4阅读快速定位法",
            "exam_types": ["CET4", "CET6"],
            "modules": ["reading"],
            "content": "先看题干再读文章。如果遇到生词超过5个的段落则先跳过。对于主旨题则改用通读首尾段法。例如某考生用此法将阅读时间从25分钟缩至18分钟。",
            "steps": [
                "1. 扫描所有题干圈出关键词（限时30秒）",
                "2. 按题号顺序到原文定位",
                "3. 比对选项排除干扰项",
                "4. 先标记不确定的题后续回查——CHECKPOINT:确认前3题定位正确",
            ],
            "source_file": "my-strategy.md",
            "source_url": "https://example.com/strategy",
            "distillation_method": "direct",
            "added_at": "2026-07-06",
            "tags": ["reading", "speed"],
        }
        scorer = DarwinStructureScorer()
        score = scorer.score(strategy)
        self.assertGreater(score.total, 30)  # should score decently
        self.assertTrue(score.passed)

    def test_step5_commit_to_library(self):
        """User commits the strategy to the library."""
        # Create library
        library = {"strategies": []}
        save_data(self.library, library)

        strategy = {
            "strategy_id": "cet4-reading-locate-001",
            "title": "CET4阅读快速定位法",
            "exam_types": ["CET4", "CET6"],
            "modules": ["reading"],
            "content": "先看题干再读文章" * 5,
            "steps": ["1. 扫描题干", "2. 定位原文", "3. 比对选项"],
            "source_file": "my-strategy.md",
            "source_type": "text",
            "distillation_method": "direct",
            "added_at": "2026-07-06",
        }

        ratchet = StrategyRatchet()
        # Baseline the strategy
        scored = ratchet.baseline(strategy, 52.0)
        ratchet.apply(scored, library, None, 52.0)

        # Save
        StrategyRatchet.atomic_save(library, self.library)

        # Verify
        loaded = load_data(self.library)
        self.assertEqual(len(loaded["strategies"]), 1)
        self.assertEqual(loaded["strategies"][0]["darwin_score"], 52.0)
        self.assertEqual(len(loaded["strategies"][0]["score_history"]), 1)

    def test_step6_update_existing_strategy(self):
        """User improves a strategy and the ratchet keeps the better version."""
        # Setup: create library with initial strategy
        old = {
            "strategy_id": "test-001", "title": "Old",
            "darwin_score": 50.0,
            "score_history": [{"version": 1, "score": 50.0, "status": "baseline", "delta": 0}],
        }
        library = {"strategies": [old]}
        save_data(self.library, library)

        # User submits improved version
        improved = {
            "strategy_id": "test-001", "title": "Improved",
            "content": "Better content with more details and examples" * 3,
            "steps": ["1. Better step", "2. Another step"],
        }
        ratchet = StrategyRatchet()
        library_loaded = load_data(self.library)
        existing = library_loaded["strategies"][0]
        ratchet.apply(improved, library_loaded, existing, 65.0)

        # Verify improvement was kept
        self.assertEqual(library_loaded["strategies"][0]["darwin_score"], 65.0)
        self.assertEqual(library_loaded["strategies"][0]["score_history"][-1]["status"], "keep")

    def test_step7_resolver_understands_common_inputs(self):
        """User provides various types of inputs and the resolver handles them."""
        self.assertEqual(resolve_input("https://www.bilibili.com/video/BV1xx"), InputType.URL_VIDEO)
        self.assertEqual(resolve_input("https://www.youtube.com/watch?v=abc"), InputType.URL_VIDEO)
        self.assertEqual(resolve_input("./book.pdf"), InputType.LOCAL_BOOK)
        self.assertEqual(resolve_input("notes.md"), InputType.LOCAL_TEXT)
        self.assertEqual(resolve_input("赖世雄"), InputType.PERSON_NAME)
        self.assertEqual(resolve_input("--help"), InputType.UNKNOWN)

    def test_step8_session_lifecycle(self):
        """User runs a full session lifecycle."""
        sessions_root = Path(self.home) / "sessions"
        mgr = SessionManager(sessions_root)

        # Create
        session = mgr.create(source_type="text")
        sid = session.session_id
        self.assertTrue(session.artifacts_dir.exists())

        # Progress through stages
        session.checkpoint("extract")
        session.checkpoint("distill")
        session.checkpoint("validate")
        session.checkpoint("commit")

        # Resume
        resumed = mgr.resume(sid)
        self.assertEqual(resumed.current_stage, "commit")

        # Get resume guidance
        info = resumed.resume_info()
        self.assertIn("next_action", info)


class CLIOnboardingTests(unittest.TestCase):
    """Test CLI commands from a new user's perspective."""

    def test_check_deps_cli(self):
        """examlex check-deps should run without crashing."""
        from examlex.cli import _check_deps_main
        import io, sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            ret = _check_deps_main([])
            self.assertIn(ret, (0, 1))
        finally:
            sys.stdout = old_stdout

    def test_help_shows_new_commands(self):
        """examlex --help should list extract/validate/commit/check-deps."""
        from examlex.cli import ALL_COMMANDS
        new_cmds = ["extract", "validate-strategies", "commit-strategies", "check-deps"]
        for cmd in new_cmds:
            self.assertIn(cmd, ALL_COMMANDS, f"Missing command: {cmd}")


if __name__ == "__main__":
    unittest.main()
