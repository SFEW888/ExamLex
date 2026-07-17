from __future__ import annotations

import unittest

from examlex.scripts import validate_exam_artifact


class ExamArtifactContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = validate_exam_artifact.load_profiles()

    def test_all_five_exam_profiles_are_machine_executable(self):
        self.assertEqual(
            {"CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8"},
            set(self.profiles),
        )
        for exam_type in sorted(self.profiles):
            paper = build_paper(exam_type, self.profiles[exam_type])
            self.assertEqual([], validate_exam_artifact.validate_paper(paper, self.profiles))

    def test_paper_rejects_official_claim_and_missing_source_coverage(self):
        paper = build_paper("CET4", self.profiles["CET4"])
        paper["official_status"] = "official"
        paper["source_notes"].pop()
        errors = validate_exam_artifact.validate_paper(paper, self.profiles)
        self.assertTrue(any("official_status" in error for error in errors))
        self.assertTrue(any("do not cover" in error for error in errors))

    def test_answerbook_requires_all_option_translations_and_distractor_rejections(self):
        paper = build_paper("CET4", self.profiles["CET4"])
        answerbook = build_answerbook(paper)
        errors = validate_exam_artifact.validate_answerbook(
            answerbook, self.profiles, paper=paper
        )
        self.assertEqual([], errors)

        answerbook["answers"][0]["option_translations"].pop("D")
        answerbook["answers"][1]["distractor_analysis"].pop()
        errors = validate_exam_artifact.validate_answerbook(
            answerbook, self.profiles, paper=paper
        )
        self.assertTrue(any("translate every option" in error for error in errors))
        self.assertTrue(any("reject each wrong option" in error for error in errors))

    def test_paper_questions_tolerates_null_sections_and_questions(self):
        # A user-supplied paper may carry null (or non-list) sections/questions;
        # the validator must index what it can rather than crash on the artifact
        # it exists to check.
        self.assertEqual({}, validate_exam_artifact._paper_questions({"sections": None}))
        self.assertEqual(
            {},
            validate_exam_artifact._paper_questions(
                {"sections": [{"questions": None}, "not-a-section"]}
            ),
        )
        self.assertEqual(
            {5: {"number": 5}},
            validate_exam_artifact._paper_questions(
                {"sections": [{"questions": [{"number": 5}, "skip", {"no": "number"}]}]}
            ),
        )

    def test_answerbook_requires_detailed_writing_and_translation_packages(self):
        paper = build_paper("CET4", self.profiles["CET4"])
        answerbook = build_answerbook(paper)
        del answerbook["section_packages"]["writing"]["model_translation"]
        answerbook["section_packages"]["translation"]["sentence_units"][0].pop(
            "keyword_deliberation"
        )
        errors = validate_exam_artifact.validate_answerbook(
            answerbook, self.profiles, paper=paper
        )
        self.assertTrue(any("model_translation" in error for error in errors))
        self.assertTrue(any("keyword_deliberation" in error for error in errors))


def build_paper(exam_type: str, profile: dict) -> dict:
    sections = []
    number = 1
    objective_left = profile["objective_item_count"]
    for section_id, count in profile["required_sections"].items():
        questions = []
        for _ in range(count):
            objective = objective_left > 0 and section_id not in {
                "writing",
                "translation",
                "writing-part-a",
                "writing-part-b",
                "dictation",
            }
            question = {
                "number": number,
                "stem": f"Question {number}",
                "objective": objective,
                "item_type": "multiple_choice" if objective else "constructed_response",
            }
            if objective:
                question["options"] = {letter: f"Option {letter}" for letter in "ABCD"}
                objective_left -= 1
            questions.append(question)
            number += 1
        sections.append({"section_id": section_id, "title": section_id, "questions": questions})
    return {
        "schema_version": 1,
        "artifact_type": "exam_paper",
        "paper_id": f"{exam_type}-TEST-01",
        "exam_type": exam_type,
        "title": f"{exam_type} original simulation",
        "official_status": "simulation_not_official",
        "sections": sections,
        "source_notes": [
            {
                "section_id": section["section_id"],
                "source_name": "Project-authored training material",
                "evidence_level": "S",
                "role": "structure constraint and original content",
                "usage_mode": "original",
                "official_claim": False,
            }
            for section in sections
        ],
    }


def build_answerbook(paper: dict) -> dict:
    answers = []
    for section in paper["sections"]:
        for question in section["questions"]:
            if not question["objective"]:
                continue
            answers.append(
                {
                    "number": question["number"],
                    "answer": "A",
                    "question_translation": "题干翻译",
                    "option_translations": {letter: f"选项{letter}翻译" for letter in "ABCD"},
                    "evidence_location": "第1段第1句",
                    "evidence_scope": "current-sentence",
                    "evidence_text": "Decisive evidence.",
                    "evidence_translation": "决定性证据。",
                    "reasoning_steps": ["定位题干关键词", "核对同义替换", "验证答案与语境"],
                    "distractor_analysis": [
                        {"option": letter, "reason": f"{letter}与证据不符"}
                        for letter in "BCD"
                    ],
                }
            )
    sentence_unit = {
        "source_sentence": "原句。",
        "sentence_intent": "说明客观变化。",
        "clause_map": ["主句", "状语"],
        "keyword_deliberation": [{"source": "变化", "choice": "change", "reason": "语域准确"}],
        "literal_skeleton": "The change ...",
        "polished_translation": "The change has continued.",
        "acceptable_alternatives": ["This change has persisted."],
        "scoring_points": ["时态", "搭配"],
        "common_errors": ["漏译", "时态错误"],
    }
    comprehension = {
        "full_text": "Complete text.",
        "full_translation": "全文翻译。",
        "core_vocabulary": [{"word": "complete", "meaning": "完整的"}],
        "item_analysis": [
            {
                "number": answer["number"],
                "location": "第1段第1句",
                "evidence_scope": "current-sentence",
                "analysis": "由定位句直接得出。",
            }
            for answer in answers
        ],
    }
    section_a = {
        "option_classification": [{"option": "A", "part_of_speech": "noun", "meaning": "含义"}],
        "completed_text": "Completed passage.",
        "full_translation": "全文翻译。",
        "core_vocabulary": [{"word": "passage", "meaning": "文章"}],
        "item_analysis": [
            {
                "number": 1,
                "grammar_analysis": "空格需要名词。",
                "semantic_judgment": "语义与上下文一致。",
            }
        ],
    }
    writing = {
        "genre_analysis": "议论文，要求明确表态并论证。",
        "prompt_focus": "围绕题目限定话题回应全部任务。",
        "viewpoints": ["个人影响", "学校措施", "社会条件"],
        "paragraph_plan": ["引言表态", "主体论证", "结论建议"],
        "model_text": "A complete original model text.",
        "model_translation": "完整原创范文译文。",
        "topic_vocabulary": {"common": ["benefit"], "advanced": ["long-term implication"]},
        "reusable_templates": [
            {"text": "With the development of [TOPIC]...", "replaceable_slots": ["TOPIC"]}
        ],
        "scoring_rubric": {"task": 25, "structure": 25, "accuracy": 25, "richness": 25},
    }
    packages = {}
    for section in paper["sections"]:
        section_id = section["section_id"]
        if section_id.startswith("writing") or section_id == "writing":
            packages[section_id] = writing
        elif section_id == "translation":
            packages[section_id] = {"sentence_units": [sentence_unit]}
        elif section_id in {"reading-section-a", "cloze", "use-of-english"}:
            packages[section_id] = section_a
        elif "reading" in section_id or section_id == "listening":
            packages[section_id] = comprehension
    return {
        "schema_version": 1,
        "artifact_type": "answerbook",
        "paper_id": paper["paper_id"],
        "exam_type": paper["exam_type"],
        "detail_level": "detailed",
        "official_status": "simulation_not_official",
        "answers": answers,
        "section_packages": packages,
    }


if __name__ == "__main__":
    unittest.main()
