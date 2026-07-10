from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


TREND_THRESHOLD = 0.05


def analyze_trends(
    *,
    ledger: list[dict[str, Any]] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    module_series: dict[str, list[float]] = {}
    strategy_series: dict[str, list[float]] = {}

    for record in ledger or []:
        module = record.get("module")
        total_items = record.get("total_items")
        correct_items = record.get("correct_items")
        if not isinstance(module, str) or not module:
            continue
        if not isinstance(total_items, int) or isinstance(total_items, bool) or total_items <= 0:
            continue
        if not isinstance(correct_items, int) or isinstance(correct_items, bool):
            continue
        # Reject inconsistent records: an accuracy ratio must stay within [0, 1].
        if correct_items < 0 or correct_items > total_items:
            continue
        accuracy = correct_items / total_items
        module_series.setdefault(module, []).append(accuracy)
        revisions = record.get("strategy_revisions", [])
        if not isinstance(revisions, list):
            continue
        for revision in revisions:
            if not isinstance(revision, dict):
                continue
            strategy_id = revision.get("strategy_id")
            revision_sha256 = revision.get("revision_sha256")
            if not isinstance(strategy_id, str) or not strategy_id:
                continue
            if not isinstance(revision_sha256, str) or len(revision_sha256) != 64:
                continue
            strategy_series.setdefault(strategy_id, []).append(accuracy)

    for snapshot in history or []:
        modules = snapshot.get("modules") if isinstance(snapshot, dict) else None
        if not isinstance(modules, dict):
            continue
        for module, nodes in modules.items():
            if not isinstance(module, str) or not isinstance(nodes, list):
                continue
            levels = [node.get("level") for node in nodes if isinstance(node, dict)]
            numeric = [level for level in levels if isinstance(level, (int, float)) and not isinstance(level, bool)]
            if numeric:
                module_series.setdefault(module, []).append(sum(numeric) / len(numeric))

    summaries = {module: _summarize_series(values) for module, values in sorted(module_series.items())}
    strategy_summaries = {
        strategy_id: {**_summarize_series(values), "usage_records": len(values)}
        for strategy_id, values in sorted(strategy_series.items())
    }
    return {
        "label": "trend_analysis",
        "inputs": {
            "ledger_records": len(ledger or []),
            "history_snapshots": len(history or []),
        },
        "modules": summaries,
        "strategies": strategy_summaries,
    }


def _summarize_series(values: list[float]) -> dict[str, Any]:
    if len(values) < 2:
        return {
            "direction": "insufficient_data",
            "points": len(values),
            "first": round(values[0], 3) if values else None,
            "last": round(values[-1], 3) if values else None,
            "change": None,
        }
    change = values[-1] - values[0]
    if change > TREND_THRESHOLD:
        direction = "improving"
    elif change < -TREND_THRESHOLD:
        direction = "declining"
    else:
        direction = "stable"
    return {
        "direction": direction,
        "points": len(values),
        "first": round(values[0], 3),
        "last": round(values[-1], 3),
        "change": round(change, 3),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze deterministic ability or practice trends.")
    parser.add_argument("--ledger", help="Optional practice ledger JSON.")
    parser.add_argument("--history", help="Optional ability history JSON list.")
    parser.add_argument("--output", help="Optional output path. Defaults to stdout.")
    args = parser.parse_args(argv)

    ledger = common.load_data(args.ledger) if args.ledger else None
    history = common.load_data(args.history) if args.history else None
    if ledger is not None and not isinstance(ledger, list):
        raise ValueError("practice ledger must be a JSON list")
    if history is not None and not isinstance(history, list):
        raise ValueError("ability history must be a JSON list")
    result = analyze_trends(ledger=ledger, history=history)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        common.save_data(output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
