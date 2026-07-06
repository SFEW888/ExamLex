from __future__ import annotations

import argparse
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


MIN_TASK_MINUTES = 10
MODULE_ORDER = ("listening", "reading", "writing", "translation", "vocabulary")


def generate_daily_plan(
    profile: dict[str, Any],
    ability_profile: dict[str, Any],
    error_summary: dict[str, Any] | None = None,
    strategies: dict[str, Any] | None = None,
    vocab_pool: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    budget = profile.get("daily_time_budget_minutes")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
        raise ValueError("daily_time_budget_minutes must be a positive integer")

    tasks: list[dict[str, Any]] = []
    remaining = budget

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

    if not tasks and remaining > 0:
        tasks.append(
            {
                "module": MODULE_ORDER[0],
                "focus": "baseline review",
                "minutes": min(MIN_TASK_MINUTES, remaining),
                "reason": "default constrained allocation",
            }
        )

    # Attach vocabulary tasks from vocab pool
    if vocab_pool and tasks:
        vocab_count = max(5, remaining // 2) if remaining > 0 else 10
        selected_vocab = select_daily_vocab(vocab_pool, ability_profile, budget, count=vocab_count)
        if selected_vocab:
            tasks.append({
                "module": "vocabulary",
                "focus": "word study",
                "minutes": min(MIN_TASK_MINUTES, budget),
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
                focus = task.get("focus", "")
                matches = [
                    s for s in strategy_list
                    if isinstance(s, dict)
                    and module in s.get("modules", [])
                    and exam_type in s.get("exam_types", [])
                ]
                # Sort by Darwin score descending, then take top 3
                matches.sort(key=lambda s: s.get("darwin_score", 0.0), reverse=True)
                if matches:
                    task["strategy_hints"] = [
                        {
                            "strategy_id": s.get("strategy_id"),
                            "title": s.get("title"),
                            "darwin_score": s.get("darwin_score"),
                            "source_type": s.get("source_type", "text"),
                            "distillation_method": s.get("distillation_method", "direct"),
                            "trigger_scenario": (s.get("ria_structure", {}).get("a2_trigger", "") or
                                                 s.get("heuristic", {}).get("scenario", "") or ""),
                            "execution_steps": (s.get("ria_structure", {}).get("e_execution", []) or
                                                s.get("steps", [])),
                        }
                        for s in matches[:3]
                    ]

    return {
        "learner_id": profile.get("learner_id"),
        "exam_type": profile.get("exam_type"),
        "daily_time_budget_minutes": budget,
        "total_planned_minutes": sum(task["minutes"] for task in tasks),
        "tasks": tasks,
    }


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
    for module in MODULE_ORDER:
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
    parser.add_argument("--strategies", help="Optional strategy library JSON for method hints.")
    parser.add_argument("--vocab-pool", help="Optional vocabulary pool JSON for word assignments.")
    args = parser.parse_args(argv)

    errors = common.load_data(args.errors) if args.errors else None
    strategies = common.load_data(args.strategies) if args.strategies else None
    vocab_pool = common.load_data(args.vocab_pool) if args.vocab_pool else None
    plan = generate_daily_plan(common.load_data(args.profile), common.load_data(args.ability), errors, strategies, vocab_pool)
    common.save_data(args.output, plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
