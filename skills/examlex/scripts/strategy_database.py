from __future__ import annotations

import argparse
import json
import sqlite3
import sys

from . import strategy_sqlite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import or export a transactional SQLite strategy library.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    importer = subparsers.add_parser("import-json")
    importer.add_argument("--input", required=True)
    importer.add_argument("--database", required=True)
    importer.add_argument("--json", action="store_true", help="Print JSON output.")
    exporter = subparsers.add_parser("export-json")
    exporter.add_argument("--database", required=True)
    exporter.add_argument("--output", required=True)
    exporter.add_argument("--json", action="store_true", help="Print JSON output.")

    # Users commonly put a shared output switch before or after a subcommand.
    # Normalize it before argparse so both forms remain stable:
    # ``strategy-db --json import-json ...`` and ``strategy-db import-json ... --json``.
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    json_output = "--json" in raw_args
    args = parser.parse_args([item for item in raw_args if item != "--json"])
    try:
        if args.action == "import-json":
            result = strategy_sqlite.import_json(args.input, args.database)
        else:
            result = strategy_sqlite.export_json(args.database, args.output)
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    result["ok"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2) if json_output else result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
