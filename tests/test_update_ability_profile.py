import unittest
from pathlib import Path

from examlex.scripts import common, update_ability_profile


class UpdateAbilityProfileTests(unittest.TestCase):
    def test_replaying_the_complete_ledger_is_idempotent(self):
        profile = {
            "modules": {
                "reading": [
                    {
                        "node": "location",
                        "level": 1,
                        "status": "priority",
                        "stats": {
                            "total_items": 99,
                            "correct_items": 1,
                            "error_count": 7,
                            "accuracy": 0.01,
                        },
                    }
                ]
            }
        }
        ledger = [
            {
                "module": "reading",
                "total_items": 10,
                "correct_items": 8,
                "error_tags": ["READING_LOCATION_FAIL"],
            }
        ]

        first = update_ability_profile.update_ability_profile(profile, ledger)
        second = update_ability_profile.update_ability_profile(first, ledger)

        self.assertEqual(first, second)
        error_dimension = common.ERROR_TAG_TO_ABILITY["READING_LOCATION_FAIL"][1]
        error_node = next(
            node
            for node in first["modules"]["reading"]
            if node["node"] == error_dimension
        )
        self.assertEqual(
            error_node["stats"],
            {
                "total_items": 10,
                "correct_items": 8,
                "error_count": 1,
                "accuracy": 0.8,
            },
        )

    def test_updates_existing_nodes_with_item_stats_and_error_tag_stats(self):
        profile = {
            "learner_id": "learner-001",
            "modules": {
                "reading": [{"node": "location", "level": 3, "status": "stable"}],
                "writing": [
                    {
                        "node": common.ERROR_TAG_TO_ABILITY["WRITING_ARTICLE_OMISSION"][1],
                        "level": 3,
                        "status": "stable",
                    }
                ],
            },
        }
        ledger = [
            {
                "module": "reading",
                "total_items": 10,
                "correct_items": 5,
                "error_tags": ["WRITING_ARTICLE_OMISSION", "WRITING_ARTICLE_OMISSION"],
            }
        ]

        updated = update_ability_profile.update_ability_profile(profile, ledger)

        reading = updated["modules"]["reading"][0]
        self.assertEqual(reading["stats"]["total_items"], 10)
        self.assertEqual(reading["stats"]["correct_items"], 5)
        self.assertEqual(reading["status"], "priority")
        self.assertEqual(reading["level"], 1)
        writing_accuracy = updated["modules"]["writing"][0]
        self.assertEqual(writing_accuracy["stats"]["error_count"], 2)
        self.assertEqual(writing_accuracy["status"], "priority")
        self.assertEqual(writing_accuracy["level"], 1)
        self.assertNotIn("total", reading["stats"])
        self.assertNotIn("correct", reading["stats"])

    def test_cli_writes_output_without_mutating_input_when_output_supplied(self):
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        ability_path = root / "task6-ability.json"
        ledger_path = root / "task6-ledger.json"
        output_path = root / "task6-updated-ability.json"
        try:
            ability_path.write_text(
                '{"modules":{"reading":[{"node":"speed","level":3,"status":"stable"}]}}',
                encoding="utf-8",
            )
            ledger_path.write_text(
                '[{"module":"reading","total_items":5,"correct_items":5,"error_tags":[]}]',
                encoding="utf-8",
            )

            self.assertEqual(
                update_ability_profile.main(
                    ["--ability", str(ability_path), "--ledger", str(ledger_path), "--output", str(output_path)]
                ),
                0,
            )

            self.assertNotIn('"stats"', ability_path.read_text(encoding="utf-8"))
            self.assertIn('"total_items": 5', output_path.read_text(encoding="utf-8"))
        finally:
            for path in (ability_path, ledger_path, output_path):
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
