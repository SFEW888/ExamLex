#!/usr/bin/env python3
"""Sync the portable ExamLex Skill into the importable ExamLex package.

Usage: python sync_mirror.py [--check]
  --check   Only report mismatches, don't fix
"""

import filecmp
import shutil
import sys
from pathlib import Path


SKILL_ROOT = Path("skills/examlex")
PACKAGE_ROOT = Path("examlex")


def sync_scripts(check_only: bool = False) -> list[str]:
    """Sync scripts/ directory. Returns list of mismatched files."""
    src = SKILL_ROOT / "scripts"
    dst = PACKAGE_ROOT / "scripts"
    source_files = _python_files(src)
    target_files = _python_files(dst)
    mismatches: list[str] = []

    for relative, src_file in sorted(source_files.items()):
        dst_file = dst / relative
        try:
            if not dst_file.exists():
                mismatches.append(f"missing: {dst_file}")
                if not check_only:
                    _mirror_file(src_file, dst_file)
            elif not filecmp.cmp(str(src_file), str(dst_file), shallow=False):
                mismatches.append(f"mismatch: {relative}")
                if not check_only:
                    _mirror_file(src_file, dst_file)
        except OSError as exc:
            mismatches.append(f"error: {relative}: {exc}")

    for relative, dst_file in sorted(target_files.items()):
        if relative in source_files:
            continue
        mismatches.append(f"extra script: {relative}")
        if not check_only:
            dst_file.unlink()

    if not check_only and dst.exists():
        _remove_empty_directories(dst)

    return mismatches


def _python_files(root: Path) -> dict[Path, Path]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root): path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    }


def _remove_empty_directories(root: Path) -> None:
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass


def _mirror_file(src_file: Path, dst_file: Path) -> None:
    """Copy src_file to dst_file, creating parent directories as needed."""
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dst_file)


def sync_cli(check_only: bool = False) -> list[str]:
    """Sync CLI entry points."""
    mismatches = []
    for fname in ("cli.py", "run.py"):
        src = SKILL_ROOT / fname
        dst = PACKAGE_ROOT / fname
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


def _resource_files(root: Path) -> dict[Path, Path]:
    """Return relative paths mapped to resource files below *root*."""
    if not root.exists():
        return {}
    return {
        path.relative_to(root): path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def _mirror_binary(src_file: Path, dst_file: Path) -> None:
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dst_file)


def _sync_resource_tree(directory_name: str, check_only: bool) -> list[str]:
    source_root = SKILL_ROOT / directory_name
    target_root = PACKAGE_ROOT / directory_name
    source_files = _resource_files(source_root)
    target_files = _resource_files(target_root)
    mismatches: list[str] = []

    for relative, source in sorted(source_files.items()):
        target = target_root / relative
        if not target.exists() or not filecmp.cmp(str(source), str(target), shallow=False):
            mismatches.append(
                f"resource mismatch: {directory_name}/{relative.as_posix()}"
            )
            if not check_only:
                _mirror_binary(source, target)

    for relative, target in sorted(target_files.items()):
        if relative not in source_files:
            mismatches.append(
                f"extra resource: {directory_name}/{relative.as_posix()}"
            )
            if not check_only:
                target.unlink()

    if not check_only and target_root.exists():
        _remove_empty_directories(target_root)

    return mismatches


def sync_resources(check_only: bool = False) -> list[str]:
    """Sync SKILL.md, assets, and references into the importable package."""
    mismatches: list[str] = []

    skill_source = SKILL_ROOT / "SKILL.md"
    skill_target = PACKAGE_ROOT / "SKILL.md"
    if not skill_target.exists() or not filecmp.cmp(
        str(skill_source), str(skill_target), shallow=False
    ):
        mismatches.append("resource mismatch: SKILL.md")
        if not check_only:
            _mirror_binary(skill_source, skill_target)

    for directory_name in ("assets", "references"):
        mismatches.extend(_sync_resource_tree(directory_name, check_only))

    return mismatches


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    check_only = "--check" in args

    all_mismatches = []
    all_mismatches.extend(sync_scripts(check_only=check_only))
    all_mismatches.extend(sync_cli(check_only=check_only))
    all_mismatches.extend(sync_resources(check_only=check_only))

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
