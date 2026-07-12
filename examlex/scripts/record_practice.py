from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from . import common
    from .file_lock import exclusive_file_lock
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]
    from file_lock import exclusive_file_lock  # type: ignore[no-redef]


_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def record_practice(ledger_path: str | Path, record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    _validate_record(normalized)
    normalized["accuracy"] = round(normalized["correct_items"] / normalized["total_items"], 2)

    path = Path(ledger_path)
    with exclusive_file_lock(path):
        ledger = common.load_data(path) if path.exists() else []
        if not isinstance(ledger, list):
            raise ValueError("ledger must contain a list of practice records")
        ledger.append(normalized)
        common.atomic_save_data(path, ledger)
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

    plan_id = record.get("plan_id")
    if plan_id is not None and (not isinstance(plan_id, str) or not plan_id.strip()):
        raise ValueError("plan_id must be a non-empty string")

    revisions = record.get("strategy_revisions", [])
    if not isinstance(revisions, list):
        raise ValueError("strategy_revisions must be a list")
    strategy_ids: set[str] = set()
    for revision in revisions:
        if not isinstance(revision, dict):
            raise ValueError("each strategy revision must be an object")
        strategy_id = revision.get("strategy_id")
        revision_sha256 = revision.get("revision_sha256")
        if not isinstance(strategy_id, str) or not strategy_id.strip():
            raise ValueError("each strategy revision must have a non-empty strategy_id")
        if not isinstance(revision_sha256, str) or not _SHA256_RE.fullmatch(revision_sha256):
            raise ValueError("each strategy revision must have a lowercase SHA-256 digest")
        if strategy_id in strategy_ids:
            raise ValueError("strategy_revisions cannot repeat a strategy_id")
        strategy_ids.add(strategy_id)

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
            "plan_id", "strategy_revisions",
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


def _references_from_plan(path: str | Path, task_index: int) -> tuple[str, list[dict[str, str]]]:
    plan = common.load_data(path)
    if not isinstance(plan, dict):
        raise ValueError("--plan must contain a JSON object")
    plan_id = plan.get("plan_id")
    tasks = plan.get("tasks")
    if not isinstance(plan_id, str) or not plan_id:
        raise ValueError("--plan is missing plan_id")
    if not isinstance(tasks, list) or task_index < 0 or task_index >= len(tasks):
        raise ValueError("--plan-task-index does not select a task in --plan")
    task = tasks[task_index]
    hints = task.get("strategy_hints", []) if isinstance(task, dict) else []
    if not isinstance(hints, list):
        raise ValueError("selected plan task has invalid strategy_hints")
    revisions = [
        {"strategy_id": hint.get("strategy_id"), "revision_sha256": hint.get("revision_sha256")}
        for hint in hints if isinstance(hint, dict)
    ]
    if len(revisions) != len(hints):
        raise ValueError("selected plan task has invalid strategy hints")
    return plan_id, revisions


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
    parser.add_argument("--plan-id", help="Optional daily-plan identifier that assigned this practice.")
    parser.add_argument("--plan", help="Daily plan JSON to read strategy revisions from.")
    parser.add_argument("--plan-task-index", type=int, default=0, help="Task index in --plan (default: 0).")
    parser.add_argument(
        "--strategy-revisions-json",
        help="Optional JSON list of {strategy_id, revision_sha256} strategy references.",
    )
    parser.add_argument("--timed", action="store_true", help="Mark this record as timed practice.")
    parser.add_argument("--time-limit-minutes", type=int,
                        help="Time limit in minutes (auto-looked up from EXAM_TIME_LIMITS if omitted).")
    parser.add_argument("--overtime-items", type=int, help="Number of items completed after time expired.")
    parser.add_argument("--overtime-correct", type=int, help="Number of overtime items answered correctly.")
    parser.add_argument("--print-record", action="store_true", help="Print the appended record as JSON.")
    args = parser.parse_args(argv)

    if args.strategy_revisions_json:
        try:
            strategy_revisions = json.loads(args.strategy_revisions_json)
        except json.JSONDecodeError as exc:
            parser.error(f"--strategy-revisions-json must be valid JSON: {exc.msg}")
        if not isinstance(strategy_revisions, list):
            parser.error("--strategy-revisions-json must decode to a list")
    else:
        strategy_revisions = None
    if args.record_json and (args.plan_id or args.plan or strategy_revisions is not None):
        parser.error("--record-json cannot be combined with plan or strategy reference options")
    if args.plan and (args.plan_id or strategy_revisions is not None):
        parser.error("--plan cannot be combined with --plan-id or --strategy-revisions-json")

    record_data = _record_from_args(args)
    if not args.record_json:
        if args.plan:
            try:
                plan_id, plan_revisions = _references_from_plan(args.plan, args.plan_task_index)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                parser.error(str(exc))
            record_data["plan_id"] = plan_id
            record_data["strategy_revisions"] = plan_revisions
        elif args.plan_id:
            record_data["plan_id"] = args.plan_id
        if strategy_revisions is not None:
            record_data["strategy_revisions"] = strategy_revisions
    record = record_practice(args.ledger, record_data)
    if args.print_record:
        print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
