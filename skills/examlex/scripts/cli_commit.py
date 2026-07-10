"""CLI entry point for validation-gated strategy approval and commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import load_data
from .config import TutorConfig
from .optimizers.ratchet import StrategyRatchet


_STRATEGY_ID_RE = re.compile(r"^[a-z0-9]+-[a-z-]+-[a-z0-9-]+-\d{3}$")


def _error(args: argparse.Namespace, message: str) -> int:
    output = {"status": "error", "committed": 0, "message": message}
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"ERROR: {message}", file=sys.stderr)
    return 2


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"{label} not found. Complete the previous pipeline stage first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return data


def _artifact_sha256(path: Path, label: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(f"{label} cannot be hashed: {exc}") from exc


def _number(value: Any, field: str, strategy_id: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} is missing or invalid for strategy '{strategy_id}'")
    return float(value)


def _approval_scores(
    strategies: list[dict[str, Any]],
    validation: dict[str, Any],
    evaluation: dict[str, Any],
    pass_score: float,
) -> dict[str, tuple[float, float, float]]:
    if validation.get("all_format_passed") is not True:
        raise ValueError("validation_report.json does not confirm all format checks passed")

    validation_entries = validation.get("results")
    evaluation_entries = evaluation.get("strategies")
    if not isinstance(validation_entries, list) or not isinstance(evaluation_entries, list):
        raise ValueError("validation and evaluation reports must contain strategy result lists")

    validation_by_id = {
        entry.get("strategy_id"): entry
        for entry in validation_entries
        if isinstance(entry, dict) and isinstance(entry.get("strategy_id"), str)
    }
    evaluation_by_id = {
        entry.get("strategy_id"): entry
        for entry in evaluation_entries
        if isinstance(entry, dict) and isinstance(entry.get("strategy_id"), str)
    }

    scores: dict[str, tuple[float, float, float]] = {}
    for strategy in strategies:
        strategy_id = strategy.get("strategy_id")
        if not isinstance(strategy_id, str) or not _STRATEGY_ID_RE.fullmatch(strategy_id):
            raise ValueError("each distilled strategy must have a valid strategy_id")
        validation_entry = validation_by_id.get(strategy_id)
        evaluation_entry = evaluation_by_id.get(strategy_id)
        if not isinstance(validation_entry, dict) or not isinstance(evaluation_entry, dict):
            raise ValueError(f"missing validation or evaluation result for strategy '{strategy_id}'")
        if validation_entry.get("format_passed") is not True or validation_entry.get("structure_passed") is not True:
            raise ValueError(f"validation failed for strategy '{strategy_id}'")

        structure = _number(validation_entry.get("structure_score"), "structure_score", strategy_id)
        effect = _number(evaluation_entry.get("effect_total"), "effect_total", strategy_id)
        total = structure + effect
        if total < pass_score:
            raise ValueError(
                f"strategy '{strategy_id}' scored {total:.1f}, below approval threshold {pass_score:.1f}"
            )
        scores[strategy_id] = (structure, effect, total)
    return scores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Approve validated strategies and commit them to the strategy library."
    )
    parser.add_argument("--artifacts-dir", required=True, help="Session artifacts directory")
    parser.add_argument("--library", required=True, help="Path to strategy-library.json")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    artifacts = Path(args.artifacts_dir)
    library_path = Path(args.library)
    try:
        distilled = _load_json(artifacts / "distilled.json", "distilled.json")
        strategies = distilled.get("strategies", [])
        if not isinstance(strategies, list):
            raise ValueError("distilled.json strategies must be a list")
        if not strategies:
            output = {"status": "warning", "committed": 0, "message": "No strategies to commit (empty)."}
            if args.json:
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                print("No strategies to commit.")
            return 0
        if not all(isinstance(strategy, dict) for strategy in strategies):
            raise ValueError("distilled.json strategies must contain objects")
        cfg = TutorConfig()
        validation_path = artifacts / "validation_report.json"
        evaluation_path = artifacts / "evaluation.json"
        scores = _approval_scores(
            strategies,
            _load_json(validation_path, "validation_report.json"),
            _load_json(evaluation_path, "evaluation.json"),
            cfg.darwin_pass_score,
        )
        approval_evidence = {
            "validation_sha256": _artifact_sha256(validation_path, "validation_report.json"),
            "evaluation_sha256": _artifact_sha256(evaluation_path, "evaluation.json"),
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }
    except ValueError as exc:
        return _error(args, str(exc))

    library = load_data(library_path) if library_path.exists() else {"strategies": []}
    if not isinstance(library, dict) or not isinstance(library.get("strategies", []), list):
        return _error(args, "strategy library must contain a strategies list")
    existing = {
        strategy.get("strategy_id"): strategy
        for strategy in library["strategies"]
        if isinstance(strategy, dict) and strategy.get("strategy_id")
    }
    ratchet = StrategyRatchet(
        touch_top_delta=cfg.darwin_touch_top_delta,
        max_rounds=cfg.darwin_max_rounds,
    )

    committed = []
    skipped = []
    for strategy in strategies:
        strategy_id = strategy["strategy_id"]
        structure, effect, total = scores[strategy_id]
        existing_strategy = existing.get(strategy_id)
        if existing_strategy and total <= existing_strategy.get("darwin_score", 0.0):
            skipped.append({"strategy_id": strategy_id, "reason": "score not improved"})
            continue

        approved = dict(strategy)
        approved["darwin_score"] = total
        approved["lifecycle_status"] = "approved"
        approved["approval_evidence"] = approval_evidence
        ratchet.apply(approved, library, existing_strategy, total)
        committed.append({
            "strategy_id": strategy_id,
            "title": approved.get("title", ""),
            "darwin_score": total,
            "structure_score": structure,
            "effect_score": effect,
        })

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
        for entry in committed:
            print(
                f"  [+] {entry['strategy_id']}: Darwin {entry['darwin_score']:.1f} "
                f"(S:{entry['structure_score']:.1f} + E:{entry['effect_score']:.1f})"
            )
        for entry in skipped:
            print(f"  [-] {entry['strategy_id']}: {entry['reason']}")
    return 0
