#!/usr/bin/env python3
"""Sync hyphenated skill directory (english-exam-ai-tutor) to
underscored mirror (english_exam_ai_tutor).

Usage: python sync_mirror.py [--check]
  --check   Only report mismatches, don't fix
"""

import filecmp
import os
import sys
from pathlib import Path


HYPHENATED = Path("skills/english-exam-ai-tutor")
UNDERSCORED = Path("skills/english_exam_ai_tutor")


def sync_scripts(check_only: bool = False) -> list[str]:
    """Sync scripts/ directory. Returns list of mismatched files."""
    src = HYPHENATED / "scripts"
    dst = UNDERSCORED / "scripts"
    mismatches = []

    for root, _dirs, files in os.walk(src):
        root_path = Path(root)
        rel = root_path.relative_to(src)
        for fname in files:
            if not fname.endswith(".py") and fname != "__init__.py":
                continue
            src_file = root_path / fname
            dst_file = dst / rel / fname
            if not dst_file.exists():
                mismatches.append(f"missing: {dst_file}")
                if not check_only:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    dst_file.write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8")
            elif not filecmp.cmp(str(src_file), str(dst_file), shallow=False):
                mismatches.append(f"mismatch: {rel / fname}")
                if not check_only:
                    dst_file.write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8")

    return mismatches


def sync_cli(check_only: bool = False) -> list[str]:
    """Sync cli.py and __main__.py."""
    mismatches = []
    for fname in ("cli.py",):
        src = HYPHENATED / fname
        dst = UNDERSCORED / fname
        if not src.exists() or not dst.exists():
            continue
        if not filecmp.cmp(str(src), str(dst), shallow=False):
            mismatches.append(f"mismatch: {fname}")
            if not check_only:
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return mismatches


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    check_only = "--check" in args

    all_mismatches = []
    all_mismatches.extend(sync_scripts(check_only=check_only))
    all_mismatches.extend(sync_cli(check_only=check_only))

    if all_mismatches:
        for m in all_mismatches:
            print(f"  {m}")
        if check_only:
            print(f"\n{len(all_mismatches)} mismatches found. Run without --check to fix.")
        else:
            print(f"\n{len(all_mismatches)} files synced.")
        return 1
    else:
        print("Mirror is in sync.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
