from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXAM_TYPES = {"CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8"}
EVIDENCE_LEVELS = {"S", "A", "B", "C", "R"}
USAGE_MODES = {"original", "theme_reference", "fact_check", "compliant_adaptation", "reference_corpus"}
EVIDENCE_SCOPES = {
    "current-sentence",
    "local-context",
    "paragraph",
    "cross-paragraph",
    "whole-passage",
    "cross-turn",
}
DETAIL_FIELDS = {
    "question_translation",
    "option_translations",
    "evidence_location",
    "evidence_scope",
    "evidence_text",
    "evidence_translation",
    "reasoning_steps",
    "distractor_analysis",
}
WRITING_FIELDS = {
    "genre_analysis",
    "prompt_focus",
    "viewpoints",
    "paragraph_plan",
    "model_text",
    "model_translation",
    "topic_vocabulary",
    "reusable_templates",
    "scoring_rubric",
}
TRANSLATION_UNIT_FIELDS = {
    "source_sentence",
    "sentence_intent",
    "clause_map",
    "keyword_deliberation",
    "literal_skeleton",
    "polished_translation",
    "acceptable_alternatives",
    "scoring_points",
    "common_errors",
}


def default_profiles_path() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "data" / "exam-artifact-profiles.json"


def load_profiles(path: str | Path | None = None) -> dict[str, Any]:
    profile_path = Path(path) if path else default_profiles_path()
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    profiles = data.get("profiles") if isinstance(data, dict) else None
    if data.get("schema_version") != 1 or not isinstance(profiles, dict):
        raise ValueError("exam artifact profiles must use schema_version 1 and contain profiles")
    return profiles


def validate_paper(data: object, profiles: dict[str, Any]) -> list[str]:
    if not isinstance(data, dict):
        return ["paper must be a JSON object"]
    errors: list[str] = []
    _require_equal(data, "schema_version", 1, errors)
    _require_equal(data, "artifact_type", "exam_paper", errors)
    _require_equal(data, "official_status", "simulation_not_official", errors)
    for field in ("paper_id", "title"):
        _require_text(data, field, errors)
    exam_type = data.get("exam_type")
    if exam_type not in EXAM_TYPES or exam_type not in profiles:
        errors.append(f"unsupported exam_type: {exam_type}")
        return errors
    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("sections must be a non-empty list")
        return errors
    by_id: dict[str, dict[str, Any]] = {}
    all_numbers: list[int] = []
    objective_numbers: list[int] = []
    for index, section in enumerate(sections, 1):
        if not isinstance(section, dict):
            errors.append(f"sections[{index}] must be an object")
            continue
        section_id = section.get("section_id")
        if not isinstance(section_id, str) or not section_id:
            errors.append(f"sections[{index}] needs section_id")
            continue
        if section_id in by_id:
            errors.append(f"duplicate section_id: {section_id}")
        by_id[section_id] = section
        questions = section.get("questions")
        if not isinstance(questions, list):
            errors.append(f"section {section_id} questions must be a list")
            continue
        for question_index, question in enumerate(questions, 1):
            if not isinstance(question, dict):
                errors.append(f"section {section_id} question {question_index} must be an object")
                continue
            number = question.get("number")
            if not isinstance(number, int) or number < 1:
                errors.append(f"section {section_id} question {question_index} needs a positive number")
            else:
                all_numbers.append(number)
                if question.get("objective") is True:
                    objective_numbers.append(number)
            _require_text(question, "stem", errors, prefix=f"question {number}")
            options = question.get("options")
            if question.get("objective") is True and question.get("item_type", "multiple_choice") == "multiple_choice":
                if not isinstance(options, dict) or len(options) != 4 or set(options) != {"A", "B", "C", "D"}:
                    errors.append(f"question {number} must contain exactly A/B/C/D options")
    profile = profiles[exam_type]
    required = profile.get("required_sections", {})
    for section_id, expected_count in required.items():
        if section_id not in by_id:
            errors.append(f"missing required section: {section_id}")
            continue
        questions = by_id[section_id].get("questions", [])
        if len(questions) != expected_count:
            errors.append(
                f"section {section_id} has {len(questions)} question(s); expected {expected_count}"
            )
    if len(all_numbers) != len(set(all_numbers)):
        errors.append("question numbers must be globally unique")
    if all_numbers and sorted(all_numbers) != list(range(min(all_numbers), max(all_numbers) + 1)):
        errors.append("question numbers must be continuous")
    expected_objective = profile.get("objective_item_count")
    if isinstance(expected_objective, int) and len(objective_numbers) != expected_objective:
        errors.append(
            f"paper has {len(objective_numbers)} objective items; expected {expected_objective}"
        )
    _validate_source_notes(data.get("source_notes"), set(by_id), errors)
    return errors


def validate_answerbook(
    data: object,
    profiles: dict[str, Any],
    *,
    paper: dict[str, Any] | None = None,
) -> list[str]:
    if not isinstance(data, dict):
        return ["answerbook must be a JSON object"]
    errors: list[str] = []
    _require_equal(data, "schema_version", 1, errors)
    _require_equal(data, "artifact_type", "answerbook", errors)
    _require_equal(data, "official_status", "simulation_not_official", errors)
    _require_equal(data, "detail_level", "detailed", errors)
    _require_text(data, "paper_id", errors)
    exam_type = data.get("exam_type")
    if exam_type not in EXAM_TYPES or exam_type not in profiles:
        errors.append(f"unsupported exam_type: {exam_type}")
        return errors
    if paper is not None:
        if data.get("paper_id") != paper.get("paper_id"):
            errors.append("answerbook paper_id does not match paper")
        if exam_type != paper.get("exam_type"):
            errors.append("answerbook exam_type does not match paper")
    answers = data.get("answers")
    if not isinstance(answers, list):
        errors.append("answers must be a list")
        answers = []
    paper_questions = _paper_questions(paper) if paper else {}
    answer_numbers: list[int] = []
    for index, answer in enumerate(answers, 1):
        if not isinstance(answer, dict):
            errors.append(f"answers[{index}] must be an object")
            continue
        number = answer.get("number")
        if not isinstance(number, int):
            errors.append(f"answers[{index}] needs an integer number")
            continue
        answer_numbers.append(number)
        _require_text(answer, "answer", errors, prefix=f"answer {number}")
        question = paper_questions.get(number)
        if question and question.get("item_type", "multiple_choice") == "multiple_choice":
            _validate_multiple_choice_explanation(answer, question, errors)
    if len(answer_numbers) != len(set(answer_numbers)):
        errors.append("answer numbers must be unique")
    if paper:
        expected = sorted(
            number for number, question in paper_questions.items() if question.get("objective") is True
        )
        if sorted(answer_numbers) != expected:
            errors.append("answer key must cover every objective paper item exactly once")
    packages = data.get("section_packages")
    if not isinstance(packages, dict):
        errors.append("section_packages must be an object")
        return errors
    profile = profiles[exam_type]
    section_ids = set(profile.get("required_sections", {}))
    for section_id in section_ids:
        if section_id.startswith("writing") or section_id == "writing":
            _validate_writing_package(packages.get(section_id), section_id, errors)
        elif section_id == "translation":
            _validate_translation_package(packages.get(section_id), section_id, errors)
        elif section_id in {"reading-section-a", "cloze", "use-of-english"}:
            _validate_completed_text_package(packages.get(section_id), section_id, errors)
        elif "reading" in section_id or section_id == "listening":
            _validate_comprehension_package(packages.get(section_id), section_id, errors)
    return errors


def _validate_multiple_choice_explanation(
    answer: dict[str, Any], question: dict[str, Any], errors: list[str]
) -> None:
    number = answer.get("number")
    missing = sorted(field for field in DETAIL_FIELDS if field not in answer)
    if missing:
        errors.append(f"answer {number} missing detailed fields: {', '.join(missing)}")
        return
    translations = answer.get("option_translations")
    option_keys = set(question.get("options", {}))
    if not isinstance(translations, dict) or set(translations) != option_keys or not all(
        _text(value) for value in translations.values()
    ):
        errors.append(f"answer {number} must translate every option")
    if answer.get("evidence_scope") not in EVIDENCE_SCOPES:
        errors.append(f"answer {number} has invalid evidence_scope")
    for field in ("question_translation", "evidence_location", "evidence_text", "evidence_translation"):
        if not _text(answer.get(field)):
            errors.append(f"answer {number} {field} must be non-empty")
    steps = answer.get("reasoning_steps")
    if not isinstance(steps, list) or len([step for step in steps if _text(step)]) < 3:
        errors.append(f"answer {number} needs at least three reasoning steps")
    distractors = answer.get("distractor_analysis")
    correct = str(answer.get("answer", "")).strip()
    expected_wrong = option_keys - {correct}
    if not isinstance(distractors, list):
        errors.append(f"answer {number} needs distractor_analysis")
    else:
        mapped = {
            item.get("option"): item
            for item in distractors
            if isinstance(item, dict) and _text(item.get("reason"))
        }
        if set(mapped) != expected_wrong:
            errors.append(f"answer {number} must reject each wrong option separately")


def _validate_writing_package(package: object, section_id: str, errors: list[str]) -> None:
    if not isinstance(package, dict):
        errors.append(f"section package {section_id} must be an object")
        return
    missing = sorted(field for field in WRITING_FIELDS if field not in package)
    if missing:
        errors.append(f"writing package {section_id} missing: {', '.join(missing)}")
    viewpoints = package.get("viewpoints")
    if not isinstance(viewpoints, list) or len([item for item in viewpoints if _text(item)]) < 3:
        errors.append(f"writing package {section_id} needs at least three viewpoints")
    for field in ("genre_analysis", "prompt_focus", "model_text", "model_translation"):
        if not _text(package.get(field)):
            errors.append(f"writing package {section_id} {field} must be non-empty")
    vocabulary = package.get("topic_vocabulary")
    if not isinstance(vocabulary, dict) or not vocabulary.get("common") or not vocabulary.get("advanced"):
        errors.append(f"writing package {section_id} needs common and advanced vocabulary")
    templates = package.get("reusable_templates")
    if not isinstance(templates, list) or not any(
        isinstance(item, dict) and item.get("replaceable_slots") for item in templates
    ):
        errors.append(f"writing package {section_id} needs reusable templates with replaceable slots")


def _validate_translation_package(package: object, section_id: str, errors: list[str]) -> None:
    if not isinstance(package, dict):
        errors.append(f"section package {section_id} must be an object")
        return
    units = package.get("sentence_units")
    if not isinstance(units, list) or not units:
        errors.append(f"translation package {section_id} needs sentence_units")
        return
    for index, unit in enumerate(units, 1):
        if not isinstance(unit, dict):
            errors.append(f"translation package {section_id} unit {index} must be an object")
            continue
        missing = sorted(field for field in TRANSLATION_UNIT_FIELDS if not unit.get(field))
        if missing:
            errors.append(
                f"translation package {section_id} unit {index} missing: {', '.join(missing)}"
            )


def _validate_completed_text_package(package: object, section_id: str, errors: list[str]) -> None:
    required = {"option_classification", "completed_text", "full_translation", "core_vocabulary", "item_analysis"}
    _validate_package_fields(package, section_id, required, errors)
    if isinstance(package, dict):
        analysis = package.get("item_analysis")
        if not isinstance(analysis, list) or not all(
            isinstance(item, dict) and item.get("grammar_analysis") and item.get("semantic_judgment")
            for item in analysis
        ):
            errors.append(f"section package {section_id} needs per-item grammar and semantic analysis")


def _validate_comprehension_package(package: object, section_id: str, errors: list[str]) -> None:
    required = {"full_text", "full_translation", "core_vocabulary", "item_analysis"}
    _validate_package_fields(package, section_id, required, errors)
    if isinstance(package, dict):
        analysis = package.get("item_analysis")
        if not isinstance(analysis, list) or not all(
            isinstance(item, dict)
            and item.get("location")
            and item.get("evidence_scope") in EVIDENCE_SCOPES
            and item.get("analysis")
            for item in analysis
        ):
            errors.append(f"section package {section_id} needs location, evidence scope, and analysis per item")


def _validate_package_fields(package: object, section_id: str, required: set[str], errors: list[str]) -> None:
    if not isinstance(package, dict):
        errors.append(f"section package {section_id} must be an object")
        return
    missing = sorted(field for field in required if not package.get(field))
    if missing:
        errors.append(f"section package {section_id} missing: {', '.join(missing)}")


def _validate_source_notes(notes: object, section_ids: set[str], errors: list[str]) -> None:
    if not isinstance(notes, list) or not notes:
        errors.append("source_notes must be a non-empty list")
        return
    covered: set[str] = set()
    for index, note in enumerate(notes, 1):
        if not isinstance(note, dict):
            errors.append(f"source_notes[{index}] must be an object")
            continue
        section_id = note.get("section_id")
        if section_id not in section_ids:
            errors.append(f"source note has unknown section_id: {section_id}")
        else:
            covered.add(section_id)
        if note.get("evidence_level") not in EVIDENCE_LEVELS:
            errors.append(f"source note {section_id} has invalid evidence_level")
        if note.get("usage_mode") not in USAGE_MODES:
            errors.append(f"source note {section_id} has invalid usage_mode")
        if note.get("official_claim") is not False:
            errors.append(f"source note {section_id} must set official_claim to false")
        for field in ("source_name", "role"):
            if not _text(note.get(field)):
                errors.append(f"source note {section_id} {field} must be non-empty")
    missing = section_ids - covered
    if missing:
        errors.append(f"source notes do not cover sections: {', '.join(sorted(missing))}")


def _paper_questions(paper: dict[str, Any] | None) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    if not isinstance(paper, dict):
        return result
    for section in paper.get("sections", []):
        if not isinstance(section, dict):
            continue
        for question in section.get("questions", []):
            if isinstance(question, dict) and isinstance(question.get("number"), int):
                result[question["number"]] = question
    return result


def _require_equal(data: dict[str, Any], field: str, expected: object, errors: list[str]) -> None:
    if data.get(field) != expected:
        errors.append(f"{field} must equal {expected!r}")


def _require_text(data: dict[str, Any], field: str, errors: list[str], *, prefix: str = "artifact") -> None:
    if not _text(data.get(field)):
        errors.append(f"{prefix} {field} must be a non-empty string")


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an ExamLex paper or detailed answerbook.")
    parser.add_argument("--kind", required=True, choices=("paper", "answerbook"))
    parser.add_argument("--file", required=True)
    parser.add_argument("--paper", help="Matching paper JSON when validating an answerbook.")
    parser.add_argument("--profiles", help="Optional exam artifact profiles JSON.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        profiles = load_profiles(args.profiles)
        paper = json.loads(Path(args.paper).read_text(encoding="utf-8")) if args.paper else None
        errors = validate_paper(data, profiles) if args.kind == "paper" else validate_answerbook(data, profiles, paper=paper)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors = [str(exc)]
    report = {"ok": not errors, "kind": args.kind, "file": str(args.file), "errors": errors}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    else:
        print(f"{args.kind.capitalize()} artifact is valid.")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
