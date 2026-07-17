"""Regression tests: malformed JSON at CLI read boundaries must never crash a command.

Companion to test_malformed_input_hardening.py, covering four more read
boundaries where a structurally-wrong-but-valid-JSON input (a scalar where an
object/list is expected, a list where an object is expected, or a mixed-type
list) previously escaped as an uncaught AttributeError/TypeError instead of a
reported issue, a clean ValueError, or a non-zero return code.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from examlex.scripts import cli_validate, estimate_vocabulary, vocabulary_block
from examlex.scripts.session import SessionManager


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class CliMalformedInputHardeningTests(unittest.TestCase):
    # ---- cli_validate.py ----

    def test_validate_reports_non_list_strategies(self):
        with tempfile.TemporaryDirectory() as temp:
            artifacts = Path(temp)
            # A truthy non-iterable "strategies" reaches `for strategy in ...`.
            _write(artifacts / "distilled.json", {"strategies": 1})
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = cli_validate.main(["--artifacts-dir", str(artifacts)])
            # Same clean error path (return 2) as the non-dict document case.
            self.assertEqual(2, rc)

    def test_validate_still_handles_empty_strategy_list(self):
        with tempfile.TemporaryDirectory() as temp:
            artifacts = Path(temp)
            _write(artifacts / "distilled.json", {"strategies": []})
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = cli_validate.main(["--artifacts-dir", str(artifacts)])
            self.assertEqual(0, rc)  # warning path, not a crash

    # ---- session.py ----

    def test_resume_raises_clean_value_error_on_non_dict_state(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp, True)
        root = Path(temp) / "sessions"
        session_dir = root / "2026-01-01" / "sess1"
        session_dir.mkdir(parents=True)
        _write(session_dir / "pipeline_state.json", [1, 2, 3])  # a list, not an object
        # A non-dict state must raise ValueError (caught by resume_main's
        # handler), never an AttributeError on state.get(...).
        with self.assertRaises(ValueError):
            SessionManager(root).resume("sess1")

    # ---- estimate_vocabulary.py ----

    def test_estimate_tolerates_non_dict_bands_and_non_list_answers(self):
        self.assertIsInstance(estimate_vocabulary.estimate(None, []), dict)
        self.assertIsInstance(estimate_vocabulary.estimate({"bands": "x"}, []), dict)
        self.assertIsInstance(estimate_vocabulary.estimate({"bands": {}}, 42), dict)
        # Non-dict answer rows are dropped, not crashed on.
        self.assertIsInstance(estimate_vocabulary.estimate({"bands": {}}, [42, "x"]), dict)

    def test_generate_interactive_quiz_tolerates_malformed_reference(self):
        self.assertEqual([], estimate_vocabulary.generate_interactive_quiz(None))
        self.assertEqual([], estimate_vocabulary.generate_interactive_quiz({"bands": "x"}))

    def test_load_reference_raises_on_non_dict_file(self):
        with tempfile.TemporaryDirectory() as temp:
            ref = Path(temp) / "ref.json"
            _write(ref, ["not", "an", "object"])
            with self.assertRaises(SystemExit):
                estimate_vocabulary.load_reference(str(ref))

    def test_main_reports_non_dict_wordlist(self):
        with tempfile.TemporaryDirectory() as temp:
            wordlist = Path(temp) / "answers.json"
            _write(wordlist, [1, 2, 3])  # a list, not an object
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = estimate_vocabulary.main(["--wordlist", str(wordlist)])
            self.assertEqual(1, rc)

    # ---- vocabulary_block.py ----

    def test_validate_rejects_mixed_type_meanings(self):
        # A meanings list with a non-string member passed validation before (the
        # filter silently dropped it) and then crashed render's str.join.
        block = {
            "sequence": 1,
            "headword": "test",
            "phonetics": "/test/",
            "heat_level": 0,
            "senses": [{"part_of_speech": "n.", "meanings": ["ok", 123]}],
            "memory": {"type": "root-affix", "breakdown": "b", "explanation": "e"},
            "example": {"sentence": "s", "translation": "t"},
            "word_family": [
                {"word": "w", "phonetics": "/w/", "part_of_speech": "n.", "meanings": ["m"]}
            ],
        }
        errors = vocabulary_block.validate_vocabulary_block(block)
        self.assertTrue(any("meanings" in e for e in errors))
        # render now raises a clean ValueError instead of a TypeError on join.
        with self.assertRaises(ValueError):
            vocabulary_block.render_vocabulary_block(block)


if __name__ == "__main__":
    unittest.main()
