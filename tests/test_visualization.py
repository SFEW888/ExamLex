from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO_ROOT / "skills" / "english-exam-ai-tutor" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from visualize import generate_report, _compute_ability_levels, _compute_trend_data
from summarize_errors import summarize_errors
from record_practice import record_practice


class TestVisualization(unittest.TestCase):
    def setUp(self):
        self.tmp = REPO_ROOT / ".task8-test-tmp" / "test_visualize"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.tmp / "practice-ledger.json"
        if self.ledger_path.exists():
            self.ledger_path.unlink()

    def test_generates_html(self):
        """generate_report produces valid HTML output."""
        ability = [{
            "modules": {
                "vocabulary": [{"node": "拼写", "level": 5}],
                "reading": [{"node": "阅读速度", "level": 6}],
                "writing": [{"node": "结构逻辑", "level": 4}],
            }
        }]
        html = generate_report(ability, [], title="Test Report", days=30)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Test Report", html)
        self.assertIn("<svg", html)

    def test_ability_levels_computation(self):
        """_compute_ability_levels returns normalized levels."""
        history = [{
            "modules": {
                "vocabulary": [{"node": "拼写", "level": 5}, {"node": "词义识别", "level": 7}],
                "reading": [{"node": "阅读速度", "level": 8}],
            }
        }]
        levels = _compute_ability_levels(history)
        self.assertAlmostEqual(levels["vocabulary"], 0.6)  # (5+7)/2/10
        self.assertAlmostEqual(levels["reading"], 0.8)     # 8/10

    def test_trend_data_from_ledger(self):
        """_compute_trend_data extracts daily accuracy per module."""
        ledger = [
            {"date": "2026-07-01", "module": "reading", "total_items": 10, "correct_items": 7},
            {"date": "2026-07-01", "module": "writing", "total_items": 10, "correct_items": 5},
            {"date": "2026-07-02", "module": "reading", "total_items": 10, "correct_items": 8},
        ]
        dates, trends = _compute_trend_data(ledger)
        self.assertEqual(len(dates), 2)
        self.assertIn("reading", trends)
        self.assertIn("writing", trends)

    def test_report_includes_speed_verdict(self):
        """HTML report includes speed analysis verdict when available."""
        rec = {
            "date": "2026-07-01", "exam_type": "CET4", "module": "reading",
            "task_id": "t1", "duration_minutes": 35, "total_items": 20,
            "correct_items": 14, "timed": True, "time_limit_minutes": 40,
            "overtime_items": 5, "overtime_correct": 4, "error_tags": [],
        }
        record_practice(self.ledger_path, rec)
        summary = summarize_errors(self.ledger_path)

        ability = [{"modules": {}}]
        html = generate_report(ability, [rec], error_summary=summary)
        self.assertIn("速度诊断", html)

    def test_cli_command_registered(self):
        """visualize command is in CLI."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "skills.english_exam_ai_tutor", "visualize", "--help"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0)

    def test_report_output_file(self):
        """Full pipeline: generate report and write to file."""
        ability = [{"modules": {"reading": [{"node": "阅读速度", "level": 6}]}}]
        ledger = [
            {"date": "2026-07-01", "module": "reading", "total_items": 10, "correct_items": 7,
             "exam_type": "CET4", "task_id": "t1", "duration_minutes": 20, "error_tags": []}
        ]
        html = generate_report(ability, ledger, title="Unit Test", days=30)
        out = self.tmp / "test-report.html"
        out.write_text(html, encoding="utf-8")
        self.assertGreater(out.stat().st_size, 100)
        content = out.read_text("utf-8")
        self.assertIn("Unit Test", content)
        self.assertIn("radar", content)


class TestSampleEssays(unittest.TestCase):
    def test_index_loads(self):
        """Sample essay index is valid JSON and all paths exist."""
        base = (REPO_ROOT / "skills" / "english-exam-ai-tutor"
                / "assets" / "data" / "sample-essays")
        index = json.loads((base / "index.json").read_text("utf-8"))
        for key, info in index.items():
            sub_index = json.loads((base / info["path"]).read_text("utf-8"))
            self.assertIn("exam_type", sub_index)
            self.assertIn("bands", sub_index)

    def test_samples_valid(self):
        """All sample essays have required fields."""
        base = (REPO_ROOT / "skills" / "english-exam-ai-tutor"
                / "assets" / "data" / "sample-essays")
        # Walk and check JSON files
        for f in base.rglob("*.json"):
            data = json.loads(f.read_text("utf-8"))
            if "sample_id" in data:  # essay file, not index
                required = ["sample_id", "exam_type", "module", "topic", "band",
                            "essay_text", "rubric_scores"]
                for field in required:
                    self.assertIn(field, data, f"{f.name}: missing {field}")
                self.assertGreater(len(data["essay_text"]), 50)


if __name__ == "__main__":
    unittest.main()
