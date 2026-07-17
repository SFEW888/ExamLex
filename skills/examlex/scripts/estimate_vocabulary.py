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
import random
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
        # "5000+" is an open-ended top band; use a larger default so advanced
        # learners are not capped by the same 1000-word span as bounded bands.
        return 5000
    parts = band_label.split("-")
    if len(parts) == 2:
        try:
            low = int(parts[0].strip())
            high = int(parts[1].strip())
            if low > high:
                raise ValueError(
                    f"Invalid band label '{band_label}': low ({low}) > high ({high})"
                )
            return high - low + 1
        except ValueError:
            raise ValueError(
                f"Unrecognized band label '{band_label}': "
                f"expected format like '1-1000' or '5000+'"
            ) from None
    raise ValueError(
        f"Unrecognized band label '{band_label}': "
        f"expected format like '1-1000' or '5000+'"
    )


def estimate(bands_data: dict, answers: list[dict], learner_id: str = "") -> dict[str, Any]:
    """Estimate vocabulary size using Yes/No test correction formula.

    adjusted_rate = (H - FA) / (1 - FA)
    where H  = claimed_known / tested_real
          FA = claimed_false_known / tested_nonword
    """
    # A malformed reference (bands_data or its "bands" is not an object, or an
    # individual band is not an object) must yield an empty estimate, not crash.
    bands = bands_data.get("bands", bands_data) if isinstance(bands_data, dict) else {}
    if not isinstance(bands, dict):
        bands = {}
    # Drop non-dict answer rows so the .get() calls below cannot raise on a
    # malformed --wordlist (e.g. [42] or a scalar entry).
    answers = [a for a in answers if isinstance(a, dict)] if isinstance(answers, list) else []
    total_estimated = 0
    total_false_alarms = 0
    total_nonword_tests = 0
    band_results: dict[str, dict[str, Any]] = {}

    for band_label in sorted(bands.keys()):
        band = bands[band_label]
        if not isinstance(band, dict):
            continue
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

    # 95% confidence interval (Wald approximation). The total estimate is a sum
    # of independent per-band count estimates, so its variance is the sum of the
    # per-band variances: Var(band_size * adjusted) ≈ band_size² * adjusted *
    # (1 - adjusted) / tested_real.
    # TODO: Use the delta method for proper variance estimation: adj = (H-FA)/(1-FA)
    # is a ratio of two binomial proportions; the current simplification ignores
    # the uncertainty contributed by FA, yielding systematically narrow CI when FA>0.
    # See: Var(adj) ≈ (1/(1-FA)²)²·H(1-H)/n_real + ((H-1)/(1-FA)²)²·FA(1-FA)/n_fake
    total_var = 0.0
    for band_label, br in band_results.items():
        band_size = get_band_size(band_label)
        adj = br["adjusted_rate"]
        n = br["tested"]
        if n > 0 and adj > 0:
            total_var += (band_size ** 2) * adj * (1 - adj) / n
    se = math.sqrt(total_var)
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
    # A malformed reference (bands_data or its "bands" is not an object) yields
    # an empty quiz rather than crashing on .keys()/membership below.
    all_bands = bands_data.get("bands", bands_data) if isinstance(bands_data, dict) else {}
    if not isinstance(all_bands, dict):
        all_bands = {}
    quiz: list[dict[str, Any]] = []
    target_bands = bands if bands else sorted(all_bands.keys())

    for band_label in target_bands:
        if band_label not in all_bands:
            print(f"Warning: band '{band_label}' not found in reference data, skipping.", file=sys.stderr)
            continue
        band = all_bands[band_label]
        if not isinstance(band, dict):
            print(f"Warning: band '{band_label}' is malformed, skipping.", file=sys.stderr)
            continue
        real_words = band.get("real_words", [])
        non_words = band.get("non_words", [])
        if not isinstance(real_words, list):
            real_words = []
        if not isinstance(non_words, list):
            non_words = []

        # Randomly sample to avoid systematic bias from a frequency/difficulty
        # ordering in the reference file.
        selected_real = random.sample(real_words, min(samples_per_band, len(real_words)))
        selected_fake = random.sample(non_words, min(nonwords_per_band, len(non_words)))

        band_items = [
            {"word": w, "band": band_label, "is_real": True, "known": None}
            for w in selected_real
        ] + [
            {"word": w, "band": band_label, "is_real": False, "known": None}
            for w in selected_fake
        ]
        # Interleave real and fake words so the learner cannot infer answers
        # from an ordering cue (all real words followed by all fake words).
        random.shuffle(band_items)
        quiz.extend(band_items)

    return quiz


def load_reference(path: str | None = None) -> dict:
    if path:
        ref_path = Path(path)
    else:
        ref_path = _DEFAULT_REF
    try:
        reference = json.loads(ref_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Reference file not found: {ref_path}", file=sys.stderr)
        raise SystemExit(1)
    except (json.JSONDecodeError, PermissionError) as exc:
        print(f"Failed to load reference file {ref_path}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(reference, dict):
        print(f"Reference file {ref_path} must contain a JSON object.", file=sys.stderr)
        raise SystemExit(1)
    return reference


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

    if args.samples_per_band <= 0:
        print("error: --samples-per-band must be positive", file=sys.stderr)
        return 1
    if args.nonwords_per_band < 0:
        print("error: --nonwords-per-band must be non-negative", file=sys.stderr)
        return 1

    reference = load_reference(args.reference)

    if args.interactive:
        band_list = [b.strip() for b in args.bands.split(",")] if args.bands else None
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
        try:
            data = common.load_data(args.wordlist)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError) as exc:
            print(f"error: failed to load wordlist: {exc}", file=sys.stderr)
            return 1
        if not isinstance(data, dict):
            print("error: wordlist must be a JSON object", file=sys.stderr)
            return 1
        answers = data.get("answers", [])
        learner_id = data.get("learner_id", "")
        result = estimate(reference, answers, learner_id)
    else:
        print("Either --wordlist or --interactive is required.", file=sys.stderr)
        return 1

    if args.output:
        write_json(result, args.output)
    else:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
