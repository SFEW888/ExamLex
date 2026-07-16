from __future__ import annotations

import unittest

from examlex.scripts import vocabulary_block


class VocabularyBlockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = {
            "sequence": 8,
            "headword": "transform",
            "phonetics": "/trænsˈfɔːm/",
            "heat_level": 2,
            "senses": [
                {"part_of_speech": "v.", "meanings": ["使改变", "使转化"]},
                {"part_of_speech": "n.", "meanings": ["变换形式"]},
            ],
            "memory": {
                "type": "root-affix",
                "breakdown": "trans-（越过、转变）+ form（形态）",
                "explanation": "形态发生跨越式改变，因此表示转化。",
            },
            "example": {
                "sentence": "Small habits can transform the way students learn.",
                "translation": "小习惯可以改变学生的学习方式。",
                "exam_context": "教育与个人成长",
            },
            "word_family": [
                {
                    "word": "transformation",
                    "phonetics": "/ˌtrænsfəˈmeɪʃn/",
                    "part_of_speech": "n.",
                    "meanings": ["转变", "转型"],
                }
            ],
        }

    def test_renders_every_required_memorization_section(self):
        rendered = vocabulary_block.render_vocabulary_block(self.data)
        for marker in ("词义", "记忆与构词", "语境例句", "派生与词族", "主动回忆"):
            self.assertIn(marker, rendered)
        self.assertIn("/trænsˈfɔːm/", rendered)
        self.assertIn("小习惯可以改变学生的学习方式", rendered)

    def test_rejects_missing_translation_and_word_family(self):
        del self.data["example"]["translation"]
        self.data["word_family"] = []
        errors = vocabulary_block.validate_vocabulary_block(self.data)
        self.assertTrue(any("example.translation" in error for error in errors))
        self.assertTrue(any("word_family" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
