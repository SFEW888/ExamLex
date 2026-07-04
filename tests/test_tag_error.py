import json
import unittest

from skills.english_exam_ai_tutor.scripts import tag_error


class TagErrorTests(unittest.TestCase):
    def test_deterministic_keyword_mapping(self):
        cases = [
            ("writing", "missing article before noun", "WRITING_ARTICLE_OMISSION"),
            ("reading", "failed to notice synonym and paraphrase", "READING_PARAPHRASE_FAIL"),
            ("listening", "wrong number and date in dictation", "LISTENING_NUMBER_DATE_FAIL"),
            ("translation", "Chinese-style wording sounds Chinglish", "TRANSLATION_CHINESE_ENGLISH"),
        ]

        for module, text, expected in cases:
            with self.subTest(expected=expected):
                result = tag_error.tag_error(text, module)
                self.assertIn(expected, result["error_tags"])

    def test_cli_outputs_json(self):
        output = tag_error.run_cli(["--module", "reading", "--text", "synonym paraphrase"])

        self.assertEqual(json.loads(output)["error_tags"], ["READING_PARAPHRASE_FAIL"])


if __name__ == "__main__":
    unittest.main()
