import tempfile
import unittest
from pathlib import Path

from examlex.scripts import common, validate_profile


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


class ProfileValidationTests(unittest.TestCase):
    def test_valid_cet4_profile_returns_no_errors(self):
        profile = {
            "learner_id": "learner-001",
            "exam_type": "CET4",
            "foundation_level": "中等基础",
            "target_band": "550+",
            "daily_time_budget_minutes": 45,
        }

        self.assertEqual(validate_profile.validate_profile(profile), [])

    def test_postgraduate_english_rejects_cet_target_band(self):
        profile = {
            "learner_id": "learner-001",
            "exam_type": "POSTGRADUATE_ENGLISH",
            "foundation_level": "基础较好",
            "target_band": "550+",
            "daily_time_budget_minutes": 45,
        }

        self.assertIn(
            "target_band must be one of 50+, 70~80, 80+, 90+ for POSTGRADUATE_ENGLISH",
            validate_profile.validate_profile(profile),
        )

    def test_daily_time_budget_zero_is_rejected(self):
        profile = {
            "learner_id": "learner-001",
            "exam_type": "CET4",
            "foundation_level": "基础偏弱",
            "target_band": "425~499",
            "daily_time_budget_minutes": 0,
        }

        self.assertIn(
            "daily_time_budget_minutes must be a positive integer",
            validate_profile.validate_profile(profile),
        )


if __name__ == "__main__":
    unittest.main()
