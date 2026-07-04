import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from skills.english_exam_ai_tutor.scripts import manage_writing_versions


class ManageWritingVersionsTests(unittest.TestCase):
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
