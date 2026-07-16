from __future__ import annotations

import argparse
import re
from datetime import date
from typing import Any

try:
    from . import common
    from . import strategy_store
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]
    import strategy_store  # type: ignore[no-redef]


MIN_TASK_MINUTES = 10
MODULE_ORDER = ("listening", "reading", "writing", "translation", "vocabulary")
TEM_MODULE_ORDER = (
    "listening", "reading", "writing", "translation", "vocabulary",
    "language-knowledge", "proofreading", "dictation",
)
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _module_order_for(exam_type: str) -> tuple[str, ...]:
    """Return the module order appropriate for a given exam type."""
    if exam_type in {"TEM4", "TEM8"}:
        return TEM_MODULE_ORDER
    return MODULE_ORDER


def generate_daily_plan(
    profile: dict[str, Any],
    ability_profile: dict[str, Any],
    error_summary: dict[str, Any] | None = None,
    strategies: dict[str, Any] | None = None,
    vocab_pool: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise TypeError(f"profile must be a dict, got {type(profile).__name__}")
    if not isinstance(ability_profile, dict):
        raise TypeError(f"ability_profile must be a dict, got {type(ability_profile).__name__}")
    budget = profile.get("daily_time_budget_minutes")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
        raise ValueError("daily_time_budget_minutes must be a positive integer")

    tasks: list[dict[str, Any]] = []
    selected_vocab: list[dict[str, Any]] = []
    vocab_minutes = 0
    if vocab_pool and budget >= MIN_TASK_MINUTES * 2:
        selected_vocab = select_daily_vocab(
            vocab_pool,
            ability_profile,
            budget,
            count=max(5, min(20, budget // 2)),
        )
        if selected_vocab:
            vocab_minutes = MIN_TASK_MINUTES
    remaining = budget - vocab_minutes

    priority_error = _priority_error(error_summary)
    if priority_error and remaining >= MIN_TASK_MINUTES:
        module, dimension = common.ERROR_TAG_TO_ABILITY[priority_error]
        minutes = min(15, remaining)
        tasks.append(
            {
                "module": module,
                "focus": dimension,
                "minutes": minutes,
                "reason": f"priority error: {priority_error}",
            }
        )
        remaining -= minutes

    for candidate in _ability_candidates(ability_profile):
        if remaining < MIN_TASK_MINUTES:
            break
        minutes = min(15 if candidate["status"] == "priority" else 10, remaining)
        tasks.append(
            {
                "module": candidate["module"],
                "focus": candidate["node"],
                "minutes": minutes,
                "reason": f"{candidate['status']} ability node",
            }
        )
        remaining -= minutes

    # Spaced repetition: add review tasks for urgent error tags
    review_urgent: list[dict[str, Any]] = []
    REVIEW_URGENCY_THRESHOLD = 0.5
    if error_summary and isinstance(error_summary.get("by_tag"), dict):
        for tag, tag_data in error_summary["by_tag"].items():
            if not isinstance(tag_data, dict):
                continue
            urgency = tag_data.get("review_urgency", 0)
            if isinstance(urgency, (int, float)) and urgency > REVIEW_URGENCY_THRESHOLD:
                module_node = common.ERROR_TAG_TO_ABILITY.get(tag)
                if module_node:
                    module, node = module_node
                    last_date = tag_data.get("last_practice_date", "")
                    review_urgent.append({
                        "module": module,
                        "focus": node,
                        "tag": tag,
                        "urgency": urgency,
                        "last_practice_date": last_date,
                    })
    # Sort by urgency descending
    review_urgent.sort(key=lambda r: r["urgency"], reverse=True)
    # Add up to 2 review tasks
    for review in review_urgent[:2]:
        if remaining < MIN_TASK_MINUTES:
            break
        minutes = min(15, remaining)
        tasks.append({
            "module": review["module"],
            "focus": review["focus"],
            "minutes": minutes,
            "reason": f"spaced review (urgency: {review['urgency']:.2f})",
        })
        remaining -= minutes

    if not tasks and remaining > 0:
        exam = profile.get("exam_type", "")
        fallback_module = _module_order_for(str(exam))[0]
        tasks.append(
            {
                "module": fallback_module,
                "minutes": min(MIN_TASK_MINUTES, remaining),
                "reason": "default constrained allocation",
            }
        )

    if selected_vocab:
        tasks.append({
            "module": "vocabulary",
            "focus": "word study",
            "minutes": vocab_minutes,
            "reason": "vocab pool selection",
            "vocab_items": selected_vocab,
        })

    # Attach matching strategies from strategy library
    exam_type = profile.get("exam_type", "")
    if strategies and tasks:
        strategy_list = strategies.get("strategies", []) if isinstance(strategies, dict) else []
        if isinstance(strategy_list, list):
            for task in tasks:
                module = task.get("module", "")
                matches = []
                for strategy in strategy_list:
                    revision_sha256 = _latest_revision_sha256(strategy)
                    if (
                        isinstance(strategy, dict)
                        and revision_sha256 is not None
                        and strategy.get("lifecycle_status") == "approved"
                        and isinstance(strategy.get("modules"), list) and module in strategy["modules"]
                        and isinstance(strategy.get("exam_types"), list) and exam_type in strategy["exam_types"]
                    ):
                        matches.append((strategy, revision_sha256))
                # Sort by Darwin score descending, then take top 3
                matches.sort(key=lambda item: item[0].get("darwin_score", 0.0), reverse=True)
                if matches:
                    task["strategy_hints"] = [
                        {
                            "strategy_id": s.get("strategy_id"),
                            "revision_sha256": revision_sha256,
                            "title": s.get("title"),
                            "darwin_score": s.get("darwin_score"),
                            "source_type": s.get("source_type", "text"),
                            "distillation_method": s.get("distillation_method", "direct"),
                            "trigger_scenario": ((s.get("ria_structure") or {}).get("a2_trigger", "") or
                                                 (s.get("heuristic") or {}).get("scenario", "") or ""),
                            "execution_steps": ((s.get("ria_structure") or {}).get("e_execution", []) or
                                                s.get("steps", [])),
                        }
                        for s, revision_sha256 in matches[:3]
                    ]

    return {
        "plan_id": f"{profile.get('learner_id', 'learner')}-{date.today().isoformat()}",
        "learner_id": profile.get("learner_id"),
        "exam_type": profile.get("exam_type"),
        "daily_time_budget_minutes": budget,
        "total_planned_minutes": sum(task["minutes"] for task in tasks),
        "tasks": tasks,
    }


def _latest_revision_sha256(strategy: Any) -> str | None:
    if not isinstance(strategy, dict):
        return None
    revisions = strategy.get("revisions")
    if not isinstance(revisions, list) or not revisions:
        return None
    revision = revisions[-1]
    if not isinstance(revision, dict):
        return None
    digest = revision.get("sha256")
    snapshot = revision.get("strategy")
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        return None
    if not isinstance(snapshot, dict) or snapshot.get("strategy_id") != strategy.get("strategy_id"):
        return None
    current_snapshot = {
        key: value
        for key, value in strategy.items()
        if key not in {"score_history", "revisions"}
    }
    if current_snapshot != snapshot:
        return None
    try:
        actual_digest = common.canonical_json_sha256(snapshot)
    except (TypeError, ValueError):
        return None
    if actual_digest != digest:
        return None
    return digest


def _priority_error(error_summary: dict[str, Any] | None) -> str | None:
    if not error_summary:
        return None
    raw_by_tag = error_summary.get("by_tag", error_summary)
    if not isinstance(raw_by_tag, dict):
        return None

    ranked: list[tuple[int, str]] = []
    for tag, data in raw_by_tag.items():
        if tag not in common.ERROR_TAG_TO_ABILITY:
            continue
        count = data.get("count", 0) if isinstance(data, dict) else data
        if isinstance(count, int) and not isinstance(count, bool):
            ranked.append((count, tag))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def _ability_candidates(ability_profile: dict[str, Any]) -> list[dict[str, Any]]:
    modules = ability_profile.get("modules", {})
    if not isinstance(modules, dict):
        return []

    candidates: list[dict[str, Any]] = []
    # Use all ability tree modules to cover CET and TEM exams
    all_modules = list(modules.keys()) if modules else list(common.ABILITY_TREE.keys())
    for module in all_modules:
        nodes = modules.get(module, [])
        if not isinstance(nodes, list):
            continue
        for node in nodes:
            if not isinstance(node, dict):
                continue
            status = str(node.get("status", "needs_work"))
            level = node.get("level", 99)
            candidates.append(
                {
                    "module": module,
                    "node": str(node.get("node", module)),
                    "status": status,
                    "level": level if isinstance(level, int) else 99,
                }
            )
    candidates.sort(
        key=lambda item: (
            0 if item["status"] == "priority" else 1,
            item["level"],
            item["module"],
            item["node"],
        )
    )
    return candidates


def select_daily_vocab(
    vocab_pool: list[dict[str, Any]],
    ability_profile: dict[str, Any],
    daily_time_budget: int,
    count: int = 20,
) -> list[dict[str, Any]]:
    """Select daily vocabulary tasks from pool based on ability needs.

    Prioritizes words related to ability nodes marked as 'needs_work' or 'priority',
    then fills remaining slots with lowest-frequency-rank words.
    """
    if not vocab_pool:
        return []

    # Collect ability nodes that need work
    weak_dimensions: set[str] = set()
    modules = ability_profile.get("modules", {})
    if isinstance(modules, dict):
        for nodes in modules.values():
            if not isinstance(nodes, list):
                continue
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if node.get("status") in ("needs_work", "priority"):
                    weak_dimensions.add(str(node.get("node", "")).lower())

    # Score each word: higher score = higher priority
    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in vocab_pool:
        if not isinstance(entry, dict):
            continue
        score = 0
        # Boost words whose synonyms, collocations, or POS match weak dimensions
        entry_text = (
            str(entry.get("word", "")) + " "
            + str(entry.get("pos", "")) + " "
            + " ".join(entry.get("synonyms", [])) + " "
            + " ".join(entry.get("collocations", []))
        ).lower()
        for dim in weak_dimensions:
            if dim in entry_text:
                score += 10
        # Prefer lower frequency rank (less common = more likely unknown)
        rank = entry.get("frequency_rank", 9999)
        if isinstance(rank, int) and rank > 0:
            score += max(0, 5000 - rank) // 500
        scored.append((score, entry))

    # Sort: highest score first, then lower frequency_rank
    scored.sort(key=lambda item: (-item[0], item[1].get("frequency_rank", 9999)))

    selected = [entry for _, entry in scored[:count]]
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic constrained daily plan.")
    parser.add_argument("--profile", required=True, help="Path to learner profile JSON.")
    parser.add_argument("--ability", required=True, help="Path to ability profile JSON.")
    parser.add_argument("--output", required=True, help="Path to write the generated plan JSON.")
    parser.add_argument("--errors", help="Optional summarized error JSON input.")
    parser.add_argument("--strategies", help="Optional JSON or SQLite strategy library for method hints.")
    parser.add_argument("--vocab-pool", help="Optional vocabulary pool JSON for word assignments.")
    args = parser.parse_args(argv)

    errors = common.load_data(args.errors) if args.errors else None
    strategies = strategy_store.load_strategy_library(args.strategies) if args.strategies else None
    vocab_pool = common.load_data(args.vocab_pool) if args.vocab_pool else None
    plan = generate_daily_plan(common.load_data(args.profile), common.load_data(args.ability), errors, strategies, vocab_pool)
    common.save_data(args.output, plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
