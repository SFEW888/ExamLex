from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from typing import Any

try:
    from . import common
    from .strategy_store import load_strategy_library
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]
    from strategy_store import load_strategy_library  # type: ignore[no-redef]


STRATEGY_ID_RE = re.compile(r"^[a-z0-9]+-[a-z-]+-[a-z0-9-]+-\d{3}$")

# Precompute once; common.ABILITY_TREE is constant across strategies.
_KNOWN_ABILITY_NODES = {node for nodes in common.ABILITY_TREE.values() for node in nodes}


@dataclass
class Check:
    field: str
    status: str
    message: str


def validate_library(library: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
    strategies = library.get("strategies")
    if not isinstance(strategies, list):
        return _fatal("top-level field 'strategies' must be a list")

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    total_pass = total_warn = total_error = 0

    for index, strategy in enumerate(strategies, start=1):
        checks = _validate_strategy(strategy, seen, index)
        passes = sum(1 for check in checks if check.status == "PASS")
        warns = sum(1 for check in checks if check.status == "WARN")
        errors = sum(1 for check in checks if check.status == "ERROR")
        if strict and warns:
            errors += warns
            warns = 0
            checks = [
                Check(check.field, "ERROR" if check.status == "WARN" else check.status, check.message)
                for check in checks
            ]

        total_pass += passes
        total_warn += warns
        total_error += errors
        sid = strategy.get("strategy_id") if isinstance(strategy, dict) else f"<entry-{index}>"
        results.append(
            {
                "strategy_id": sid,
                "checks": [asdict(check) for check in checks],
                "pass": passes,
                "warn": warns,
                "error": errors,
            }
        )

    return {
        "total_strategies": len(strategies),
        "results": results,
        "summary": {
            "total_pass": total_pass,
            "total_warn": total_warn,
            "total_error": total_error,
            "passed": total_error == 0 and total_warn == 0,
        },
    }


def _fatal(message: str) -> dict[str, Any]:
    return {
        "total_strategies": 0,
        "results": [],
        "summary": {"total_pass": 0, "total_warn": 0, "total_error": 1, "passed": False},
        "fatal": message,
    }


def _validate_strategy(strategy: Any, seen: set[str], index: int) -> list[Check]:
    if not isinstance(strategy, dict):
        return [Check("entry", "ERROR", f"strategy entry {index} must be an object")]

    checks: list[Check] = []
    sid = strategy.get("strategy_id")
    if not isinstance(sid, str) or not sid.strip():
        checks.append(Check("strategy_id", "ERROR", "strategy_id is required"))
    elif not STRATEGY_ID_RE.match(sid):
        checks.append(Check("strategy_id", "ERROR", "strategy_id must match {exam}-{module}-{keyword}-{seq}"))
    elif sid in seen:
        checks.append(Check("strategy_id", "ERROR", "strategy_id must be unique"))
    else:
        seen.add(sid)
        checks.append(Check("strategy_id", "PASS", "valid and unique"))

    checks.append(_nonempty(strategy, "title", 1))
    checks.append(_enum_array(strategy, "exam_types", common.EXAM_TYPES))
    checks.append(_enum_array(strategy, "modules", set(common.ABILITY_TREE)))
    checks.append(_nonempty(strategy, "content", 20))
    checks.append(_nonempty(strategy, "source_file", 1))
    checks.append(_date(strategy, "added_at"))

    # Validate source_type and distillation_method if present
    src_type = strategy.get("source_type")
    if src_type is not None:
        if src_type in common.SOURCE_TYPES:
            checks.append(Check("source_type", "PASS", f"valid: {src_type}"))
        else:
            checks.append(Check("source_type", "WARN", f"unknown source_type '{src_type}'. Valid: {sorted(common.SOURCE_TYPES)}"))

    dist_method = strategy.get("distillation_method")
    if dist_method is not None:
        if dist_method in common.DISTILLATION_METHODS:
            checks.append(Check("distillation_method", "PASS", f"valid: {dist_method}"))
        else:
            checks.append(Check("distillation_method", "WARN", f"unknown distillation_method '{dist_method}'. Valid: {sorted(common.DISTILLATION_METHODS)}"))

    ability_nodes = strategy.get("ability_nodes", [])
    if isinstance(ability_nodes, list):
        known_nodes = _KNOWN_ABILITY_NODES
        for node in ability_nodes:
            status = "PASS" if node in known_nodes else "WARN"
            checks.append(Check("ability_nodes", status, f"{node} is {'known' if status == 'PASS' else 'unknown'}"))
    else:
        checks.append(Check("ability_nodes", "WARN", "ability_nodes should be a list when present"))

    steps = strategy.get("steps", [])
    if isinstance(steps, list):
        if any(not isinstance(step, str) or not step.strip() for step in steps):
            checks.append(Check("steps", "WARN", "steps contains an empty item"))
    elif "steps" in strategy:
        checks.append(Check("steps", "WARN", "steps should be a list when present"))

    return checks


def _nonempty(strategy: dict[str, Any], field: str, minimum: int) -> Check:
    value = strategy.get(field)
    if not isinstance(value, str) or len(value.strip()) < minimum:
        return Check(field, "ERROR", f"{field} must contain at least {minimum} characters")
    return Check(field, "PASS", "present")


def _enum_array(strategy: dict[str, Any], field: str, allowed: set[str]) -> Check:
    values = strategy.get(field)
    if not isinstance(values, list) or not values:
        return Check(field, "ERROR", f"{field} must be a non-empty list")
    invalid = [value for value in values if value not in allowed]
    if invalid:
        return Check(field, "ERROR", f"invalid values: {', '.join(map(str, invalid))}")
    return Check(field, "PASS", "all values are valid")


def _date(strategy: dict[str, Any], field: str) -> Check:
    value = strategy.get(field)
    if not isinstance(value, str):
        return Check(field, "ERROR", f"{field} is required")
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return Check(field, "ERROR", f"{field} must be YYYY-MM-DD")
    return Check(field, "PASS", "valid date")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a JSON or SQLite strategy library.")
    parser.add_argument("--library", required=True, help="Strategy library JSON or SQLite path.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    try:
        library = load_strategy_library(args.library)
    except (FileNotFoundError, PermissionError, OSError, ValueError, sqlite3.Error) as exc:
        if args.json:
            _print_json({"file": args.library, "fatal": str(exc)})
        else:
            print(f"ERROR: Cannot load '{args.library}': {exc}", file=sys.stderr)
        return 2
    result = validate_library(library, strict=args.strict)
    result["file"] = args.library
    if args.json:
        _print_json(result)
    else:
        print(f"strategies: {result['total_strategies']}")
        if "fatal" in result:
            print(f"ERROR: {result['fatal']}")
        for entry in result["results"]:
            print(f"{entry['strategy_id']}: {entry['pass']} PASS, {entry['warn']} WARN, {entry['error']} ERROR")

    summary = result["summary"]
    if summary["total_error"]:
        return 2
    if summary["total_warn"]:
        return 1
    return 0


def _print_json(data: Any) -> None:
    sys.stdout.buffer.write((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
