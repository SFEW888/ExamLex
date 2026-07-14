import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENGLISH_REFERENCE = (
    PROJECT_ROOT
    / "skills"
    / "examlex"
    / "references"
    / "answer-explanation-standard.md"
)
PACKAGED_ENGLISH_REFERENCE = (
    PROJECT_ROOT
    / "examlex"
    / "references"
    / "answer-explanation-standard.md"
)
CHINESE_REFERENCE = (
    PROJECT_ROOT
    / "zh-CN"
    / "skill"
    / "references"
    / "answer-explanation-standard.md"
)


def reference_texts():
    return (
        ENGLISH_REFERENCE.read_text(encoding="utf-8"),
        CHINESE_REFERENCE.read_text(encoding="utf-8"),
    )


class AnswerExplanationStandardTests(unittest.TestCase):
    def test_main_skills_and_workflows_route_to_the_standard(self):
        paths = (
            PROJECT_ROOT / "README.md",
            PROJECT_ROOT / "zh-CN" / "README.md",
            PROJECT_ROOT / "skills" / "examlex" / "SKILL.md",
            PROJECT_ROOT / "zh-CN" / "skill" / "SKILL.md",
            PROJECT_ROOT / "skills" / "examlex" / "references" / "workflow.md",
            PROJECT_ROOT / "zh-CN" / "skill" / "references" / "workflow.md",
        )

        for path in paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn("answer-explanation-standard.md", text)
                self.assertIn("detailed", text)

    def test_default_is_detailed_for_every_learner(self):
        english, chinese = reference_texts()

        self.assertIn("`detailed` is the default for every learner", english)
        self.assertIn("所有学习者和所有完整模拟卷一律默认使用 `detailed`", chinese)
        for text in (english, chinese):
            for level in ("基础偏弱", "中等基础", "基础较好"):
                with self.subTest(level=level):
                    self.assertIn(level, text)

    def test_all_supported_exams_and_modules_are_covered(self):
        exams = ("CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8")
        modules = (
            "vocabulary",
            "listening",
            "reading",
            "translation",
            "writing",
            "cloze",
            "language-knowledge",
            "proofreading",
            "dictation",
        )

        for text in reference_texts():
            for marker in (*exams, *modules):
                with self.subTest(marker=marker):
                    self.assertIn(marker, text)

    def test_objective_and_constructed_response_fields_are_mandatory(self):
        objective_fields = (
            "answer_key",
            "tested_skill",
            "question_translation",
            "option_translation",
            "evidence_anchor",
            "evidence_scope",
            "evidence_translation",
            "reasoning_steps",
            "paraphrase_map",
            "key_language",
            "distractor_analysis",
            "error_tag",
            "learner_retry",
        )
        constructed_fields = (
            "task_analysis",
            "answer_plan",
            "reference_answer",
            "reference_translation",
            "scoring_points",
            "language_notes",
            "acceptable_alternatives",
            "common_errors",
            "learner_revision",
        )

        for text in reference_texts():
            for field in (*objective_fields, *constructed_fields):
                with self.subTest(field=field):
                    self.assertIn(f"`{field}`", text)

    def test_writing_and_translation_scaffolds_cannot_be_omitted(self):
        required = (
            "idea_bank",
            "topic_vocabulary",
            "reusable_templates",
            "[TOPIC]",
            "[REASON]",
            "[EXAMPLE]",
            "[ACTION]",
            "sentence_intent_analysis",
            "clause_map",
            "keyword_deliberation",
            "translation_build",
        )

        for text in reference_texts():
            for marker in required:
                with self.subTest(marker=marker):
                    self.assertIn(f"`{marker}`" if "_" in marker else marker, text)

    def test_cet4_and_cet6_playbooks_are_explicit(self):
        required = (
            "CET4-specific-playbook",
            "CET6-specific-playbook",
            "Section A",
            "Section B",
            "Section C",
            "grammar_analysis",
            "semantic_judgment",
            "question_translation",
            "option_translation",
            "evidence_scope",
        )

        for text in reference_texts():
            for marker in required:
                with self.subTest(marker=marker):
                    self.assertIn(marker, text)

    def test_postgraduate_playbook_is_explicit(self):
        required = (
            "postgraduate-playbook-contract",
            "Use of English",
            "Reading Part A",
            "Reading Part B",
            "Reading/Translation Part C",
            "Writing Part A",
            "Part B",
            "core_vocabulary",
            "keyword_deliberation",
        )

        for text in reference_texts():
            for marker in required:
                with self.subTest(marker=marker):
                    self.assertIn(marker, text)

    def test_tem4_playbook_is_explicit(self):
        required = (
            "TEM4-specific-playbook",
            "TEM4 dictation",
            "TEM4 listening",
            "TEM4 language knowledge",
            "TEM4 cloze",
            "TEM4 reading",
            "TEM4 writing",
        )

        for text in reference_texts():
            for marker in required:
                with self.subTest(marker=marker):
                    self.assertIn(marker, text)

    def test_tem8_playbook_is_explicit(self):
        required = (
            "TEM8-specific-playbook",
            "TEM8 mini-lecture",
            "TEM8 interview listening",
            "TEM8 reading",
            "TEM8 language knowledge",
            "TEM8 bidirectional translation",
            "TEM8 proofreading",
            "TEM8 writing",
        )

        for text in reference_texts():
            for marker in required:
                with self.subTest(marker=marker):
                    self.assertIn(marker, text)

    def test_teaching_references_cannot_be_promoted_to_exam_sources(self):
        english, chinese = reference_texts()
        english_sources = (
            PROJECT_ROOT
            / "skills"
            / "examlex"
            / "references"
            / "source-collection.md"
        ).read_text(encoding="utf-8")
        chinese_sources = (
            PROJECT_ROOT
            / "zh-CN"
            / "skill"
            / "references"
            / "source-collection.md"
        ).read_text(encoding="utf-8")

        self.assertIn("`R`-level teaching-method references", english)
        self.assertIn("`R` 级教学方法参考", chinese)
        self.assertIn("teaching-method reference corpus", english_sources)
        self.assertIn("教学方法参考语料", chinese_sources)
        self.assertIn("official", english.lower())
        self.assertIn("copy", english.lower())
        self.assertIn("官方", chinese)
        self.assertIn("复制", chinese)

    def test_packaged_english_reference_is_synced(self):
        self.assertEqual(
            ENGLISH_REFERENCE.read_text(encoding="utf-8"),
            PACKAGED_ENGLISH_REFERENCE.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
