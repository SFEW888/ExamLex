from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


STAT_KEYS = ("total_items", "correct_items", "error_count")


def update_ability_profile(ability_profile: dict[str, Any], ledger: list[dict[str, Any]]) -> dict[str, Any]:
    updated = copy.deepcopy(ability_profile)
    modules = updated.setdefault("modules", {})
    if not isinstance(modules, dict):
        raise ValueError("ability profile modules must be an object")

    # The CLI accepts the complete practice ledger, so derived statistics must
    # be rebuilt from that ledger rather than accumulated onto a previous run.
    for nodes in modules.values():
        if not isinstance(nodes, list):
            continue
        for node in nodes:
            if isinstance(node, dict):
                node["stats"] = {**_empty_stats(), "accuracy": None}

    module_stats: dict[str, dict[str, int]] = {}
    dimension_errors: dict[tuple[str, str], int] = {}

    for record in ledger:
        _validate_record(record)
        module = record.get("module")
        if isinstance(module, str) and module:
            stats = module_stats.setdefault(module, _empty_stats())
            stats["total_items"] += record["total_items"]
            stats["correct_items"] += record["correct_items"]

        for tag in record.get("error_tags", []):
            module_name, dimension = common.ERROR_TAG_TO_ABILITY[tag]
            dimension_errors[(module_name, dimension)] = dimension_errors.get((module_name, dimension), 0) + 1

    for (module, dimension), count in dimension_errors.items():
        node = _find_or_create_node(modules, module, dimension)
        _merge_stats(node, {"total_items": 0, "correct_items": 0, "error_count": count})

    for module, stats in module_stats.items():
        for node in _nodes_for_module(modules, module):
            _merge_stats(node, stats)

    for nodes in modules.values():
        if not isinstance(nodes, list):
            continue
        for node in nodes:
            if isinstance(node, dict):
                _refresh_level_and_status(node)

    return updated


def _validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise ValueError("ledger records must be objects")
    if "total" in record or "correct" in record:
        raise ValueError("practice records must use total_items and correct_items")
    total_items = record.get("total_items")
    correct_items = record.get("correct_items")
    if not isinstance(total_items, int) or isinstance(total_items, bool) or total_items <= 0:
        raise ValueError("total_items must be a positive integer")
    if (
        not isinstance(correct_items, int)
        or isinstance(correct_items, bool)
        or correct_items < 0
        or correct_items > total_items
    ):
        raise ValueError("correct_items must be an integer between 0 and total_items")
    error_tags = record.get("error_tags", [])
    if not isinstance(error_tags, list) or not all(isinstance(tag, str) for tag in error_tags):
        raise ValueError("error_tags must be a list of strings")
    unknown = common.validate_error_tags(error_tags)
    if unknown:
        raise ValueError(f"unknown error tags: {', '.join(unknown)}")


def _empty_stats() -> dict[str, int]:
    return {"total_items": 0, "correct_items": 0, "error_count": 0}


def _nodes_for_module(modules: dict[str, Any], module: str) -> list[dict[str, Any]]:
    nodes = modules.setdefault(module, [])
    if not isinstance(nodes, list):
        raise ValueError(f"ability profile module {module} must contain a list")
    return [node for node in nodes if isinstance(node, dict)]


def _find_or_create_node(modules: dict[str, Any], module: str, dimension: str) -> dict[str, Any]:
    nodes = modules.setdefault(module, [])
    if not isinstance(nodes, list):
        raise ValueError(f"ability profile module {module} must contain a list")
    for node in nodes:
        if isinstance(node, dict) and node.get("node") == dimension:
            return node
    node = {"node": dimension, "level": 2, "status": "needs_work"}
    nodes.append(node)
    return node


def _merge_stats(node: dict[str, Any], added: dict[str, int]) -> None:
    stats = node.setdefault("stats", {})
    if not isinstance(stats, dict):
        stats = {}
        node["stats"] = stats
    for key in STAT_KEYS:
        stats[key] = _int_value(stats.get(key)) + added.get(key, 0)
    stats["accuracy"] = round(stats["correct_items"] / stats["total_items"], 2) if stats["total_items"] else None


def _refresh_level_and_status(node: dict[str, Any]) -> None:
    stats = node.get("stats")
    if not isinstance(stats, dict):
        return
    total_items = _int_value(stats.get("total_items"))
    correct_items = _int_value(stats.get("correct_items"))
    error_count = _int_value(stats.get("error_count"))
    accuracy = correct_items / total_items if total_items else None

    if error_count >= 2 or (accuracy is not None and accuracy < 0.60):
        status, level = "priority", 1
    elif error_count == 1 or (accuracy is not None and accuracy < 0.80):
        status, level = "needs_work", 2
    elif accuracy is not None and accuracy < 0.90:
        status, level = "stable", 3
    elif accuracy is not None:
        status, level = "strong", 4
    else:
        return

    node["status"] = status
    node["level"] = level


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    # Preserve whole-number floats (e.g. 15.0 from manual edits or other tools)
    # instead of silently discarding accumulated stats.
    if isinstance(value, float) and value == int(value):
        return int(value)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Update an ability profile from a practice ledger.")
    parser.add_argument("--ability", required=True, help="Path to ability profile JSON.")
    parser.add_argument("--ledger", required=True, help="Path to practice ledger JSON.")
    parser.add_argument("--output", help="Optional output path. Defaults to updating --ability in place.")
    args = parser.parse_args(argv)

    ability = common.load_data(args.ability)
    ledger = common.load_data(args.ledger)
    if not isinstance(ability, dict):
        raise ValueError("ability profile must be a JSON object")
    if not isinstance(ledger, list):
        raise ValueError("practice ledger must be a JSON list")
    updated = update_ability_profile(ability, ledger)
    output = Path(args.output) if args.output else Path(args.ability)
    output.parent.mkdir(parents=True, exist_ok=True)
    common.save_data(output, updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
