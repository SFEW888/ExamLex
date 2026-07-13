from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "examlex"
ERRORS_DIR = SKILL_DIR / "assets" / "data" / "common-errors"
SCHEMA_PATH = SKILL_DIR / "assets" / "schemas" / "error-pattern.schema.json"

sys.path.insert(0, str(SKILL_DIR / "scripts"))
import common


class TestCommonErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text("utf-8"))
        cls.error_files = sorted(ERRORS_DIR.glob("*.json"))

    def _load_errors(self, path: Path) -> list[dict]:
        return json.loads(path.read_text("utf-8")).get("error_patterns", [])

    def test_error_files_exist(self):
        """All 5 module error files exist."""
        expected = {
            "chinese-learner-writing-errors.json",
            "chinese-learner-translation-errors.json",
            "chinese-learner-listening-errors.json",
            "chinese-learner-reading-errors.json",
            "chinese-learner-vocabulary-errors.json",
        }
        actual = {p.name for p in self.error_files}
        self.assertEqual(expected, actual)

    def test_all_patterns_valid_schema(self):
        """All error pattern files pass schema validation."""
        props = self.schema.get("properties", {}).get("error_patterns", {})
        items = props.get("items", {}) if isinstance(props, dict) else {}
        required = items.get("required", [])

        errors = []
        for fpath in self.error_files:
            patterns = self._load_errors(fpath)
            for i, p in enumerate(patterns):
                for field in required:
                    if field not in p:
                        errors.append(f"{fpath.name}[{i}]: missing required field '{field}'")
                # Validate pattern_id format
                pid = p.get("pattern_id", "")
                if not re.match(r"^CN-[A-Z]{2}-[A-Z]+-\d{3}$", pid):
                    errors.append(f"{fpath.name}[{i}]: invalid pattern_id '{pid}'")
                # Validate frequency_in_corpus enum
                freq = p.get("frequency_in_corpus", "")
                if freq not in {"very_high", "high", "medium", "low"}:
                    errors.append(f"{fpath.name}[{i}]: invalid frequency '{freq}'")

        self.assertEqual(errors, [], "Schema validation errors:\n" + "\n".join(errors))

    def test_tags_exist_in_error_taxonomy(self):
        """All pattern tags are in ERROR_TAG_TO_ABILITY."""
        unknown = []
        for fpath in self.error_files:
            patterns = self._load_errors(fpath)
            for p in patterns:
                tag = p.get("tag", "")
                if tag not in common.ERROR_TAG_TO_ABILITY:
                    unknown.append(f"{fpath.name}: {tag}")
        self.assertEqual(unknown, [], "Unknown tags:\n" + "\n".join(unknown))

    def test_exam_types_valid(self):
        """All exam_types values are in common.EXAM_TYPES."""
        invalid = []
        for fpath in self.error_files:
            patterns = self._load_errors(fpath)
            for i, p in enumerate(patterns):
                for et in p.get("exam_types", []):
                    if et not in common.EXAM_TYPES:
                        invalid.append(f"{fpath.name}[{i}]: exam_type '{et}'")
        self.assertEqual(invalid, [], "Invalid exam types:\n" + "\n".join(invalid))

    def test_examples_have_correct_incorrect(self):
        """All typical_examples entries have correct and incorrect fields."""
        bad = []
        for fpath in self.error_files:
            patterns = self._load_errors(fpath)
            for i, p in enumerate(patterns):
                for j, ex in enumerate(p.get("typical_examples", [])):
                    if "incorrect" not in ex or "correct" not in ex:
                        bad.append(f"{fpath.name}[{i}].examples[{j}]: missing correct/incorrect")
                    if not ex.get("incorrect") or not ex.get("correct"):
                        bad.append(f"{fpath.name}[{i}].examples[{j}]: empty correct/incorrect")
        self.assertEqual(bad, [], "Example issues:\n" + "\n".join(bad))

    def test_related_tags_exist(self):
        """All related_tags reference valid error tags."""
        unknown = []
        for fpath in self.error_files:
            patterns = self._load_errors(fpath)
            for i, p in enumerate(patterns):
                for rt in p.get("related_tags", []):
                    if rt not in common.ERROR_TAG_TO_ABILITY:
                        unknown.append(f"{fpath.name}[{i}]: related_tag '{rt}'")
        self.assertEqual(unknown, [], "Unknown related tags:\n" + "\n".join(unknown))

    def test_non_empty_collection(self):
        """Each error file contains at least 1 pattern."""
        for fpath in self.error_files:
            patterns = self._load_errors(fpath)
            self.assertGreater(len(patterns), 0,
                               f"{fpath.name} should have at least 1 error pattern")


if __name__ == "__main__":
    unittest.main()
