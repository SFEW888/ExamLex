from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# Ensure we can import from the package
REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO_ROOT / "skills" / "examlex" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import vocab_generator
from vocab_generator import generate_all, generate_level, validate_entry, load_schema


class TestVocabPool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vocab_dir = REPO_ROOT / "skills" / "examlex" / "assets" / "data" / "vocabulary"
        cls.schema = load_schema()

    def test_index_exists(self):
        """index.json can be loaded and all paths exist."""
        index_path = self.vocab_dir / "index.json"
        self.assertTrue(index_path.exists(), "index.json should exist")
        index = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertGreater(len(index), 0, "index.json should have entries")
        for key, info in index.items():
            path = self.vocab_dir / info["path"]
            self.assertTrue(path.exists(), f"Vocabulary file {info['path']} should exist")

    def test_index_has_all_levels(self):
        """index.json covers all 5 exam levels."""
        index_path = self.vocab_dir / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        expected_keys = {"cet4-core-2000", "cet6-core-1500", "postgraduate-core-1000",
                         "tem4-core-2000", "tem8-core-2000"}
        self.assertEqual(set(index.keys()), expected_keys)

    def test_all_entries_valid(self):
        """All vocabulary entries pass schema validation."""
        index_path = self.vocab_dir / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        total_errors = 0
        for key, info in index.items():
            path = self.vocab_dir / info["path"]
            data = json.loads(path.read_text(encoding="utf-8"))
            for i, entry in enumerate(data):
                errs = validate_entry(entry, self.schema)
                if errs:
                    total_errors += 1
        self.assertEqual(total_errors, 0, f"Found {total_errors} validation errors in vocabulary entries")

    def test_cet4_sorted_by_frequency(self):
        """cet4-core-2000.json entries are sorted by frequency_rank ascending."""
        path = self.vocab_dir / "cet4-core-2000.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        ranks = [e["frequency_rank"] for e in data]
        self.assertEqual(ranks, sorted(ranks), "cet4-core-2000 should be sorted by frequency_rank")

    def test_cet6_sorted_by_frequency(self):
        """cet6-core-1500.json entries are sorted by frequency_rank ascending."""
        path = self.vocab_dir / "cet6-core-1500.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        ranks = [e["frequency_rank"] for e in data]
        self.assertEqual(ranks, sorted(ranks))

    def test_daily_vocab_selection_respects_count(self):
        """select_daily_vocab returns no more than count entries."""
        from generate_daily_plan import select_daily_vocab
        pool = [{"word": f"word_{i}", "frequency_rank": i,
                 "meaning_cn": "测试", "synonyms": [], "collocations": []}
                for i in range(1, 51)]
        ability = {"modules": {}}
        for count in [5, 10, 20]:
            result = select_daily_vocab(pool, ability, 60, count=count)
            self.assertLessEqual(len(result), count,
                                 f"select_daily_vocab should return <= {count} for limit {count}")

    def test_daily_vocab_prioritizes_needs_work(self):
        """Words matching 'needs_work' ability nodes are prioritized."""
        from generate_daily_plan import select_daily_vocab
        pool = [
            {"word": "abandon", "frequency_rank": 100, "meaning_cn": "放弃",
             "synonyms": ["give up", "desert"], "collocations": []},
            {"word": "ability", "frequency_rank": 1, "meaning_cn": "能力",
             "synonyms": ["capability"], "collocations": []},
            {"word": "abstract", "frequency_rank": 50, "meaning_cn": "抽象的",
             "synonyms": ["theoretical"], "collocations": []},
        ]
        ability = {"modules": {
            "vocabulary": [{"node": "词义识别", "status": "needs_work"}],
        }}
        # "give up" matches "词义识别" dimension — actually, the match is based on
        # word/pos/synonyms/collocations containing the dimension text.
        # Let's test with a dimension that literally matches a word
        ability2 = {"modules": {
            "vocabulary": [{"node": "capability", "status": "needs_work"}],
        }}
        result = select_daily_vocab(pool, ability2, 60, count=2)
        # "ability" has "capability" as synonym → should be scored higher
        words = [r["word"] for r in result]
        self.assertIn("ability", words[:2])

    def test_cet6_no_overlap_with_cet4(self):
        """cet6-core-1500 and cet4-core-2000 have no duplicate words."""
        cet4_path = self.vocab_dir / "cet4-core-2000.json"
        cet6_path = self.vocab_dir / "cet6-core-1500.json"
        cet4_words = {e["word"].lower() for e in json.loads(cet4_path.read_text(encoding="utf-8"))}
        cet6_words = {e["word"].lower() for e in json.loads(cet6_path.read_text(encoding="utf-8"))}
        overlap = cet4_words & cet6_words
        self.assertEqual(len(overlap), 0,
                         f"CET-6 words overlap with CET-4: {overlap}")

    def test_vocab_pool_in_daily_plan(self):
        """Daily plan with --vocab-pool includes vocabulary tasks."""
        from generate_daily_plan import generate_daily_plan
        profile = {"learner_id": "test1", "exam_type": "CET4", "daily_time_budget_minutes": 60}
        ability = {"modules": {"vocabulary": [{"node": "拼写", "status": "needs_work", "level": 3}]}}
        vocab_pool = [
            {"word": "abandon", "frequency_rank": 1, "meaning_cn": "放弃", "synonyms": [], "collocations": []},
            {"word": "abstract", "frequency_rank": 50, "meaning_cn": "抽象的", "synonyms": [], "collocations": []},
        ]
        plan = generate_daily_plan(profile, ability, vocab_pool=vocab_pool)
        has_vocab_task = any(
            t.get("module") == "vocabulary" and "vocab_items" in t
            for t in plan.get("tasks", [])
        )
        self.assertTrue(has_vocab_task, "Plan should include a vocabulary task with vocab_items")

    def test_vocab_pool_none_does_not_crash(self):
        """generate_daily_plan handles vocab_pool=None gracefully."""
        from generate_daily_plan import generate_daily_plan
        profile = {"learner_id": "test2", "exam_type": "CET6", "daily_time_budget_minutes": 30}
        ability = {"modules": {}}
        plan = generate_daily_plan(profile, ability, vocab_pool=None)
        self.assertIn("tasks", plan)
        # Should still produce a plan (fallback task)
        self.assertGreater(len(plan["tasks"]), 0)

    def test_vocab_generator_regenerate_is_stable(self):
        """Re-generating vocabulary produces the same count."""
        cet4 = generate_level("CET4")
        self.assertGreater(len(cet4), 0)
        cet4_again = generate_level("CET4")
        self.assertEqual(len(cet4), len(cet4_again))

    def test_validate_generated_vocab_is_clean(self):
        """Generated vocabulary should pass validation."""
        schema = load_schema()
        for level in ["CET4", "CET6", "POSTGRADUATE", "TEM4", "TEM8"]:
            entries = generate_level(level)
            for entry in entries:
                errs = validate_entry(entry, schema)
                self.assertEqual(errs, [], f"{level} entry {entry.get('word')} has errors: {errs}")


if __name__ == "__main__":
    unittest.main()
