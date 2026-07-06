from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


SKILL_NAME = "english-exam-ai-tutor"
SKILL_ALIASES = (
    "learning-planner",
    "vocabulary-builder",
    "reading-navigator",
    "structure-planner",
    "grammar-corrector",
    "polish-wizard",
    "scenario-dialog",
    "culture-guide",
)
DEFAULT_SKILL_NAMES = (SKILL_NAME, *SKILL_ALIASES)


@dataclass(frozen=True)
class InstallResult:
    source: Path
    dest: Path
    target: Path
    dry_run: bool
    copied: bool


def default_source() -> Path:
    return Path(__file__).resolve().parents[1] / "skills"


def default_dest() -> Path:
    return Path.home() / ".claude" / "skills"


def ignore_cache_files(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name == "__pycache__" or name.endswith(".pyc"):
            ignored.add(name)
    return ignored


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def reject_unsafe_target(source_path: Path, target: Path) -> None:
    resolved_source = source_path.resolve()
    resolved_target = target.resolve(strict=False)

    if resolved_target == resolved_source:
        raise ValueError(f"Unsafe install target aliases the source: {target}")
    if path_is_relative_to(resolved_target, resolved_source):
        raise ValueError(f"Unsafe install target is inside the source: {target}")
    if path_is_relative_to(resolved_source, resolved_target):
        raise ValueError(f"Unsafe install target contains the source: {target}")


def install_skill(
    source: str | Path | None = None,
    dest: str | Path | None = None,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> InstallResult:
    source_path = Path(source) if source is not None else default_source()
    dest_path = Path(dest) if dest is not None else default_dest()
    source_path = source_path.expanduser().resolve()
    dest_path = dest_path.expanduser()
    target = dest_path / source_path.name

    if not source_path.is_dir():
        raise FileNotFoundError(f"Skill source does not exist: {source_path}")
    reject_unsafe_target(source_path, target)
    if target.exists() and not force:
        raise FileExistsError(f"Destination exists: {target}. Re-run with --force to overwrite it.")

    if dry_run:
        return InstallResult(source_path, dest_path, target, True, False)

    dest_path.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source_path, target, ignore=ignore_cache_files)
    return InstallResult(source_path, dest_path, target, False, True)


def is_skill_dir(path: Path) -> bool:
    return path.is_dir() and (path / "SKILL.md").is_file()


def discover_skill_sources(source: str | Path | None = None) -> list[Path]:
    source_path = Path(source) if source is not None else default_source()
    source_path = source_path.expanduser().resolve()
    if is_skill_dir(source_path):
        return [source_path]
    if not source_path.is_dir():
        raise FileNotFoundError(f"Skill source does not exist: {source_path}")

    sources: list[Path] = []
    for name in DEFAULT_SKILL_NAMES:
        candidate = source_path / name
        if is_skill_dir(candidate):
            sources.append(candidate)
    if not sources:
        raise FileNotFoundError(f"No Skill directories with SKILL.md found in: {source_path}")
    return sources


def install_skills(
    source: str | Path | None = None,
    dest: str | Path | None = None,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> list[InstallResult]:
    return [
        install_skill(skill_source, dest, dry_run=dry_run, force=force)
        for skill_source in discover_skill_sources(source)
    ]


def _result_dict(result: InstallResult) -> dict[str, str | bool]:
    data = asdict(result)
    return {key: str(value) if isinstance(value, Path) else value for key, value in data.items()}


def result_to_json(result: InstallResult | list[InstallResult]) -> str:
    if isinstance(result, list):
        if len(result) == 1:
            return json.dumps(_result_dict(result[0]))
        return json.dumps({"skills": [_result_dict(item) for item in result]})
    return json.dumps(_result_dict(result))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install the English Exam AI Tutor Skill for Claude Code.")
    parser.add_argument("--source", type=Path, default=default_source(), help="Skill directory or skills root to copy.")
    parser.add_argument("--dest", type=Path, default=default_dest(), help="Destination skills directory.")
    parser.add_argument("--dry-run", action="store_true", help="Report the copy target without writing files.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing installed Skill directory.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = install_skills(args.source, args.dest, dry_run=args.dry_run, force=args.force)
    except (FileNotFoundError, FileExistsError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"ERROR: {exc}")
        return 1

    if args.json:
        print(result_to_json(results))
    elif args.dry_run:
        for result in results:
            print(f"DRY RUN: would copy {result.source} to {result.target}")
    else:
        for result in results:
            print(f"Installed {result.source} to {result.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
