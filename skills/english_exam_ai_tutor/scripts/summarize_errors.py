from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


def summarize_errors(ledger_path: str | Path, window_days: int = 30) -> dict[str, Any]:
    ledger = common.load_data(ledger_path)
    if not isinstance(ledger, list):
        raise ValueError("ledger must contain a list of practice records")

    today = datetime.date.today()
    total_records = len(ledger)
    # Count only string tags so the percentage denominator matches the per-tag
    # counting below (which skips non-string tags).
    total_error_tags = sum(
        sum(1 for tag in record.get("error_tags", []) if isinstance(tag, str))
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

    # Spaced repetition: compute review urgency for each error tag
    for tag in list(summary["by_tag"].keys()):
        last_date, urgency = compute_review_urgency(tag, ledger, today, window_days)
        summary["by_tag"][tag]["last_practice_date"] = last_date
        summary["by_tag"][tag]["review_urgency"] = urgency

    # Speed analysis: aggregate timed practice records
    timed_records = [r for r in ledger if isinstance(r, dict) and r.get("timed")]
    if timed_records:
        total_overtime_items = sum(_as_number(r.get("overtime_items", 0)) for r in timed_records)
        total_overtime_correct = sum(_as_number(r.get("overtime_correct", 0)) for r in timed_records)
        overtime_accuracy = (
            # Clamp to 1.0: inconsistent records (overtime_correct > overtime_items)
            # must not produce an accuracy above 100%.
            round(min(total_overtime_correct / total_overtime_items, 1.0), 3)
            if total_overtime_items > 0 else 0.0
        )
        # Per-module speed breakdown
        by_module_speed: dict[str, dict[str, Any]] = {}
        for r in timed_records:
            mod = str(r.get("module", "unknown"))
            entry = by_module_speed.setdefault(mod, {
                "timed_sessions": 0, "overtime_items": 0, "overtime_correct": 0,
            })
            entry["timed_sessions"] += 1
            entry["overtime_items"] += _as_number(r.get("overtime_items", 0))
            entry["overtime_correct"] += _as_number(r.get("overtime_correct", 0))

        summary["speed_analysis"] = {
            "timed_sessions": len(timed_records),
            "total_overtime_items": total_overtime_items,
            "overtime_accuracy": overtime_accuracy,
            "verdict": (
                "速度是主要瓶颈" if overtime_accuracy > 0.6
                else "知识缺口是主要瓶颈" if overtime_accuracy < 0.3
                else "速度与知识均需提升"
            ),
            "by_module": by_module_speed,
        }

    return summary


def _as_number(value: Any) -> int | float:
    """Return numeric values unchanged; coerce booleans and non-numerics to 0.

    Guards aggregation against malformed ledger records that store strings,
    ``None``, or other non-numeric values in the overtime fields.
    """
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return value
    return 0


def _add(bucket: dict[str, Any], key: str, total_error_tags: int, **extra: str) -> None:
    entry = bucket.setdefault(key, {"count": 0, "percentage": 0.0, **extra})
    entry["count"] += 1
    entry["percentage"] = round(entry["count"] / total_error_tags, 2) if total_error_tags else 0.0


def compute_review_urgency(
    tag: str,
    ledger: list[dict],
    today: datetime.date | None = None,
    window_days: int = 30,
) -> tuple[str | None, float]:
    """Compute review urgency for an error tag.

    Uses base severity weight from common.ERROR_SEVERITY_WEIGHTS,
    days since last occurrence, and recent error frequency.
    Returns (last_practice_date_iso, urgency_0_to_1).
    """
    if today is None:
        today = datetime.date.today()

    tagged = [r for r in ledger if isinstance(r, dict) and tag in r.get("error_tags", [])]
    if not tagged:
        return (None, 0.0)

    # Last occurrence date
    dates = []
    for r in tagged:
        try:
            dates.append(datetime.date.fromisoformat(str(r["date"])))
        except (ValueError, KeyError):
            continue
    if not dates:
        return (None, 0.0)

    last_date = max(dates)
    days_since = max(0, (today - last_date).days)

    # Recent frequency within window
    recent_count = sum(1 for d in dates if (today - d).days <= window_days)

    def _days_since(record: dict) -> int | None:
        # Exclude records with missing or malformed dates from the window count
        # (instead of defaulting them to "today", which would inflate urgency)
        # and never let a bad date string crash the whole summary.
        date_str = record.get("date")
        if not isinstance(date_str, str):
            return None
        try:
            return (today - datetime.date.fromisoformat(date_str)).days
        except ValueError:
            return None

    total_records_in_window = sum(
        1 for r in ledger
        if isinstance(r, dict)
        and (_ds := _days_since(r)) is not None
        and _ds <= window_days
    )
    error_freq = recent_count / total_records_in_window if total_records_in_window > 0 else 0.0

    base_weight = common.ERROR_SEVERITY_WEIGHTS.get(tag, 0.5)
    urgency = base_weight * (days_since / 7.0) * (error_freq + 0.1)
    urgency = min(urgency, 1.0)

    return (last_date.isoformat(), round(urgency, 3))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize practice ledger error tags.")
    parser.add_argument("--ledger", required=True, help="Path to the practice ledger.")
    parser.add_argument("--output", help="Optional output JSON path.")
    parser.add_argument("--days", type=int, default=30, help="Review window in days (default: 30).")
    args = parser.parse_args(argv)

    summary = summarize_errors(args.ledger, window_days=args.days)
    if args.output:
        common.save_data(args.output, summary)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
