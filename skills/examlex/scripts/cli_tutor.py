"""Safe CLI preflight for the in-process private tutor runtime."""

from __future__ import annotations

import argparse
import json
import sys

from .tutor_prompts import PromptAssetError, ROLE_IDS
from .tutor_runtime import (
    CLARIFICATION_FIELDS,
    ROLE_ALIASES,
    prepare_tutor_turn,
    resolve_private_prompt_directory,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare tutor routing and print only safe metadata. Private prompts are loaded "
            "later by an in-process provider, never through stdout."
        )
    )
    parser.add_argument("--request", required=True, help="Learner request used for role routing")
    parser.add_argument(
        "--role",
        default="auto",
        choices=("auto", *ROLE_IDS, *ROLE_ALIASES),
        help="Explicit role or shortcut alias; defaults to automatic routing",
    )
    parser.add_argument(
        "--private-dir",
        help="External prompt directory; otherwise use environment or saved configuration",
    )
    parser.add_argument(
        "--asked-field",
        action="append",
        default=[],
        choices=CLARIFICATION_FIELDS,
        help="Previously asked field to suppress; repeat for multiple fields",
    )
    parser.add_argument("--json", action="store_true", help="Print safe metadata as JSON")
    args = parser.parse_args(argv)

    try:
        turn = prepare_tutor_turn(
            args.request,
            role_id=args.role,
            asked_fields=args.asked_field,
        )
        try:
            resolve_private_prompt_directory(args.private_dir)
            private_configured = True
        except PromptAssetError:
            private_configured = False
    except (PromptAssetError, OSError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True))
        else:
            print(f"Tutor preparation failed: {exc}", file=sys.stderr)
        return 2

    manifest = {
        "ok": True,
        **turn.safe_manifest(),
        "private_prompt_configured": private_configured,
    }
    if args.json:
        print(json.dumps(manifest, ensure_ascii=True, indent=2))
        return 0

    print("Prepared tutor routing without exposing private prompt text.")
    print("  Role sequence: " + " -> ".join(turn.role_ids))
    print(f"  Private prompt configured: {'yes' if private_configured else 'no'}")
    if turn.clarification_questions:
        print("  Ask together before execution:")
        for question in turn.clarification_questions:
            print(f"    - {question}")
    else:
        print("  Clarification needed: no")
    return 0
