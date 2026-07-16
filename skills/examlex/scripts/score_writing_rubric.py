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
    "on the one hand",
    "on the other hand",
}
TARGET_WORD_RANGES = {
    "CET4": (100, 180),
    "CET6": (140, 220),
    "POSTGRADUATE_ENGLISH": (160, 260),
    "TEM4": (150, 250),
    "TEM8": (250, 450),
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "he", "in", "is", "it", "its", "of", "on", "or", "she", "that", "the", "their",
    "they", "this", "to", "was", "we", "were", "will", "with", "you",
}
SUBJUNCTIVE_TRIGGERS = re.compile(
    r"\b(?:suggest|recommend|insist|demand|request|require|propose|essential|important)\b[^.?!]{0,45}\bthat\s*$",
    re.IGNORECASE,
)
GRAMMAR_RULES = (
    ("subject_verb_people_is", re.compile(r"\bpeople\s+is\b", re.IGNORECASE)),
    ("subject_verb_students_is", re.compile(r"\bstudents\s+is\b", re.IGNORECASE)),
    ("third_person_go", re.compile(r"\b(?:he|she)\s+go\b", re.IGNORECASE)),
    ("it_have", re.compile(r"\bit\s+have\b", re.IGNORECASE)),
    ("preposition_base_verb", re.compile(r"\binstead\s+of\s+(?:study|play|work|learn)\b", re.IGNORECASE)),
)


def default_reference_samples() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "data" / "sample-essays"


def score_writing(
    text: str,
    exam_type: str,
    *,
    prompt: str | None = None,
    reference_samples: str | Path | None = None,
) -> dict[str, Any]:
    if exam_type not in common.EXAM_TYPES:
        raise ValueError(f"unknown exam type: {exam_type}")
    if exam_type not in TARGET_WORD_RANGES:
        raise ValueError(f"no word range defined for exam type: {exam_type}")
    words = _words(text)
    word_count = len(words)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    connector_count = _connector_count(text)
    grammar_risks = _grammar_risks(text)
    content_words = [word.casefold() for word in words if word.casefold() not in STOPWORDS]
    unique_ratio = len(set(content_words)) / len(content_words) if content_words else 0.0
    prompt_coverage = _prompt_coverage(words, prompt)
    anchors = load_reference_samples(reference_samples or default_reference_samples(), exam_type)
    anchor_summary = _nearest_anchor(
        anchors,
        word_count=word_count,
        paragraph_count=len(paragraphs),
        connector_count=connector_count,
        unique_ratio=unique_ratio,
    )

    if word_count == 0:
        dimensions = {
            dimension: _dimension(0, "no scorable text was provided") for dimension in DIMENSIONS
        }
    else:
        dimensions = {
            "task_completion": _task_completion(word_count, exam_type, prompt_coverage),
            "structure_logic": _structure_logic(len(paragraphs), connector_count),
            "language_accuracy": _language_accuracy(grammar_risks, word_count),
            "expression_richness": _expression_richness(unique_ratio, word_count),
        }
    raw_total = sum(item["score"] for item in dimensions.values())
    calibrated_total = _calibrate_total(raw_total, anchor_summary)
    return {
        "label": "training_rubric_estimate_not_official",
        "exam_type": exam_type,
        "total_score": calibrated_total,
        "raw_heuristic_score": raw_total,
        "max_score": MAX_SCORE,
        "normalized_score": round(calibrated_total / MAX_SCORE, 2),
        "calibration_status": "anchored" if anchor_summary else "unanchored_limited_estimate",
        "limitations": [
            "This is a deterministic training estimate, not an official score.",
            "Automated signals cannot replace a qualified human review of ideas, register, and accuracy.",
        ],
        "signals": {
            "word_count": word_count,
            "paragraph_count": len(paragraphs),
            "connector_count": connector_count,
            "grammar_risk_count": len(grammar_risks),
            "grammar_risks": grammar_risks,
            "content_vocabulary_variety_ratio": round(unique_ratio, 2),
            "prompt_keyword_coverage": prompt_coverage,
        },
        "anchor_summary": anchor_summary,
        "dimensions": dimensions,
    }


def load_reference_samples(root: str | Path, exam_type: str) -> list[dict[str, Any]]:
    sample_root = Path(root)
    if not sample_root.exists():
        return []
    samples: list[dict[str, Any]] = []
    for path in sorted(sample_root.rglob("*.json")):
        if path.name == "index.json":
            continue
        try:
            sample = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(sample, dict) or sample.get("exam_type") != exam_type:
            continue
        essay = sample.get("essay_text")
        scores = sample.get("rubric_scores")
        if not isinstance(essay, str) or not isinstance(scores, dict):
            continue
        sample_words = _words(essay)
        content_words = [word.casefold() for word in sample_words if word.casefold() not in STOPWORDS]
        paragraphs = [part for part in re.split(r"\n\s*\n", essay.strip()) if part.strip()]
        maximum = scores.get("max")
        total = scores.get("total")
        if not isinstance(maximum, (int, float)) or maximum <= 0 or not isinstance(total, (int, float)):
            continue
        samples.append(
            {
                "sample_id": sample.get("sample_id"),
                "topic": sample.get("topic"),
                "band": sample.get("band"),
                "word_count": len(sample_words),
                "paragraph_count": len(paragraphs),
                "connector_count": _connector_count(essay),
                "unique_ratio": (
                    len(set(content_words)) / len(content_words) if content_words else 0.0
                ),
                "normalized_rubric": float(total) / float(maximum),
            }
        )
    return samples


def _nearest_anchor(
    anchors: list[dict[str, Any]],
    *,
    word_count: int,
    paragraph_count: int,
    connector_count: int,
    unique_ratio: float,
) -> dict[str, Any] | None:
    if not anchors or word_count == 0:
        return None
    candidates: list[tuple[float, dict[str, Any]]] = []
    for anchor in anchors:
        length_distance = abs(word_count - anchor["word_count"]) / max(word_count, anchor["word_count"], 1)
        paragraph_distance = abs(paragraph_count - anchor["paragraph_count"]) / max(paragraph_count, anchor["paragraph_count"], 1)
        connector_distance = abs(connector_count - anchor["connector_count"]) / max(connector_count, anchor["connector_count"], 1)
        lexical_distance = abs(unique_ratio - anchor["unique_ratio"])
        distance = 0.4 * length_distance + 0.2 * paragraph_distance + 0.15 * connector_distance + 0.25 * lexical_distance
        candidates.append((distance, anchor))
    distance, nearest = min(candidates, key=lambda item: item[0])
    return {
        "anchor_count": len(anchors),
        "nearest_sample_id": nearest["sample_id"],
        "nearest_topic": nearest["topic"],
        "nearest_band": nearest["band"],
        "signal_similarity": round(max(0.0, 1.0 - distance), 2),
        "anchor_normalized_rubric": round(nearest["normalized_rubric"], 2),
    }


def _calibrate_total(raw_total: int, anchor: dict[str, Any] | None) -> int:
    if not anchor:
        return raw_total
    similarity = float(anchor["signal_similarity"])
    anchor_score = float(anchor["anchor_normalized_rubric"]) * MAX_SCORE
    weight = min(0.25, max(0.10, similarity * 0.25))
    return int(round(raw_total * (1.0 - weight) + anchor_score * weight))


def _task_completion(word_count: int, exam_type: str, prompt_coverage: float | None) -> dict[str, Any]:
    low, high = TARGET_WORD_RANGES[exam_type]
    if low <= word_count <= high:
        score = 22
        rationale = f"word count {word_count} is inside the target range {low}-{high}"
    elif max(1, int(low * 0.75)) <= word_count <= int(high * 1.25):
        score = 17
        rationale = f"word count {word_count} is close to the target range {low}-{high}"
    else:
        score = 10
        rationale = f"word count {word_count} is far from the target range {low}-{high}"
    if prompt_coverage is None:
        rationale += "; no prompt was provided, so task response is only partially assessable"
    elif prompt_coverage >= 0.6:
        score = min(MAX_DIMENSION_SCORE, score + 3)
        rationale += f"; prompt keyword coverage is {prompt_coverage:.2f}"
    elif prompt_coverage < 0.3:
        score = max(0, score - 5)
        rationale += f"; prompt keyword coverage is low at {prompt_coverage:.2f}"
    return _dimension(score, rationale)


def _structure_logic(paragraph_count: int, connector_count: int) -> dict[str, Any]:
    score = 9
    if paragraph_count >= 2:
        score += 6
    if paragraph_count >= 3:
        score += 3
    score += min(connector_count, 3) * 2
    return _dimension(
        min(score, MAX_DIMENSION_SCORE),
        f"found {paragraph_count} paragraph(s) and {connector_count} distinct connector type(s)",
    )


def _language_accuracy(grammar_risks: list[dict[str, Any]], word_count: int) -> dict[str, Any]:
    if word_count == 0:
        return _dimension(0, "no scorable text was provided")
    density = len(grammar_risks) / max(word_count, 1) * 100
    score = max(7, int(round(MAX_DIMENSION_SCORE - density * 8)))
    return _dimension(score, f"detected {len(grammar_risks)} high-precision grammar risk(s), {density:.2f} per 100 words")


def _expression_richness(unique_ratio: float, word_count: int) -> dict[str, Any]:
    if word_count == 0:
        return _dimension(0, "no scorable text was provided")
    if unique_ratio >= 0.68 and word_count >= 80:
        score = 23
    elif unique_ratio >= 0.55 and word_count >= 50:
        score = 19
    elif unique_ratio >= 0.42 and word_count >= 30:
        score = 15
    else:
        score = 10
    return _dimension(score, f"content-word variety ratio is {unique_ratio:.2f}")


def _dimension(score: int, rationale: str) -> dict[str, Any]:
    return {"score": score, "max_score": MAX_DIMENSION_SCORE, "rationale": rationale}


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", text)


def _connector_count(text: str) -> int:
    lowered = text.lower()
    return sum(1 for connector in CONNECTORS if re.search(rf"\b{re.escape(connector)}\b", lowered))


def _grammar_risks(text: str) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for rule_id, pattern in GRAMMAR_RULES:
        for match in pattern.finditer(text):
            before = text[max(0, match.start() - 70):match.start()]
            if rule_id == "third_person_go" and SUBJUNCTIVE_TRIGGERS.search(before):
                continue
            if rule_id == "it_have" and re.search(r"\b(?:does|did|will|would|can|could|may|might|must|should)\s*$", before, re.IGNORECASE):
                continue
            risks.append(
                {
                    "rule_id": rule_id,
                    "text": match.group(0),
                    "character_offset": match.start(),
                }
            )
    return risks


def _grammar_risk_count(text: str) -> int:
    """Backward-compatible count helper used by older callers."""
    return len(_grammar_risks(text))


def _prompt_coverage(words: list[str], prompt: str | None) -> float | None:
    if not prompt:
        return None
    essay_terms = {word.casefold() for word in words if word.casefold() not in STOPWORDS}
    prompt_terms = {
        word.casefold() for word in _words(prompt)
        if word.casefold() not in STOPWORDS and len(word) >= 4
    }
    if not prompt_terms:
        return None
    return round(len(essay_terms & prompt_terms) / len(prompt_terms), 2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate writing quality with an anchored deterministic rubric.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--text-file")
    prompt_source = parser.add_mutually_exclusive_group()
    prompt_source.add_argument("--prompt")
    prompt_source.add_argument("--prompt-file")
    parser.add_argument("--exam-type", required=True, choices=sorted(common.EXAM_TYPES))
    parser.add_argument("--reference-samples", default=str(default_reference_samples()))
    parser.add_argument("--output", help="Optional output path. Defaults to stdout.")
    args = parser.parse_args(argv)
    try:
        text = Path(args.text_file).read_text(encoding="utf-8") if args.text_file else args.text
        prompt = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else args.prompt
        result = score_writing(
            text,
            args.exam_type,
            prompt=prompt,
            reference_samples=args.reference_samples,
        )
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
