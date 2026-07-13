from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from . import common
    from .strategy_store import find_possible_duplicate_strategies
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]
    from strategy_store import find_possible_duplicate_strategies  # type: ignore[no-redef]


def list_strategies(
    library_path: str | Path,
    *,
    search: str | None = None,
    include_duplicates: bool = False,
    duplicate_limit: int = 20,
) -> dict[str, Any]:
    library = common.load_data(library_path)
    if not isinstance(library, dict):
        raise ValueError("strategy library must be a JSON object")
    strategies = library.get("strategies", [])
    if not isinstance(strategies, list):
        raise ValueError("strategy library must contain a strategies list")

    if search:
        needle = search.lower()
        strategies = [
            strategy
            for strategy in strategies
            if isinstance(strategy, dict)
            and needle in json.dumps(strategy, ensure_ascii=False).lower()
        ]

    by_exam: dict[str, int] = {}
    by_module: dict[str, int] = {}
    for strategy in strategies:
        if not isinstance(strategy, dict):
            print(f"Warning: skipping non-dict strategy entry: {strategy!r}", file=sys.stderr)
            continue
        for exam in strategy.get("exam_types", []):
            if isinstance(exam, str):
                by_exam[exam] = by_exam.get(exam, 0) + 1
        for module in strategy.get("modules", []):
            if isinstance(module, str):
                by_module[module] = by_module.get(module, 0) + 1

    result = {
        "total": len(strategies),
        "by_exam": by_exam,
        "by_module": by_module,
        "strategies": strategies,
    }
    if include_duplicates:
        result["duplicate_candidates"] = find_possible_duplicate_strategies(
            {"strategies": strategies},
            limit=duplicate_limit,
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List or search strategy library entries.")
    parser.add_argument("--library", required=True, help="Strategy library JSON path.")
    parser.add_argument("--search", help="Optional keyword search.")
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="List bounded possible-duplicate groups for user review; never deletes data.",
    )
    parser.add_argument("--duplicate-limit", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.duplicate_limit <= 0:
        parser.error("--duplicate-limit must be positive")
    try:
        result = list_strategies(
            args.library,
            search=args.search,
            include_duplicates=args.duplicates,
            duplicate_limit=args.duplicate_limit,
        )
    except (OSError, ValueError) as exc:
        print(f"Error loading strategy library: {exc}", file=sys.stderr)
        return 1
    if args.json:
        _print_json(result)
    else:
        print(f"strategies: {result['total']}")
        if result.get("by_exam"):
            print(f"by exam: {', '.join(f'{k}:{v}' for k,v in sorted(result['by_exam'].items()))}")
        if result.get("by_module"):
            print(f"by module: {', '.join(f'{k}:{v}' for k,v in sorted(result['by_module'].items()))}")
        for strategy in result["strategies"]:
            if isinstance(strategy, dict):
                src = strategy.get("source_type", "text")
                method = strategy.get("distillation_method", "direct")
                print(f"- {strategy.get('strategy_id')}: {strategy.get('title')}  [{src} via {method}]")
        if args.duplicates:
            candidates = result.get("duplicate_candidates", [])
            print(f"possible duplicate groups: {len(candidates)}")
            for candidate in candidates:
                labels = []
                for item in candidate.get("items", []):
                    version = item.get("version")
                    suffix = "" if version == "current" else f"@v{version}"
                    labels.append(f"{item.get('strategy_id')}{suffix}")
                reference_note = " [check references before deletion]" if candidate.get(
                    "requires_reference_check"
                ) else ""
                print(
                    f"- {candidate.get('candidate_id')} {candidate.get('reason')}: "
                    f"{', '.join(labels)}{reference_note}"
                )
    return 0


def _print_json(data: Any) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is not None:
        # Force UTF-8 bytes so non-ASCII output is stable regardless of the
        # console's default encoding (e.g. GBK on Windows).
        buffer.write(text.encode("utf-8"))
    else:
        # Captured stdout (e.g. io.StringIO in tests) has no binary buffer.
        sys.stdout.write(text)
