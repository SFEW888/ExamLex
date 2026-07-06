from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


def record_practice(ledger_path: str | Path, record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    _validate_record(normalized)
    normalized["accuracy"] = round(normalized["correct_items"] / normalized["total_items"], 2)

    path = Path(ledger_path)
    ledger = common.load_data(path) if path.exists() else []
    if not isinstance(ledger, list):
        raise ValueError("ledger must contain a list of practice records")
    ledger.append(normalized)
    path.parent.mkdir(parents=True, exist_ok=True)
    common.save_data(path, ledger)
    return normalized


def _validate_record(record: dict[str, Any]) -> None:
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

    duration_minutes = record.get("duration_minutes")
    if duration_minutes is not None and (
        not isinstance(duration_minutes, int)
        or isinstance(duration_minutes, bool)
        or duration_minutes <= 0
    ):
        raise ValueError("duration_minutes must be a positive integer")

    overtime_items = record.get("overtime_items")
    overtime_correct = record.get("overtime_correct")
    if overtime_items is not None and (
        not isinstance(overtime_items, int)
        or isinstance(overtime_items, bool)
        or overtime_items < 0
    ):
        raise ValueError("overtime_items must be a non-negative integer")
    if overtime_correct is not None and (
        not isinstance(overtime_correct, int)
        or isinstance(overtime_correct, bool)
        or overtime_correct < 0
    ):
        raise ValueError("overtime_correct must be a non-negative integer")
    if (
        overtime_items is not None
        and overtime_correct is not None
        and overtime_correct > overtime_items
    ):
        raise ValueError("overtime_correct cannot exceed overtime_items")


def _record_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.record_json:
        record = json.loads(args.record_json)
        if not isinstance(record, dict):
            raise ValueError("--record-json must decode to an object")
        allowed_keys = {
            "date", "exam_type", "module", "task_id", "duration_minutes",
            "total_items", "correct_items", "error_tags",
            "timed", "time_limit_minutes", "overtime_items", "overtime_correct",
        }
        unknown = set(record) - allowed_keys
        if unknown:
            raise ValueError(
                f"unknown fields in --record-json: {', '.join(sorted(unknown))}"
            )
        return record

    record: dict[str, Any] = {
        "date": args.date,
        "exam_type": args.exam_type,
        "module": args.module,
        "task_id": args.task_id,
        "duration_minutes": args.duration_minutes,
        "total_items": args.total_items,
        "correct_items": args.correct_items,
        "error_tags": args.error_tags or [],
    }

    # Timed practice fields
    if args.timed:
        record["timed"] = True
        if args.time_limit_minutes is not None:
            record["time_limit_minutes"] = args.time_limit_minutes
        elif args.exam_type and args.module:
            auto_limit = common.get_time_limit(args.exam_type, args.module)
            if auto_limit is not None:
                record["time_limit_minutes"] = auto_limit
        if args.overtime_items is not None:
            record["overtime_items"] = args.overtime_items
        if args.overtime_correct is not None:
            record["overtime_correct"] = args.overtime_correct

    return {key: value for key, value in record.items() if value is not None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append a practice record to a JSON ledger.")
    parser.add_argument("--ledger", required=True, help="Path to the practice ledger.")
    parser.add_argument("--record-json", help="Complete record as a JSON object.")
    parser.add_argument("--date")
    parser.add_argument("--exam-type")
    parser.add_argument("--module")
    parser.add_argument("--task-id")
    parser.add_argument("--duration-minutes", type=int)
    parser.add_argument("--total-items", type=int)
    parser.add_argument("--correct-items", type=int)
    parser.add_argument("--error-tags", nargs="*")
    parser.add_argument("--timed", action="store_true", help="Mark this record as timed practice.")
    parser.add_argument("--time-limit-minutes", type=int,
                        help="Time limit in minutes (auto-looked up from EXAM_TIME_LIMITS if omitted).")
    parser.add_argument("--overtime-items", type=int, help="Number of items completed after time expired.")
    parser.add_argument("--overtime-correct", type=int, help="Number of overtime items answered correctly.")
    parser.add_argument("--print-record", action="store_true", help="Print the appended record as JSON.")
    args = parser.parse_args(argv)

    record = record_practice(args.ledger, _record_from_args(args))
    if args.print_record:
        print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
