import json
import re
import threading
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from examlex.scripts import manage_writing_versions


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ManageWritingVersionsTests(unittest.TestCase):
    def test_packaged_schema_accepts_runtime_generated_v5_and_later(self):
        schema = json.loads(
            (
                PROJECT_ROOT
                / "skills/examlex/assets/schemas/writing-version-record.schema.json"
            ).read_text(encoding="utf-8")
        )
        pattern = schema["properties"]["version"]["pattern"]

        self.assertIsNotNone(re.fullmatch(pattern, "V5"))
        self.assertIsNotNone(re.fullmatch(pattern, "V100"))
        self.assertIsNone(re.fullmatch(pattern, "V0"))

    def test_concurrent_cli_appends_keep_both_versions(self):
        versions_path = Path("test-artifacts") / "concurrent-writing-versions.json"
        versions_path.parent.mkdir(exist_ok=True)
        versions_path.write_text("[]\n", encoding="utf-8")
        original_load = manage_writing_versions._load_records

        def delayed_load(path):
            records = original_load(path)
            time.sleep(0.05)
            return records

        def append(writing_id):
            self.assertEqual(
                0,
                manage_writing_versions.main(
                    ["--file", str(versions_path), "--writing-id", writing_id, "--text", "draft"]
                ),
            )

        try:
            with patch.object(manage_writing_versions, "_load_records", side_effect=delayed_load):
                workers = [threading.Thread(target=append, args=(f"essay-{i}",)) for i in range(2)]
                for worker in workers:
                    worker.start()
                for worker in workers:
                    worker.join()
            saved = json.loads(versions_path.read_text(encoding="utf-8"))
            self.assertEqual({"essay-0", "essay-1"}, {item["writing_id"] for item in saved})
        finally:
            versions_path.unlink(missing_ok=True)

    def test_packaged_writing_template_is_an_appendable_store(self):
        template = json.loads(
            (
                PROJECT_ROOT
                / "skills/examlex/assets/templates/writing-version-record.yaml"
            ).read_text(encoding="utf-8")
        )

        self.assertIsInstance(template, list)

    def test_adds_next_version_for_existing_writing_id(self):
        data = [
            {
                "writing_id": "essay-1",
                "version": "V1",
                "source_version": None,
                "text": "First draft.",
                "changes": [],
            }
        ]

        updated, version = manage_writing_versions.add_writing_version(
            data,
            writing_id="essay-1",
            text="Second draft.",
            source_version="V1",
            changes=["fixed tense"],
        )

        self.assertEqual(version["version"], "V2")
        self.assertEqual(version["source_version"], "V1")
        self.assertEqual(version["changes"], ["fixed tense"])
        self.assertEqual(len(updated), 2)

    def test_cli_creates_file_and_prints_added_record(self):
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        versions_path = root / "task6-writing-versions.json"
        try:
            stdout = StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(
                    manage_writing_versions.main(
                        [
                            "--file",
                            str(versions_path),
                            "--writing-id",
                            "essay-2",
                            "--text",
                            "A concise paragraph.",
                            "--changes",
                            "initial draft",
                            "--print",
                        ]
                    ),
                    0,
                )

            saved = json.loads(versions_path.read_text(encoding="utf-8"))
            self.assertEqual(saved[0]["version"], "V1")
            self.assertEqual(saved[0]["changes"], ["initial draft"])
            self.assertEqual(json.loads(stdout.getvalue())["writing_id"], "essay-2")
        finally:
            if versions_path.exists():
                versions_path.unlink()


if __name__ == "__main__":
    unittest.main()
