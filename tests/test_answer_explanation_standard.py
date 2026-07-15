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
ENGLISH_RENDERING_TEMPLATE = (
    PROJECT_ROOT
    / "skills"
    / "examlex"
    / "references"
    / "answerbook-rendering-template.md"
)
PACKAGED_RENDERING_TEMPLATE = (
    PROJECT_ROOT
    / "examlex"
    / "references"
    / "answerbook-rendering-template.md"
)
CHINESE_RENDERING_TEMPLATE = (
    PROJECT_ROOT
    / "zh-CN"
    / "skill"
    / "references"
    / "answerbook-rendering-template.md"
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

    def test_image_mapped_answerbook_contract_is_mandatory(self):
        required = (
            "image-mapped-answerbook-contract",
            "answer-check-block",
            "passage-first-contract",
            "item-locality-contract",
            "no-summary-substitution",
            "printable-bilingual-layout",
            "bilingual-item-block",
        )

        for text in reference_texts():
            for marker in required:
                with self.subTest(marker=marker):
                    self.assertIn(f"`{marker}`", text)

    def test_image_mapped_page_functions_cannot_regress(self):
        page_functions = (
            "answer-check",
            "writing-analysis",
            "model-and-translation",
            "topic-vocabulary",
            "writing-template",
            "full-script-and-translation",
            "option-classification",
            "full-text-translation",
            "core-vocabulary",
            "grammar-analysis",
            "semantic-judgment",
            "statement-translation-and-location",
            "multiple-choice-reading-analysis",
            "translation-breakdown",
            "source-and-evidence-note",
        )

        for text in reference_texts():
            for marker in page_functions:
                with self.subTest(marker=marker):
                    self.assertIn(f"`{marker}`", text)

    def test_rendering_templates_exist_and_cover_every_page_function(self):
        templates = (
            ENGLISH_RENDERING_TEMPLATE.read_text(encoding="utf-8"),
            CHINESE_RENDERING_TEMPLATE.read_text(encoding="utf-8"),
        )
        required = (
            "answer-check",
            "writing-analysis",
            "model-and-translation",
            "topic-vocabulary",
            "writing-template",
            "full-script-and-translation",
            "bilingual-item-block",
            "option-classification",
            "full-text-translation",
            "core-vocabulary",
            "grammar-analysis",
            "semantic-judgment",
            "statement-translation-and-location",
            "multiple-choice-reading-analysis",
            "translation-breakdown",
            "source-and-evidence-note",
        )

        for text in templates:
            for marker in required:
                with self.subTest(marker=marker):
                    self.assertIn(f"`{marker}`", text)

    def test_standard_and_skill_route_to_rendering_template(self):
        paths = (
            ENGLISH_REFERENCE,
            CHINESE_REFERENCE,
            PROJECT_ROOT / "skills" / "examlex" / "SKILL.md",
            PROJECT_ROOT / "zh-CN" / "skill" / "SKILL.md",
        )
        for path in paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                self.assertIn(
                    "answerbook-rendering-template.md",
                    path.read_text(encoding="utf-8"),
                )

    def test_item_explanation_must_be_local_and_not_a_summary(self):
        english, chinese = reference_texts()

        self.assertRegex(english, r"same\s+item block")
        self.assertIn("at least three explicit `reasoning_steps`", english)
        self.assertIn("every source sentence", english)
        self.assertIn("同一个题号块", chinese)
        self.assertIn("至少三步 `reasoning_steps`", chinese)
        self.assertIn("覆盖原文每一句", chinese)
        self.assertIn("不得只写“其余选项均未提及”", chinese)

    def test_skill_and_workflow_expose_the_rendering_contract(self):
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
                self.assertIn(
                    "image-mapped-answerbook-contract",
                    path.read_text(encoding="utf-8"),
                )

    def test_every_exam_playbook_inherits_the_rendering_contract(self):
        for text in reference_texts():
            with self.subTest(language="chinese" if "图片映射式" in text else "english"):
                self.assertGreaterEqual(
                    text.count("image-mapped-answerbook-contract"),
                    6,
                )

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

    def test_answerbook_format_is_not_an_evidence_source(self):
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

        self.assertIn("project-authored quality requirement", english)
        self.assertRegex(english, r"not an\s+evidence source")
        self.assertIn("项目自有的质量要求", chinese)
        self.assertIn("不是证据来源", chinese)
        self.assertIn(
            "| `R` | Translation, terminology, cultural-background, or writing reference corpus; not a direct exam source. |",
            english_sources,
        )
        self.assertIn(
            "| `R` | 翻译、术语、中国文化背景或写作参考语料，不是直接真题原文。 |",
            chinese_sources,
        )

    def test_packaged_english_reference_is_synced(self):
        self.assertEqual(
            ENGLISH_REFERENCE.read_text(encoding="utf-8"),
            PACKAGED_ENGLISH_REFERENCE.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            ENGLISH_RENDERING_TEMPLATE.read_text(encoding="utf-8"),
            PACKAGED_RENDERING_TEMPLATE.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
