"""CI-discoverable end-to-end contract for continuous learning."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from examlex.scripts import common, generate_daily_plan, ingest_strategy


class ContinuousLearningEndToEndTests(unittest.TestCase):
    def test_draft_to_approved_strategy_contract(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "reading-method.md"
            library_path = root / "strategy-library.json"
            source.write_text(
                "1. Preview question stems.\n2. Locate evidence.\n3. Verify the option.\n",
                encoding="utf-8",
            )

            draft = ingest_strategy.ingest_strategy(
                file_path=source,
                library_path=library_path,
                exam_types=["CET4"],
                modules=["reading"],
            )

            self.assertEqual(draft["lifecycle_status"], "draft")
            self.assertRegex(draft["strategy_id"], r"^cet4-reading-[a-z0-9-]+-001$")
            self.assertEqual(set(common.SOURCE_TYPES), {
                "text", "book", "video", "podcast", "person", "course", "conversation",
            })

            approved_content = {
                **draft,
                "lifecycle_status": "approved",
                "darwin_score": 80,
            }
            snapshot = dict(approved_content)
            revision_sha256 = hashlib.sha256(
                json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            approved = {
                **approved_content,
                "revisions": [{
                    "version": 1,
                    "sha256": revision_sha256,
                    "strategy": snapshot,
                }],
            }
            plan = generate_daily_plan.generate_daily_plan(
                {"learner_id": "learner", "exam_type": "CET4", "daily_time_budget_minutes": 20},
                {"modules": {"reading": [{"node": "locating", "level": 1, "status": "priority"}]}},
                strategies={"strategies": [draft, approved]},
            )
            hints = [hint for task in plan["tasks"] for hint in task.get("strategy_hints", [])]
            self.assertEqual([hint["strategy_id"] for hint in hints], [approved["strategy_id"]])
            self.assertEqual(hints[0]["revision_sha256"], revision_sha256)

    def test_schema_and_thin_import_bridge_are_current(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads(
            (root / "skills" / "examlex" / "assets" / "schemas" / "strategy-library.schema.json").read_text(encoding="utf-8")
        )
        properties = schema["properties"]["strategies"]["items"]["properties"]
        self.assertEqual(set(properties["source_type"]["enum"]), common.SOURCE_TYPES)
        self.assertEqual(set(properties["distillation_method"]["enum"]), set(common.DISTILLATION_METHODS))
        self.assertEqual(properties["lifecycle_status"]["enum"], ["draft", "approved", "deprecated"])

        bridge = root / "examlex" / "scripts" / "__init__.py"
        self.assertIn("skills.examlex", bridge.read_text(encoding="utf-8"))
        mirrored = [
            path
            for path in (root / "examlex" / "scripts").rglob("*.py")
            if path.name != "__init__.py"
        ]
        self.assertEqual([], mirrored)

    @staticmethod
    def _temporary_dir():
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()
