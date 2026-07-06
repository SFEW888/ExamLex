#!/usr/bin/env python3
"""Vocabulary size estimation via Yes/No sampling method.

Usage:
  # Batch mode: process a pre-annotated wordlist
  python estimate_vocabulary.py --wordlist answers.json --output result.json

  # Interactive mode: agent quizzes the learner one word at a time
  python estimate_vocabulary.py --interactive --output result.json
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]

try:
    from .vocab_generator import write_json
except ImportError:
    from vocab_generator import write_json  # type: ignore[no-redef]


# Default built-in test words path
_DEFAULT_REF = (
    Path(__file__).resolve().parents[1]
    / "assets" / "data" / "vocab-test-words.json"
)


def get_band_size(band_label: str) -> int:
    """Parse band label like '1-1000' or '5000+' to get the band size."""
    band_label = band_label.strip()
    if band_label.endswith("+"):
        # "5000+" maps to 1000 (same as other bands)
        return 1000
    parts = band_label.split("-")
    if len(parts) == 2:
        try:
            low = int(parts[0].strip())
            high = int(parts[1].strip())
            return high - low + 1
        except ValueError:
            return 0
    return 0


def estimate(bands_data: dict, answers: list[dict], learner_id: str = "") -> dict[str, Any]:
    """Estimate vocabulary size using Yes/No test correction formula.

    adjusted_rate = (H - FA) / (1 - FA)
    where H  = claimed_known / tested_real
          FA = claimed_false_known / tested_nonword
    """
    bands = bands_data.get("bands", bands_data)
    total_estimated = 0
    total_false_alarms = 0
    total_nonword_tests = 0
    band_results: dict[str, dict[str, Any]] = {}

    for band_label in sorted(bands.keys()):
        band = bands[band_label]
        real_words_set = set(band.get("real_words", []))
        non_words_set = set(band.get("non_words", []))

        real_answers = [
            a for a in answers
            if a.get("band") == band_label and a.get("word", "") in real_words_set
        ]
        fake_answers = [
            a for a in answers
            if a.get("band") == band_label and a.get("word", "") in non_words_set
        ]

        tested_real = len(real_answers)
        claimed_real = sum(1 for a in real_answers if a.get("known"))
        tested_fake = len(fake_answers)
        claimed_fake = sum(1 for a in fake_answers if a.get("known"))

        if tested_real == 0:
            continue

        H = claimed_real / tested_real
        FA = claimed_fake / tested_fake if tested_fake > 0 else 0.0

        if FA < 1.0:
            adjusted = max(0.0, (H - FA) / (1.0 - FA))
        else:
            adjusted = 0.0

        band_size = get_band_size(band_label)
        estimated_band = round(adjusted * band_size)

        total_estimated += estimated_band
        total_false_alarms += claimed_fake
        total_nonword_tests += tested_fake

        band_results[band_label] = {
            "tested": tested_real,
            "claimed": claimed_real,
            "hit_rate": round(H, 3),
            "false_alarm_rate": round(FA, 3),
            "adjusted_rate": round(adjusted, 3),
            "estimated": estimated_band,
        }

    # 95% confidence interval (Wald method approximation)
    overall_adjusted = total_estimated / sum(get_band_size(b) for b in band_results) if band_results else 0
    se = math.sqrt(total_estimated * (1 - overall_adjusted)) if overall_adjusted > 0 else 0
    ci_low = max(0, round(total_estimated - 1.96 * se))
    ci_high = round(total_estimated + 1.96 * se)

    overall_fa = total_false_alarms / total_nonword_tests if total_nonword_tests > 0 else 0.0

    return {
        "learner_id": learner_id or answers[0].get("learner_id", "") if answers else "",
        "test_date": datetime.date.today().isoformat(),
        "method": "yes-no-sampling",
        "estimated_vocabulary": total_estimated,
        "confidence_interval": [ci_low, ci_high],
        "false_alarm_rate": round(overall_fa, 3),
        "by_band": band_results,
    }


def suggest_foundation(estimated_vocab: int) -> str:
    """Suggest foundation level based on estimated vocabulary size."""
    if estimated_vocab < 2000:
        return "基础偏弱"
    elif estimated_vocab < 4000:
        return "中等基础"
    else:
        return "基础较好"


def generate_interactive_quiz(
    bands_data: dict,
    bands: list[str] | None = None,
    samples_per_band: int = 10,
    nonwords_per_band: int = 2,
) -> list[dict[str, Any]]:
    """Generate a quiz word list for interactive mode.

    Returns a list of word prompts that an agent can present to the learner.
    """
    all_bands = bands_data.get("bands", bands_data)
    quiz: list[dict[str, Any]] = []
    target_bands = bands if bands else sorted(all_bands.keys())

    for band_label in target_bands:
        if band_label not in all_bands:
            continue
        band = all_bands[band_label]
        real_words = band.get("real_words", [])
        non_words = band.get("non_words", [])

        # Select real words (random-ish by index)
        selected_real = real_words[:samples_per_band] if len(real_words) >= samples_per_band else real_words
        selected_fake = non_words[:nonwords_per_band] if len(non_words) >= nonwords_per_band else non_words

        for w in selected_real:
            quiz.append({"word": w, "band": band_label, "is_real": True, "known": None})
        for w in selected_fake:
            quiz.append({"word": w, "band": band_label, "is_real": False, "known": None})

    return quiz


def load_reference(path: str | None = None) -> dict:
    if path:
        ref_path = Path(path)
    else:
        ref_path = _DEFAULT_REF
    return json.loads(ref_path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate vocabulary size via Yes/No sampling.")
    parser.add_argument("--wordlist", help="Path to pre-annotated answer JSON (batch mode).")
    parser.add_argument("--interactive", action="store_true",
                        help="Generate interactive quiz words (print JSON to stdout).")
    parser.add_argument("--bands", help="Comma-separated band labels (e.g. '1-1000,1001-2000').")
    parser.add_argument("--samples-per-band", type=int, default=10,
                        help="Real words per band in interactive mode (default: 10).")
    parser.add_argument("--nonwords-per-band", type=int, default=2,
                        help="Non-words per band in interactive mode (default: 2).")
    parser.add_argument("--output", help="Path to write result JSON.")
    parser.add_argument("--reference", help="Path to test word reference file.")
    args = parser.parse_args(argv)

    reference = load_reference(args.reference)

    if args.interactive:
        band_list = args.bands.split(",") if args.bands else None
        quiz = generate_interactive_quiz(
            reference, band_list, args.samples_per_band, args.nonwords_per_band
        )
        result: dict[str, Any] = {
            "learner_id": "",
            "quiz_words": quiz,
            "instruction": (
                "Present each word to the learner and ask: 你认识这个词吗？ [y/n]. "
                "Collect answers and pass the completed wordlist to --wordlist for scoring."
            ),
        }
    elif args.wordlist:
        data = common.load_data(args.wordlist)
        answers = data.get("answers", [])
        learner_id = data.get("learner_id", "")
        result = estimate(reference, answers, learner_id)
    else:
        print("Either --wordlist or --interactive is required.", file=sys.stderr)
        return 1

    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
