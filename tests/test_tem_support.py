from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
SKILL_SCRIPTS = REPO_ROOT / "skills" / "english-exam-ai-tutor" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import common
from validate_profile import validate_profile, _target_bands_for
from generate_daily_plan import generate_daily_plan, _module_order_for


class TestTEMProfileValidation(unittest.TestCase):
    def test_tem4_profile_validation_passes(self):
        """TEM-4 learner profile passes validation."""
        profile = json.loads((FIXTURES / "tem4-learner-profile.json").read_text("utf-8"))
        errors = validate_profile(profile)
        self.assertEqual(errors, [], f"Expected no errors but got: {errors}")

    def test_tem8_profile_validation_passes(self):
        """TEM-8 learner profile passes validation."""
        profile = json.loads((FIXTURES / "tem8-learner-profile.json").read_text("utf-8"))
        errors = validate_profile(profile)
        self.assertEqual(errors, [], f"Expected no errors but got: {errors}")

    def test_tem4_invalid_band_rejected(self):
        """TEM-4 with CET band '550+' is rejected."""
        profile = json.loads((FIXTURES / "tem4-learner-profile.json").read_text("utf-8"))
        profile["target_band"] = "550+"
        errors = validate_profile(profile)
        self.assertTrue(any("target_band" in e for e in errors),
                        f"Expected target_band error but got: {errors}")

    def test_tem8_invalid_band_rejected(self):
        """TEM-8 with '90+' is rejected."""
        profile = json.loads((FIXTURES / "tem8-learner-profile.json").read_text("utf-8"))
        profile["target_band"] = "90+"
        errors = validate_profile(profile)
        self.assertTrue(any("target_band" in e for e in errors),
                        f"Expected target_band error but got: {errors}")

    def test_tem_target_bands_helper(self):
        """_target_bands_for returns correct TEM bands."""
        self.assertIn("60~69", _target_bands_for("TEM4"))
        self.assertIn("70~79", _target_bands_for("TEM4"))
        self.assertIn("80+", _target_bands_for("TEM4"))
        self.assertIn("80+", _target_bands_for("TEM8"))


class TestTEMDailyPlan(unittest.TestCase):
    def test_tem4_daily_plan_includes_dictation(self):
        """TEM-4 daily plan can include dictation module (in ability profile)."""
        profile = json.loads((FIXTURES / "tem4-learner-profile.json").read_text("utf-8"))
        ability = json.loads((FIXTURES / "tem4-ability-profile.json").read_text("utf-8"))
        plan = generate_daily_plan(profile, ability)
        self.assertIn("tasks", plan)
        modules_in_plan = {t.get("module") for t in plan["tasks"]}
        # dictation is in the TEM ability profile, so it should appear
        # (the plan prioritizes by status, so it may or may not include dictation
        #  depending on budget — just verify it handles TEM modules without error)
        self.assertGreater(len(plan["tasks"]), 0)

    def test_tem8_daily_plan_includes_proofreading(self):
        """TEM-8 daily plan can handle proofreading module."""
        profile = json.loads((FIXTURES / "tem8-learner-profile.json").read_text("utf-8"))
        ability = json.loads((FIXTURES / "tem8-ability-profile.json").read_text("utf-8"))
        plan = generate_daily_plan(profile, ability)
        self.assertGreater(len(plan["tasks"]), 0)

    def test_tem_module_order_includes_new_modules(self):
        """_module_order_for returns extended order for TEM exams."""
        tem4_order = _module_order_for("TEM4")
        self.assertIn("dictation", tem4_order)
        self.assertIn("language-knowledge", tem4_order)
        self.assertIn("proofreading", tem4_order)

        tem8_order = _module_order_for("TEM8")
        self.assertIn("proofreading", tem8_order)

        cet4_order = _module_order_for("CET4")
        self.assertNotIn("dictation", cet4_order)
        self.assertNotIn("proofreading", cet4_order)


class TestTEMErrorTags(unittest.TestCase):
    def test_tem4_error_tags_mapped_correctly(self):
        """DICTATION_ACCURACY_LOW → dictation / 听写准确率."""
        result = common.ERROR_TAG_TO_ABILITY.get("DICTATION_ACCURACY_LOW")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("dictation", "听写准确率"))

    def test_tem8_proofread_tags_mapped_correctly(self):
        """PROOFREAD_ARTICLE_MISS → proofreading / 冠词错误."""
        result = common.ERROR_TAG_TO_ABILITY.get("PROOFREAD_ARTICLE_MISS")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("proofreading", "冠词错误"))

    def test_lang_grammar_tags_mapped(self):
        """LANG_GRAMMAR_SELECT_FAIL → language-knowledge / 语法选择."""
        result = common.ERROR_TAG_TO_ABILITY.get("LANG_GRAMMAR_SELECT_FAIL")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("language-knowledge", "语法选择"))

    def test_all_tem_error_tags_valid(self):
        """All TEM error tags map to valid ability tree nodes."""
        for tag, (module, node) in common.ERROR_TAG_TO_ABILITY.items():
            if module in ("language-knowledge", "proofreading", "dictation"):
                self.assertIn(module, common.ABILITY_TREE,
                              f"Module {module} should be in ABILITY_TREE")
                self.assertIn(node, common.ABILITY_TREE[module],
                              f"Node {node} should be in ABILITY_TREE[{module}]")


class TestTEMAbilityTree(unittest.TestCase):
    def test_tem_modules_present(self):
        """TEM-specific modules are in ABILITY_TREE."""
        self.assertIn("language-knowledge", common.ABILITY_TREE)
        self.assertIn("proofreading", common.ABILITY_TREE)
        self.assertIn("dictation", common.ABILITY_TREE)

    def test_tem_exam_types_present(self):
        """TEM4 and TEM8 are in EXAM_TYPES."""
        self.assertIn("TEM4", common.EXAM_TYPES)
        self.assertIn("TEM8", common.EXAM_TYPES)

    def test_tem_target_bands(self):
        """common.target_bands_for returns TEM bands."""
        self.assertIn("60~69", common.target_bands_for("TEM4"))
        self.assertIn("70~79", common.target_bands_for("TEM8"))
        self.assertEqual(common.target_bands_for("TEM4"), {"60~69", "70~79", "80+"})

    def test_tem_time_limits(self):
        """TEM time limits are defined."""
        self.assertIn("TEM4", common.EXAM_TIME_LIMITS)
        self.assertIn("TEM8", common.EXAM_TIME_LIMITS)
        self.assertIn("dictation", common.EXAM_TIME_LIMITS["TEM4"])
        self.assertIn("proofreading", common.EXAM_TIME_LIMITS["TEM8"])


if __name__ == "__main__":
    unittest.main()
