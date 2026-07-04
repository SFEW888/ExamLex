import tempfile
import unittest
from pathlib import Path

from skills.english_exam_ai_tutor.scripts import common


class CommonRuntimeTests(unittest.TestCase):
    def test_load_json_compatible_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text(
                '{"exam_type": "CET4", "target_band": "550+"}',
                encoding="utf-8",
            )
            self.assertEqual(common.load_data(path)["target_band"], "550+")

    def test_supported_error_tags_include_article_omission(self):
        self.assertIn("WRITING_ARTICLE_OMISSION", common.ERROR_TAG_TO_ABILITY)


if __name__ == "__main__":
    unittest.main()
