"""CLI for validating external private tutor prompt assets without exposing their text."""

from __future__ import annotations

import argparse
import json
import sys

from .tutor_prompts import PromptAssetError, audit_private_prompt_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate eight external private tutor prompts without printing their content."
    )
    parser.add_argument("--private-dir", required=True, help="Directory containing eight role-id.md files")
    parser.add_argument("--json", action="store_true", help="Print safe metadata as JSON")
    args = parser.parse_args(argv)

    try:
        report = audit_private_prompt_directory(args.private_dir)
    except (PromptAssetError, OSError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True))
        else:
            print(f"Private prompt validation failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"ok": True, **report}, ensure_ascii=True, indent=2))
        return 0

    print(f"Validated {report['role_count']} private tutor prompts.")
    for role in report["roles"]:
        print(
            f"  [OK] {role['role_id']}: {role['size_bytes']} bytes, "
            f"sha256={role['sha256']}"
        )
    for warning in report["warnings"]:
        print(f"  [WARN] {warning}")
    return 0
