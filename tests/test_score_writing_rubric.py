import json
import unittest
from pathlib import Path

from examlex.scripts import score_writing_rubric


class ScoreWritingRubricTests(unittest.TestCase):
    def test_scores_four_dimensions_with_rationales_and_estimate_label(self):
        text = (
            "Online learning has become common for college students. It gives learners flexible access "
            "to lectures and review materials.\n\nFirst, students can repeat difficult lessons at their "
            "own pace. However, they still need discipline because distractions are everywhere.\n\nIn "
            "conclusion, online learning is useful when schools combine clear guidance with regular "
            "practice and feedback."
        )

        result = score_writing_rubric.score_writing(text, "CET4")

        self.assertEqual(result["label"], "training_rubric_estimate_not_official")
        self.assertEqual(result["exam_type"], "CET4")
        self.assertEqual(set(result["dimensions"]), set(score_writing_rubric.DIMENSIONS))
        self.assertGreater(result["total_score"], 0)
        self.assertLessEqual(result["total_score"], result["max_score"])
        self.assertGreaterEqual(result["normalized_score"], 0)
        self.assertEqual("anchored", result["calibration_status"])
        self.assertGreaterEqual(result["anchor_summary"]["anchor_count"], 1)
        for dimension in score_writing_rubric.DIMENSIONS:
            self.assertIn("rationale", result["dimensions"][dimension])

    def test_cli_scores_text_file_to_output(self):
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        text_path = root / "task6-writing.txt"
        output_path = root / "task6-writing-score.json"
        try:
            text_path.write_text("I think practice is important. First, it builds skill. In conclusion, it helps.", encoding="utf-8")

            self.assertEqual(
                score_writing_rubric.main(
                    ["--text-file", str(text_path), "--exam-type", "CET6", "--output", str(output_path)]
                ),
                0,
            )

            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result["label"], "training_rubric_estimate_not_official")
            self.assertEqual(result["exam_type"], "CET6")
        finally:
            for path in (text_path, output_path):
                if path.exists():
                    path.unlink()

    def test_correct_articles_and_subjunctive_are_not_false_positives(self):
        text = (
            "A university can offer an hour of guided practice. "
            "It is essential that he go to the workshop, and does it have enough seats?"
        )
        risks = score_writing_rubric._grammar_risks(text)
        self.assertEqual([], risks)

    def test_prompt_coverage_and_all_five_exam_anchors(self):
        sample_root = score_writing_rubric.default_reference_samples()
        for exam_type in ("CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8"):
            anchors = score_writing_rubric.load_reference_samples(sample_root, exam_type)
            self.assertGreaterEqual(len(anchors), 1, exam_type)
        result = score_writing_rubric.score_writing(
            "Digital tools help students study, but students must verify information and protect attention.",
            "TEM4",
            prompt="Discuss how students can use digital tools responsibly.",
        )
        self.assertIsNotNone(result["signals"]["prompt_keyword_coverage"])


if __name__ == "__main__":
    unittest.main()
