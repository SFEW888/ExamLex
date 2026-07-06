"""CLI entry point: tutor commit — ratchet check + atomic write to library."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .common import load_data
from .optimizers.ratchet import StrategyRatchet
from .config import TutorConfig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Commit distilled strategies to the strategy library."
    )
    parser.add_argument("--artifacts-dir", required=True,
                        help="Session artifacts directory")
    parser.add_argument("--library", required=True,
                        help="Path to strategy-library.json")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    artifacts = Path(args.artifacts_dir)
    library_path = Path(args.library)

    # Read all artifacts
    distilled = artifacts / "distilled.json"
    validation = artifacts / "validation_report.json"
    evaluation = artifacts / "evaluation.json"

    if not distilled.exists():
        print("ERROR: distilled.json not found.", file=sys.stderr)
        return 2

    strategies = json.loads(distilled.read_text(encoding="utf-8")).get("strategies", [])
    if not strategies:
        output = {"status": "warning", "committed": 0, "message": "No strategies to commit (empty)."}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("No strategies to commit.")
        return 0

    # Read validation scores if available
    val_scores = {}
    if validation.exists():
        val_data = json.loads(validation.read_text(encoding="utf-8"))
        for r in val_data.get("results", []):
            val_scores[r["strategy_id"]] = r.get("structure_score", 0.0)

    # Read evaluation scores if available
    eval_scores = {}
    if evaluation.exists():
        eval_data = json.loads(evaluation.read_text(encoding="utf-8"))
        for s in eval_data.get("strategies", []):
            eval_scores[s["strategy_id"]] = s.get("effect_total", 0.0)

    # Load library
    library = load_data(library_path) if library_path.exists() else {"strategies": []}
    existing = {s.get("strategy_id"): s for s in library.get("strategies", [])
                if isinstance(s, dict) and s.get("strategy_id")}

    cfg = TutorConfig()
    ratchet = StrategyRatchet(
        touch_top_delta=cfg.darwin_touch_top_delta,
        max_rounds=cfg.darwin_max_rounds,
    )

    committed = []
    skipped = []

    for strategy in strategies:
        sid = strategy.get("strategy_id")
        structure = val_scores.get(sid, 0.0)
        effect = eval_scores.get(sid, 0.0)
        total_score = structure + effect

        # Set Darwin score
        strategy["darwin_score"] = total_score

        existing_strategy = existing.get(sid)
        if existing_strategy and total_score <= existing_strategy.get("darwin_score", 0.0):
            skipped.append({"strategy_id": sid, "reason": "score not improved"})
            continue

        ratchet.apply(strategy, library, existing_strategy, total_score)
        committed.append({
            "strategy_id": sid,
            "title": strategy.get("title", ""),
            "darwin_score": total_score,
            "structure_score": structure,
            "effect_score": effect,
        })

    # Atomic save
    StrategyRatchet.atomic_save(library, library_path)

    output = {
        "status": "ok",
        "committed": len(committed),
        "skipped": len(skipped),
        "library_path": str(library_path),
        "details": committed,
    }

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Committed: {len(committed)} strategies to {library_path}")
        for c in committed:
            print(f"  [+] {c['strategy_id']}: Darwin {c['darwin_score']:.1f} "
                  f"(S:{c['structure_score']:.1f} + E:{c['effect_score']:.1f})")
        for s in skipped:
            print(f"  [-] {s['strategy_id']}: {s['reason']}")

    return 0
