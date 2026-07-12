import unittest
import json
from pathlib import Path

from examlex.scripts import generate_daily_plan


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GenerateDailyPlanTests(unittest.TestCase):
    def test_packaged_ability_template_produces_real_candidates(self):
        ability = json.loads(
            (PROJECT_ROOT / "examlex/assets/templates/ability-profile.yaml").read_text(
                encoding="utf-8"
            )
        )

        candidates = generate_daily_plan._ability_candidates(ability)

        self.assertGreaterEqual(len(candidates), 5)
        self.assertTrue(
            all(candidate["node"] != candidate["module"] for candidate in candidates)
        )

    def test_plan_never_exceeds_daily_budget_and_prioritizes_errors(self):
        profile = {
            "learner_id": "learner-001",
            "exam_type": "CET4",
            "daily_time_budget_minutes": 35,
        }
        ability = {
            "modules": {
                "reading": [{"node": "paraphrase", "level": 1, "status": "priority"}],
                "writing": [{"node": "accuracy", "level": 2, "status": "needs_work"}],
            }
        }
        errors = {"by_tag": {"WRITING_ARTICLE_OMISSION": {"count": 3}}}

        plan = generate_daily_plan.generate_daily_plan(profile, ability, errors)

        self.assertLessEqual(plan["total_planned_minutes"], 35)
        self.assertEqual(sum(item["minutes"] for item in plan["tasks"]), plan["total_planned_minutes"])
        self.assertTrue(
            any("WRITING_ARTICLE_OMISSION" in task["reason"] for task in plan["tasks"]),
            plan,
        )

    def test_cli_writes_plan_json(self):
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        profile_path = root / "task5-profile.json"
        ability_path = root / "task5-ability.json"
        output_path = root / "task5-plan.json"
        try:
            profile_path.write_text(
                '{"learner_id":"learner-001","exam_type":"CET4","daily_time_budget_minutes":20}',
                encoding="utf-8",
            )
            ability_path.write_text(
                '{"modules":{"listening":[{"node":"numbers","level":1,"status":"priority"}]}}',
                encoding="utf-8",
            )

            self.assertEqual(
                generate_daily_plan.main(
                    [
                        "--profile",
                        str(profile_path),
                        "--ability",
                        str(ability_path),
                        "--output",
                        str(output_path),
                    ]
                ),
                0,
            )

            self.assertIn('"total_planned_minutes"', output_path.read_text(encoding="utf-8"))
        finally:
            for path in (profile_path, ability_path, output_path):
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
