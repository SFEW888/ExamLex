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
            if not fname.endswith(".py"):  # __init__.py is already covered by .py suffix
                continue
            src_file = root_path / fname
            dst_file = dst / rel / fname
            try:
                if not dst_file.exists():
                    mismatches.append(f"missing: {dst_file}")
                    if not check_only:
                        _mirror_file(src_file, dst_file)
                elif not filecmp.cmp(str(src_file), str(dst_file), shallow=False):
                    mismatches.append(f"mismatch: {rel / fname}")
                    if not check_only:
                        _mirror_file(src_file, dst_file)
            except OSError as exc:
                mismatches.append(f"error: {rel / fname}: {exc}")

    return mismatches


def _mirror_file(src_file: Path, dst_file: Path) -> None:
    """Copy src_file to dst_file, creating parent directories as needed."""
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8")


def sync_cli(check_only: bool = False) -> list[str]:
    """Sync cli.py."""
    mismatches = []
    for fname in ("cli.py",):
        src = HYPHENATED / fname
        dst = UNDERSCORED / fname
        if not src.exists():
            continue
        try:
            if not dst.exists():
                mismatches.append(f"missing: {dst}")
                if not check_only:
                    _mirror_file(src, dst)
            elif not filecmp.cmp(str(src), str(dst), shallow=False):
                mismatches.append(f"mismatch: {fname}")
                if not check_only:
                    _mirror_file(src, dst)
        except OSError as exc:
            mismatches.append(f"error: {fname}: {exc}")
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
            return 1
        errors = [m for m in all_mismatches if m.startswith("error:")]
        print(f"\n{len(all_mismatches) - len(errors)} files synced.")
        if errors:
            print(f"{len(errors)} errors — see above.")
            return 1
        return 0
    else:
        print("Mirror is in sync.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
