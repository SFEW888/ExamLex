"""CLI entry point for validation-gated strategy approval and commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .cleanup_sessions import apply_retention_policy
from .common import canonical_json_sha256
from .config import TutorConfig
from .optimizers.ratchet import StrategyRatchet
from .session import Session
from .strategy_store import (
    find_possible_duplicate_strategies,
    mutate_strategy_library,
    warn_duplicate_candidates,
    warn_if_strategy_library_large,
)


_STRATEGY_ID_RE = re.compile(r"^[a-z0-9]+-[a-z-]+-[a-z0-9-]+-\d{3}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def _index_report_entries(
    entries: list[Any], label: str
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("strategy_id"), str):
            raise ValueError(f"{label} report contains an invalid strategy result")
        strategy_id = entry["strategy_id"]
        if strategy_id in indexed:
            raise ValueError(f"{label} report repeats strategy_id '{strategy_id}'")
        indexed[strategy_id] = entry
    return indexed


def _approval_scores(
    strategies: list[dict[str, Any]],
    validation: dict[str, Any],
    evaluation: dict[str, Any],
    pass_score: float,
) -> dict[str, tuple[float, float, float, str]]:
    if validation.get("all_format_passed") is not True:
        raise ValueError("validation_report.json does not confirm all format checks passed")

    validation_entries = validation.get("results")
    evaluation_entries = evaluation.get("strategies")
    if not isinstance(validation_entries, list) or not isinstance(evaluation_entries, list):
        raise ValueError("validation and evaluation reports must contain strategy result lists")

    validation_by_id = _index_report_entries(validation_entries, "validation")
    evaluation_by_id = _index_report_entries(evaluation_entries, "evaluation")
    scores: dict[str, tuple[float, float, float, str]] = {}
    seen_strategy_ids: set[str] = set()
    for strategy in strategies:
        strategy_id = strategy.get("strategy_id")
        if not isinstance(strategy_id, str) or not _STRATEGY_ID_RE.fullmatch(strategy_id):
            raise ValueError("each distilled strategy must have a valid strategy_id")
        if strategy_id in seen_strategy_ids:
            raise ValueError(f"distilled strategies repeat strategy_id '{strategy_id}'")
        seen_strategy_ids.add(strategy_id)
        validation_entry = validation_by_id.get(strategy_id)
        evaluation_entry = evaluation_by_id.get(strategy_id)
        if not isinstance(validation_entry, dict) or not isinstance(evaluation_entry, dict):
            raise ValueError(f"missing validation or evaluation result for strategy '{strategy_id}'")
        if validation_entry.get("format_passed") is not True or validation_entry.get("structure_passed") is not True:
            raise ValueError(f"validation failed for strategy '{strategy_id}'")

        strategy_sha256 = canonical_json_sha256(strategy)
        for label, entry in (
            ("validation", validation_entry),
            ("evaluation", evaluation_entry),
        ):
            reported_digest = entry.get("strategy_sha256")
            if (
                not isinstance(reported_digest, str)
                or not _SHA256_RE.fullmatch(reported_digest)
                or reported_digest != strategy_sha256
            ):
                raise ValueError(
                    f"{label} evidence does not match current content for strategy '{strategy_id}'"
                )

        structure = _number(validation_entry.get("structure_score"), "structure_score", strategy_id)
        effect = _number(evaluation_entry.get("effect_total"), "effect_total", strategy_id)
        total = structure + effect
        if total < pass_score:
            raise ValueError(
                f"strategy '{strategy_id}' scored {total:.1f}, below approval threshold {pass_score:.1f}"
            )
        scores[strategy_id] = (structure, effect, total, strategy_sha256)
    return scores


def _complete_managed_session(
    artifacts: Path,
    cfg: TutorConfig,
) -> tuple[dict[str, Any], list[str]]:
    """Complete a standard managed session and apply automatic retention."""
    state_path = artifacts / "pipeline_state.json"
    if not state_path.exists():
        return {"status": "not_managed"}, []
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "warning"}, [f"session retention skipped: {exc}"]
    if not isinstance(state, dict):
        return {"status": "warning"}, ["session retention skipped: invalid pipeline state"]

    resolved_artifacts = artifacts.resolve()
    stored_artifacts = state.get("artifacts_dir")
    session_id = state.get("session_id")
    if (
        not isinstance(stored_artifacts, str)
        or Path(stored_artifacts).resolve() != resolved_artifacts
        or not isinstance(session_id, str)
        or session_id != resolved_artifacts.name
        or not _DATE_DIR_RE.fullmatch(resolved_artifacts.parent.name)
    ):
        return {"status": "warning"}, [
            "session retention skipped: artifacts do not match the managed date/session layout"
        ]

    session = Session(
        session_id=session_id,
        artifacts_dir=resolved_artifacts,
        source_type=str(state.get("source_type", "unknown")),
        current_stage=str(state.get("stage", "unknown")),
        sub_stage=state.get("sub_stage") if isinstance(state.get("sub_stage"), str) else None,
    )
    try:
        session.checkpoint("committed")
    except (OSError, TimeoutError) as exc:
        return {"status": "warning"}, [f"session completion checkpoint failed: {exc}"]

    if not cfg.auto_cleanup:
        return {"status": "disabled", "session_id": session_id}, []
    try:
        result = apply_retention_policy(
            resolved_artifacts.parent.parent,
            retention_hours=cfg.session_retention_hours,
            max_reproducible_artifact_bytes=cfg.max_reproducible_artifact_bytes,
        )
    except (OSError, TimeoutError, ValueError) as exc:
        return {"status": "warning", "session_id": session_id}, [
            f"automatic session retention failed: {exc}"
        ]
    status = "warning" if result.failures else "ok"
    warnings = [f"automatic session retention: {message}" for message in result.failures]
    return {"status": status, "session_id": session_id, **asdict(result)}, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Approve validated strategies and commit them to the strategy library."
    )
    parser.add_argument("--artifacts-dir", required=True, help="Session artifacts directory")
    parser.add_argument("--library", required=True, help="Path to a JSON or SQLite strategy library")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    artifacts = Path(args.artifacts_dir)
    library_path = Path(args.library)
    cfg = TutorConfig()
    try:
        distilled = _load_json(artifacts / "distilled.json", "distilled.json")
        strategies = distilled.get("strategies", [])
        if not isinstance(strategies, list):
            raise ValueError("distilled.json strategies must be a list")
        if not strategies:
            retention, warnings = _complete_managed_session(artifacts, cfg)
            library_health = warn_if_strategy_library_large(
                library_path,
                warning_threshold_bytes=cfg.strategy_library_warning_bytes,
            )
            output = {
                "status": "warning",
                "committed": 0,
                "message": "No strategies to commit (empty).",
                "retention": retention,
                "strategy_library": library_health,
                "warnings": warnings,
            }
            if args.json:
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                print("No strategies to commit.")
                for warning in warnings:
                    print(f"Warning: {warning}", file=sys.stderr)
            return 0
        if not all(isinstance(strategy, dict) for strategy in strategies):
            raise ValueError("distilled.json strategies must contain objects")
        validation_path = artifacts / "validation_report.json"
        evaluation_path = artifacts / "evaluation.json"
        scores = _approval_scores(
            strategies,
            _load_json(validation_path, "validation_report.json"),
            _load_json(evaluation_path, "evaluation.json"),
            cfg.darwin_pass_score,
        )
        approval_evidence_base = {
            "validation_sha256": _artifact_sha256(validation_path, "validation_report.json"),
            "evaluation_sha256": _artifact_sha256(evaluation_path, "evaluation.json"),
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }
    except ValueError as exc:
        return _error(args, str(exc))

    ratchet = StrategyRatchet(
        touch_top_delta=cfg.darwin_touch_top_delta,
        max_rounds=cfg.darwin_max_rounds,
    )

    committed = []
    skipped = []
    duplicate_candidates: list[dict[str, Any]] = []

    def apply_approvals(library: dict[str, Any]) -> None:
        previous_candidates = {
            candidate["candidate_id"]
            for candidate in find_possible_duplicate_strategies(library, limit=1000)
        }
        existing = {
            item.get("strategy_id"): item
            for item in library["strategies"]
            if isinstance(item, dict) and item.get("strategy_id")
        }
        for strategy in strategies:
            strategy_id = strategy["strategy_id"]
            structure, effect, total, strategy_sha256 = scores[strategy_id]
            existing_strategy = existing.get(strategy_id)
            if existing_strategy and total <= existing_strategy.get("darwin_score", 0.0):
                skipped.append({"strategy_id": strategy_id, "reason": "score not improved"})
                continue

            approved = dict(strategy)
            approved["darwin_score"] = total
            approved["lifecycle_status"] = "approved"
            approved["approval_evidence"] = {
                **approval_evidence_base,
                "strategy_sha256": strategy_sha256,
            }
            updated = ratchet.apply(
                approved, library, existing_strategy, total
            )
            existing[strategy_id] = updated
            committed.append({
                "strategy_id": strategy_id,
                "title": approved.get("title", ""),
                "darwin_score": total,
                "structure_score": structure,
                "effect_score": effect,
            })
        duplicate_candidates.extend(
            candidate
            for candidate in find_possible_duplicate_strategies(library, limit=1000)
            if candidate["candidate_id"] not in previous_candidates
        )

    try:
        mutate_strategy_library(library_path, apply_approvals)
    except (OSError, TimeoutError, ValueError) as exc:
        return _error(args, str(exc))
    warn_duplicate_candidates(
        duplicate_candidates,
        library_path=library_path,
    )
    library_health = warn_if_strategy_library_large(
        library_path,
        warning_threshold_bytes=cfg.strategy_library_warning_bytes,
    )
    retention, retention_warnings = _complete_managed_session(artifacts, cfg)
    output = {
        "status": "ok",
        "committed": len(committed),
        "skipped": len(skipped),
        "library_path": str(library_path),
        "details": committed,
        "retention": retention,
        "strategy_library": library_health,
        "duplicate_candidates": duplicate_candidates,
        "warnings": retention_warnings,
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
        for warning in retention_warnings:
            print(f"Warning: {warning}", file=sys.stderr)
    return 0
