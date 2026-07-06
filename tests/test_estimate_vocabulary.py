from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO_ROOT / "skills" / "english-exam-ai-tutor" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from estimate_vocabulary import (
    estimate,
    suggest_foundation,
    generate_interactive_quiz,
    get_band_size,
    load_reference,
)


class TestEstimateVocabulary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_reference()
        cls.bands = cls.reference.get("bands", {})

    def _make_answers(self, known_map=None):
        """Build answers list from reference bands. known_map is {word: known}."""
        if known_map is None:
            known_map = {}
        answers = []
        for band_label, band in sorted(self.bands.items()):
            for w in band.get("real_words", []):
                answers.append({"word": w, "band": band_label, "is_real": True,
                                "known": known_map.get(w, True)})
            for w in band.get("non_words", []):
                answers.append({"word": w, "band": band_label, "is_real": False,
                                "known": known_map.get(w, False)})
        return answers

    def test_perfect_score(self):
        """All real words known, no non-words claimed → estimate ≈ total."""
        answers = self._make_answers()  # default: all real=True known, non=False unknown
        result = estimate(self.bands, answers, "learner-perfect")
        self.assertGreater(result["estimated_vocabulary"], 4000)
        self.assertEqual(result["false_alarm_rate"], 0.0)
        self.assertEqual(result["method"], "yes-no-sampling")

    def test_zero_knowledge(self):
        """No real words known → estimate ≈ 0."""
        known_map = {w: False for band in self.bands.values()
                     for w in band.get("real_words", [])}
        answers = self._make_answers(known_map)
        result = estimate(self.bands, answers, "learner-zero")
        self.assertEqual(result["estimated_vocabulary"], 0)

    def test_false_alarm_correction(self):
        """All non-words claimed as known (FA=1.0) → heavily corrected estimate."""
        known_map = {w: True for band in self.bands.values()
                     for w in band.get("non_words", [])}
        answers = self._make_answers(known_map)
        result = estimate(self.bands, answers, "learner-fa")
        # FA = 1.0 means adjusted_rate = 0 for all bands → estimate = 0
        self.assertEqual(result["estimated_vocabulary"], 0)
        self.assertEqual(result["false_alarm_rate"], 1.0)

    def test_partial_knowledge(self):
        """Simulate ~2000-3000 word vocabulary."""
        known_map = {}
        for band_label in ["1-1000", "1001-2000"]:
            band = self.bands[band_label]
            for w in band.get("real_words", []):
                known_map[w] = True
        for band_label in ["2001-3000", "3001-4000"]:
            band = self.bands[band_label]
            for w in band.get("real_words", []):
                known_map[w] = True  # knows most
        answers = self._make_answers(known_map)
        result = estimate(self.bands, answers, "learner-partial")
        self.assertGreater(result["estimated_vocabulary"], 2000)
        self.assertLessEqual(result["estimated_vocabulary"], 6000)

    def test_single_band_only(self):
        """Only one band has answers."""
        band_1k = self.bands["1-1000"]
        answers = []
        for w in band_1k.get("real_words", [])[:10]:
            answers.append({"word": w, "band": "1-1000", "is_real": True, "known": True})
        result = estimate(self.bands, answers, "learner-single")
        # Should estimate for band 1-1000 only
        self.assertGreater(result["estimated_vocabulary"], 0)
        self.assertIn("1-1000", result["by_band"])

    def test_output_json_format(self):
        """Result conforms to expected schema structure."""
        answers = self._make_answers()
        result = estimate(self.bands, answers, "learner-test")
        # Required fields
        self.assertIn("learner_id", result)
        self.assertIn("test_date", result)
        self.assertIn("method", result)
        self.assertIn("estimated_vocabulary", result)
        self.assertIn("confidence_interval", result)
        self.assertIn("false_alarm_rate", result)
        self.assertIn("by_band", result)
        # Confidence interval structure
        ci = result["confidence_interval"]
        self.assertEqual(len(ci), 2)
        self.assertGreaterEqual(ci[1], ci[0])
        # by_band structure
        for band_label, band_info in result["by_band"].items():
            self.assertIn("tested", band_info)
            self.assertIn("claimed", band_info)
            self.assertIn("estimated", band_info)

    def test_suggest_foundation_weak(self):
        """vocab < 2000 → 基础偏弱."""
        self.assertEqual(suggest_foundation(0), "基础偏弱")
        self.assertEqual(suggest_foundation(1500), "基础偏弱")
        self.assertEqual(suggest_foundation(1999), "基础偏弱")

    def test_suggest_foundation_mid(self):
        """vocab 2000-3999 → 中等基础."""
        self.assertEqual(suggest_foundation(2000), "中等基础")
        self.assertEqual(suggest_foundation(3000), "中等基础")
        self.assertEqual(suggest_foundation(3999), "中等基础")

    def test_suggest_foundation_strong(self):
        """vocab >= 4000 → 基础较好."""
        self.assertEqual(suggest_foundation(4000), "基础较好")
        self.assertEqual(suggest_foundation(8000), "基础较好")

    def test_band_size_parsing(self):
        """get_band_size parses band labels correctly."""
        self.assertEqual(get_band_size("1-1000"), 1000)
        self.assertEqual(get_band_size("1001-2000"), 1000)
        self.assertEqual(get_band_size("2001-3000"), 1000)
        self.assertEqual(get_band_size("3001-4000"), 1000)
        self.assertEqual(get_band_size("4001-5000"), 1000)
        self.assertEqual(get_band_size("5001-6000"), 1000)
        self.assertEqual(get_band_size("5000+"), 1000)
        self.assertEqual(get_band_size("invalid"), 0)

    def test_interactive_quiz_generation(self):
        """Interactive mode generates quiz words with correct structure."""
        quiz = generate_interactive_quiz(self.reference, bands=["1-1000"],
                                         samples_per_band=5, nonwords_per_band=2)
        self.assertIsInstance(quiz, list)
        self.assertGreater(len(quiz), 0)
        for item in quiz:
            self.assertIn("word", item)
            self.assertIn("band", item)
            self.assertIn("is_real", item)
            self.assertIn("known", item)
            self.assertIsNone(item["known"])

        # Check counts: 5 real + 2 non = 7 for band 1-1000
        real = [q for q in quiz if q["is_real"]]
        fake = [q for q in quiz if not q["is_real"]]
        self.assertEqual(len(real), 5)
        self.assertEqual(len(fake), 2)


class TestVocabEstimateCLI(unittest.TestCase):
    """Integration tests for the vocab-estimate CLI command."""

    def setUp(self):
        self.tmp = REPO_ROOT / ".task8-test-tmp" / "test_estimate_vocab"
        self.tmp.mkdir(parents=True, exist_ok=True)

    def test_cli_registered(self):
        """english-exam-tutor vocab-estimate --help runs successfully."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "skills.english_exam_ai_tutor", "vocab-estimate", "--help"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn("usage", result.stdout.lower() or "usage")

    def test_batch_mode_with_wordlist(self):
        """Batch mode processes a wordlist and produces valid output."""
        wordlist_path = self.tmp / "answers.json"
        ref_path = (REPO_ROOT / "skills" / "english-exam-ai-tutor"
                    / "assets" / "data" / "vocab-test-words.json")
        answers = {
            "learner_id": "cli-test",
            "test_date": "2026-07-06",
            "answers": [
                {"word": "the", "band": "1-1000", "is_real": True, "known": True},
                {"word": "abandon", "band": "1001-2000", "is_real": True, "known": True},
                {"word": "flompery", "band": "1-1000", "is_real": False, "known": False},
            ],
        }
        wordlist_path.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")

        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "skills.english_exam_ai_tutor", "vocab-estimate",
             "--wordlist", str(wordlist_path), "--reference", str(ref_path)],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        output = (result.stdout + result.stderr).strip()
        self.assertIn("estimated_vocabulary", output)

    def test_interactive_mode(self):
        """Interactive mode generates quiz output."""
        ref_path = (REPO_ROOT / "skills" / "english-exam-ai-tutor"
                    / "assets" / "data" / "vocab-test-words.json")
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "skills.english_exam_ai_tutor", "vocab-estimate",
             "--interactive", "--bands", "1-1000", "--samples-per-band", "3",
             "--nonwords-per-band", "1", "--reference", str(ref_path)],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        output = result.stdout
        data = json.loads(output)
        self.assertIn("quiz_words", data)
        self.assertEqual(len(data["quiz_words"]), 4)  # 3 real + 1 non


if __name__ == "__main__":
    unittest.main()
