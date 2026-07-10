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

        self.assertEqual(result["label"], "rubric_estimate")
        self.assertEqual(result["exam_type"], "CET4")
        self.assertEqual(set(result["dimensions"]), set(score_writing_rubric.DIMENSIONS))
        self.assertGreater(result["total_score"], 0)
        self.assertLessEqual(result["total_score"], result["max_score"])
        self.assertGreaterEqual(result["normalized_score"], 0)
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
            self.assertEqual(result["label"], "rubric_estimate")
            self.assertEqual(result["exam_type"], "CET6")
        finally:
            for path in (text_path, output_path):
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
