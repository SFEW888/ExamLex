from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


DIMENSIONS = ("task_completion", "structure_logic", "language_accuracy", "expression_richness")
MAX_DIMENSION_SCORE = 25
MAX_SCORE = MAX_DIMENSION_SCORE * len(DIMENSIONS)
# NOTE: "first"/"second"/"third" are counted as connectors but may appear as
# ordinals ("the first reason"), which can inflate connector_count.
CONNECTORS = {
    "first",
    "second",
    "third",
    "however",
    "therefore",
    "moreover",
    "besides",
    "because",
    "although",
    "finally",
    "in conclusion",
    "as a result",
}
GRAMMAR_RISK_PATTERNS = (
    # WARNING: also matches correct subjunctive ("I suggest that he go…").
    # "I go" is correct; only third-person "he/she go" misses the -s.
    r"\b(he|she)\s+go\b",
    # NOTE: may false-match "does it have", "will it have", etc.
    r"\bit\s+have\b",
    r"\bpeople\s+is\b",
    r"\bstudents\s+is\b",
    # WARNING: these article patterns match letters, not sounds, so they yield
    # false positives ("a European", "a university", "an hour", "an MBA").
    r"\ba\s+[aeiouAEIOU]",
    r"\ban\s+[^aeiouAEIOU\W]",
)
TARGET_WORD_RANGES = {
    "CET4": (100, 180),
    "CET6": (140, 220),
    "POSTGRADUATE_ENGLISH": (160, 260),
    "TEM4": (150, 200),
    "TEM8": (200, 300),
}


def score_writing(text: str, exam_type: str) -> dict[str, Any]:
    if exam_type not in common.EXAM_TYPES:
        raise ValueError(f"unknown exam type: {exam_type}")
    if exam_type not in TARGET_WORD_RANGES:
        raise ValueError(f"no word range defined for exam type: {exam_type}")
    words = _words(text)
    word_count = len(words)
    if word_count == 0:
        return {
            "label": "rubric_estimate",
            "exam_type": exam_type,
            "total_score": 0,
            "max_score": MAX_SCORE,
            "normalized_score": 0.0,
            "signals": {
                "word_count": 0,
                "paragraph_count": 0,
                "connector_count": 0,
                "grammar_risk_count": 0,
                "vocabulary_variety_ratio": 0.0,
            },
            "dimensions": {
                dimension: _dimension(0, "no scorable text was provided")
                for dimension in DIMENSIONS
            },
        }
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    connector_count = _connector_count(text)
    grammar_risks = _grammar_risk_count(text)
    unique_ratio = len({word.lower() for word in words}) / word_count if word_count else 0.0

    dimensions = {
        "task_completion": _task_completion(word_count, exam_type),
        "structure_logic": _structure_logic(len(paragraphs), connector_count),
        "language_accuracy": _language_accuracy(grammar_risks, word_count),
        "expression_richness": _expression_richness(unique_ratio, word_count),
    }
    total = sum(item["score"] for item in dimensions.values())
    return {
        "label": "rubric_estimate",
        "exam_type": exam_type,
        "total_score": total,
        "max_score": MAX_SCORE,
        "normalized_score": round(total / MAX_SCORE, 2),
        "signals": {
            "word_count": word_count,
            "paragraph_count": len(paragraphs),
            "connector_count": connector_count,
            "grammar_risk_count": grammar_risks,
            "vocabulary_variety_ratio": round(unique_ratio, 2),
        },
        "dimensions": dimensions,
    }


def _task_completion(word_count: int, exam_type: str) -> dict[str, Any]:
    low, high = TARGET_WORD_RANGES[exam_type]
    if low <= word_count <= high:
        score = 23
        rationale = f"word count {word_count} is inside the target range {low}-{high}"
    elif word_count >= max(1, int(low * 0.75)) and word_count <= int(high * 1.25):
        score = 18
        rationale = f"word count {word_count} is close to the target range {low}-{high}"
    elif word_count > 0:
        score = 12
        rationale = f"word count {word_count} is far from the target range {low}-{high}"
    else:
        score = 0
        rationale = "no scorable text was provided"
    return _dimension(score, rationale)


def _structure_logic(paragraph_count: int, connector_count: int) -> dict[str, Any]:
    score = 10
    if paragraph_count >= 2:
        score += 6
    if paragraph_count >= 3:
        score += 3
    score += min(connector_count, 3) * 2
    return _dimension(
        min(score, MAX_DIMENSION_SCORE),
        f"found {paragraph_count} paragraph(s) and {connector_count} explicit connector(s)",
    )


def _language_accuracy(grammar_risks: int, word_count: int) -> dict[str, Any]:
    if word_count == 0:
        return _dimension(0, "no scorable text was provided")
    score = max(8, MAX_DIMENSION_SCORE - grammar_risks * 4)
    return _dimension(score, f"detected {grammar_risks} obvious grammar risk pattern(s)")


def _expression_richness(unique_ratio: float, word_count: int) -> dict[str, Any]:
    if word_count == 0:
        return _dimension(0, "no scorable text was provided")
    if unique_ratio >= 0.65 and word_count >= 80:
        score = 23
    elif unique_ratio >= 0.50 and word_count >= 50:
        score = 18
    elif unique_ratio >= 0.35 and word_count >= 30:
        score = 14
    else:
        score = 10
    return _dimension(score, f"vocabulary variety ratio is {unique_ratio:.2f}")


def _dimension(score: int, rationale: str) -> dict[str, Any]:
    return {"score": score, "max_score": MAX_DIMENSION_SCORE, "rationale": rationale}


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", text)


def _connector_count(text: str) -> int:
    lowered = text.lower()
    return sum(1 for connector in CONNECTORS if re.search(rf"\b{re.escape(connector)}\b", lowered))


def _grammar_risk_count(text: str) -> int:
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in GRAMMAR_RISK_PATTERNS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate writing quality with a deterministic rubric.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--text-file")
    parser.add_argument("--exam-type", required=True, choices=sorted(common.EXAM_TYPES))
    parser.add_argument("--output", help="Optional output path. Defaults to stdout.")
    args = parser.parse_args(argv)

    try:
        text = Path(args.text_file).read_text(encoding="utf-8") if args.text_file else args.text
        result = score_writing(text, args.exam_type)
    except (FileNotFoundError, ValueError, KeyError, TypeError, PermissionError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        common.save_data(output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
