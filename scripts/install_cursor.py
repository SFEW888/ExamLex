from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.install_claude import SKILL_NAME, install_skill, result_to_json


def default_dest() -> Path:
    return Path.home() / ".cursor" / "rules" / "skills"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install the English Exam AI Tutor Skill for Cursor-compatible local rules.")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "skills" / SKILL_NAME)
    parser.add_argument("--dest", type=Path, default=default_dest())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = install_skill(args.source, args.dest, dry_run=args.dry_run, force=args.force)
    except (FileNotFoundError, FileExistsError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"ERROR: {exc}")
        return 1
    if args.json:
        print(result_to_json(result))
    elif result.dry_run:
        print(f"DRY RUN: would copy {result.source} to Cursor-compatible target {result.target}")
    else:
        print(f"Installed {result.source} to Cursor-compatible target {result.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
