from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


def summarize_errors(ledger_path: str | Path) -> dict[str, Any]:
    ledger = common.load_data(ledger_path)
    if not isinstance(ledger, list):
        raise ValueError("ledger must contain a list of practice records")

    total_records = len(ledger)
    total_error_tags = sum(
        len(record.get("error_tags", []))
        for record in ledger
        if isinstance(record, dict) and isinstance(record.get("error_tags", []), list)
    )
    summary: dict[str, Any] = {
        "total_records": total_records,
        "total_error_tags": total_error_tags,
        "by_tag": {},
        "by_module": {},
        "by_dimension": {},
    }

    for record in ledger:
        if not isinstance(record, dict):
            continue
        tags = record.get("error_tags", [])
        if not isinstance(tags, list):
            continue
        module = str(record.get("module", "unknown"))
        for tag in tags:
            if not isinstance(tag, str):
                continue
            dimension, ability = common.ERROR_TAG_TO_ABILITY.get(tag, (module, "unknown"))
            _add(summary["by_tag"], tag, total_error_tags, module=dimension, dimension=ability)
            _add(summary["by_module"], dimension, total_error_tags)
            _add(summary["by_dimension"], ability, total_error_tags)

    return summary


def _add(bucket: dict[str, Any], key: str, total_error_tags: int, **extra: str) -> None:
    entry = bucket.setdefault(key, {"count": 0, "percentage": 0.0, **extra})
    entry["count"] += 1
    entry["percentage"] = round(entry["count"] / total_error_tags, 2) if total_error_tags else 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize practice ledger error tags.")
    parser.add_argument("--ledger", required=True, help="Path to the practice ledger.")
    parser.add_argument("--output", help="Optional output JSON path.")
    args = parser.parse_args(argv)

    summary = summarize_errors(args.ledger)
    if args.output:
        common.save_data(args.output, summary)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
