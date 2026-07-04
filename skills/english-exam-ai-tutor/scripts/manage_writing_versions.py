from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


VERSION_RE = re.compile(r"^V([1-9][0-9]*)$")


def add_writing_version(
    records: list[dict[str, Any]],
    *,
    writing_id: str,
    text: str,
    version: str | None = None,
    source_version: str | None = None,
    changes: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not writing_id:
        raise ValueError("writing_id is required")
    if not text:
        raise ValueError("text is required")
    if version is None:
        version = _next_version(records, writing_id)
    elif not VERSION_RE.match(version):
        raise ValueError("version must use V1/V2/V3 style metadata")

    if any(record.get("writing_id") == writing_id and record.get("version") == version for record in records):
        raise ValueError(f"{writing_id} {version} already exists")

    record = {
        "writing_id": writing_id,
        "version": version,
        "source_version": source_version,
        "text": text,
        "changes": changes or [],
    }
    updated = list(records)
    updated.append(record)
    return updated, record


def _next_version(records: list[dict[str, Any]], writing_id: str) -> str:
    highest = 0
    for record in records:
        if record.get("writing_id") != writing_id:
            continue
        raw_version = record.get("version")
        if not isinstance(raw_version, str):
            continue
        match = VERSION_RE.match(raw_version)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"V{highest + 1}"


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = common.load_data(path)
    if not isinstance(data, list):
        raise ValueError("writing versions file must contain a JSON list")
    if not all(isinstance(record, dict) for record in data):
        raise ValueError("writing version records must be objects")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add deterministic writing version metadata.")
    parser.add_argument("--file", required=True, help="Writing versions JSON file to read or create.")
    parser.add_argument("--writing-id", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--version", help="Optional explicit V-number, such as V2.")
    parser.add_argument("--source-version", help="Optional source version metadata.")
    parser.add_argument("--changes", nargs="*", default=[], help="Optional list of deterministic change notes.")
    parser.add_argument("--output", help="Optional output path. Defaults to writing --file.")
    parser.add_argument("--print", action="store_true", dest="print_record", help="Print the added record as JSON.")
    args = parser.parse_args(argv)

    source = Path(args.file)
    records = _load_records(source)
    updated, record = add_writing_version(
        records,
        writing_id=args.writing_id,
        text=args.text,
        version=args.version,
        source_version=args.source_version,
        changes=args.changes,
    )
    output = Path(args.output) if args.output else source
    output.parent.mkdir(parents=True, exist_ok=True)
    common.save_data(output, updated)
    if args.print_record:
        print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
