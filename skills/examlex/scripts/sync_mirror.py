#!/usr/bin/env python3
"""Validate or repair the thin ``examlex`` compatibility package.

The canonical implementation and resources live under ``skills/examlex``.
The historical ``examlex`` import path contains only lightweight wrappers, so
tracked project size no longer doubles whenever a resource is added.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


SKILL_ROOT = Path("skills/examlex")
PACKAGE_ROOT = Path("examlex")

SCRIPT_INIT = '''"""Expose canonical Skill scripts under the historical ``examlex.scripts`` path."""\n\nfrom skills.examlex import scripts as _canonical_scripts\n\n__path__ = _canonical_scripts.__path__\n'''
CLI_WRAPPER = '''"""Compatibility entry point backed by the canonical Skill package."""\n\nfrom skills.examlex import cli as _canonical_cli\nfrom skills.examlex.cli import *  # noqa: F401,F403\nfrom skills.examlex.cli import main\n\n\ndef __getattr__(name: str):\n    """Forward private compatibility imports to the canonical CLI module."""\n    return getattr(_canonical_cli, name)\n\n\ndef __dir__() -> list[str]:\n    return sorted(set(globals()) | set(dir(_canonical_cli)))\n'''
RUN_WRAPPER = '''"""Compatibility runner backed by the canonical Skill package."""\n\nfrom skills.examlex.cli import main\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'''


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sync_scripts(check_only: bool = False) -> list[str]:
    """Keep only the namespace bridge below ``examlex/scripts``."""
    target = PACKAGE_ROOT / "scripts"
    mismatches: list[str] = []
    init = target / "__init__.py"
    if not init.exists() or init.read_text(encoding="utf-8") != SCRIPT_INIT:
        mismatches.append("thin wrapper mismatch: scripts/__init__.py")
        if not check_only:
            _write_text(init, SCRIPT_INIT)
    if target.exists():
        for path in sorted(target.rglob("*"), reverse=True):
            if path.is_file() and path != init and "__pycache__" not in path.parts:
                mismatches.append(
                    f"extra mirrored script: {path.relative_to(target).as_posix()}"
                )
                if not check_only:
                    path.unlink()
        if not check_only:
            for directory in sorted(
                (item for item in target.rglob("*") if item.is_dir()),
                key=lambda item: len(item.parts),
                reverse=True,
            ):
                try:
                    directory.rmdir()
                except OSError:
                    pass
    return mismatches


def sync_cli(check_only: bool = False) -> list[str]:
    mismatches: list[str] = []
    for filename, content in (("cli.py", CLI_WRAPPER), ("run.py", RUN_WRAPPER)):
        target = PACKAGE_ROOT / filename
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            mismatches.append(f"thin wrapper mismatch: {filename}")
            if not check_only:
                _write_text(target, content)
    return mismatches


def sync_resources(check_only: bool = False) -> list[str]:
    """Remove resource mirrors; wheel packaging reads the canonical Skill tree."""
    mismatches: list[str] = []
    targets = [PACKAGE_ROOT / "SKILL.md", PACKAGE_ROOT / "assets", PACKAGE_ROOT / "references"]
    for target in targets:
        if not target.exists():
            continue
        mismatches.append(f"duplicated package resource: {target.name}")
        if not check_only:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
    return mismatches


def main(argv: list[str] | None = None) -> int:
    check_only = "--check" in (argv or sys.argv[1:])
    mismatches = [
        *sync_scripts(check_only=check_only),
        *sync_cli(check_only=check_only),
        *sync_resources(check_only=check_only),
    ]
    if mismatches:
        for mismatch in mismatches:
            print(f"  {mismatch}")
        if check_only:
            print(f"\n{len(mismatches)} thin-package issues found.")
            return 1
        print(f"\n{len(mismatches)} thin-package issues repaired.")
        return 0
    print("Thin compatibility package is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
