#!/usr/bin/env python3
"""Preview or archive stale ExamLex pipeline sessions."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from .config import TutorConfig
    from .file_lock import exclusive_file_lock
    from .session import session_lock_target
except ImportError:
    from config import TutorConfig  # type: ignore[no-redef]
    from file_lock import exclusive_file_lock  # type: ignore[no-redef]
    from session import session_lock_target  # type: ignore[no-redef]


TERMINAL_STAGES = {"committed", "failed"}
PRUNABLE_STAGES = {"committed"}
PRUNABLE_FILE_NAMES = {"full_text.txt", "post_caption.txt", "transcript.txt"}
PRUNABLE_DIRECTORY_NAMES = {"chapters"}


@dataclass(frozen=True)
class StaleSession:
    session_id: str
    stage: str
    updated_at: str
    age_hours: float
    session_dir: Path


@dataclass
class CleanupResult:
    archived: list[str]
    failures: list[str]


@dataclass
class PruneResult:
    pruned: list[str]
    bytes_reclaimed: int
    failures: list[str]


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _parse_updated_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def find_stale_sessions(
    sessions_root: Path,
    older_than_hours: float,
    now: datetime | None = None,
    stages: set[str] | None = None,
) -> list[StaleSession]:
    """Return sessions in the requested stages that exceed the age threshold.

    The default preserves the original behavior and returns only non-terminal
    sessions. Passing ``stages`` selects an explicit set instead.
    """
    if older_than_hours <= 0:
        raise ValueError("older_than_hours must be positive")

    root = Path(sessions_root).resolve()
    if not root.exists():
        return []
    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    candidates: list[StaleSession] = []

    for state_file in sorted(root.rglob("pipeline_state.json")):
        session_dir = state_file.parent.resolve()
        if not _is_within(session_dir, root):
            continue
        relative_session = session_dir.relative_to(root)
        if len(relative_session.parts) != 2:
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        stage = str(state.get("stage", "unknown"))
        if stages is None and stage in TERMINAL_STAGES:
            continue
        if stages is not None and stage not in stages:
            continue
        updated = _parse_updated_at(state.get("updated_at"))
        if updated is None:
            continue
        age_hours = (current_time - updated).total_seconds() / 3600
        if age_hours <= older_than_hours:
            continue
        candidates.append(
            StaleSession(
                session_id=str(state.get("session_id") or session_dir.name),
                stage=stage,
                updated_at=updated.isoformat(),
                age_hours=age_hours,
                session_dir=session_dir,
            )
        )

    return candidates


def _is_prunable_artifact(path: Path) -> bool:
    name = path.name
    return (
        name in PRUNABLE_FILE_NAMES
        or name in PRUNABLE_DIRECTORY_NAMES
        or name.startswith("audio.")
        or (name.startswith("transcript.") and name.endswith(".json"))
    )


def _path_size(path: Path) -> int:
    if path.is_symlink():
        return path.lstat().st_size
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, directories, files in os.walk(path, followlinks=False):
        root_path = Path(root)
        for directory in directories:
            candidate = root_path / directory
            if candidate.is_symlink():
                total += candidate.lstat().st_size
        for file_name in files:
            candidate = root_path / file_name
            try:
                total += candidate.lstat().st_size
            except OSError:
                continue
    return total


def prune_terminal_artifacts(
    candidates: list[StaleSession],
    sessions_root: Path,
) -> PruneResult:
    """Remove reproducible bulky artifacts from stale committed sessions."""
    source_root = Path(sessions_root).resolve()
    pruned: list[str] = []
    failures: list[str] = []
    bytes_reclaimed = 0

    for candidate in candidates:
        source = candidate.session_dir.resolve()
        if not _is_within(source, source_root):
            failures.append(f"source is outside sessions root: {source}")
            continue
        relative_source = source.relative_to(source_root)
        if len(relative_source.parts) != 2:
            failures.append(f"source does not match date/session layout: {source}")
            continue
        try:
            with exclusive_file_lock(session_lock_target(source)):
                state_path = source / "pipeline_state.json"
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
                    failures.append(f"session changed before prune: {source}: {exc}")
                    continue
                current_stage = str(state.get("stage", "unknown"))
                current_updated = _parse_updated_at(state.get("updated_at"))
                if (
                    current_stage not in PRUNABLE_STAGES
                    or current_stage != candidate.stage
                    or current_updated is None
                    or current_updated.isoformat() != candidate.updated_at
                ):
                    failures.append(f"session changed before prune: {source}")
                    continue

                for artifact in sorted(source.iterdir(), key=lambda item: item.name):
                    if not _is_prunable_artifact(artifact):
                        continue
                    resolved_parent = artifact.parent.resolve()
                    if resolved_parent != source:
                        failures.append(f"artifact is outside session directory: {artifact}")
                        continue
                    artifact_size = _path_size(artifact)
                    if artifact.is_dir() and not artifact.is_symlink():
                        shutil.rmtree(artifact)
                    else:
                        artifact.unlink()
                    bytes_reclaimed += artifact_size
                    pruned.append(str(artifact))
        except (OSError, TimeoutError) as exc:
            failures.append(f"failed to prune {source}: {exc}")

    return PruneResult(
        pruned=pruned,
        bytes_reclaimed=bytes_reclaimed,
        failures=failures,
    )


def archive_stale_sessions(
    candidates: list[StaleSession],
    sessions_root: Path,
    archive_root: Path | None = None,
) -> CleanupResult:
    """Move stale sessions to a sibling archive without overwriting data."""
    source_root = Path(sessions_root).resolve()
    target_root = Path(archive_root or source_root.parent / "session-archive").resolve()
    archived: list[str] = []
    failures: list[str] = []

    for candidate in candidates:
        source = candidate.session_dir.resolve()
        if not _is_within(source, source_root):
            failures.append(f"source is outside sessions root: {source}")
            continue
        relative_source = source.relative_to(source_root)
        if len(relative_source.parts) != 2:
            failures.append(f"source does not match date/session layout: {source}")
            continue
        date_name = source.parent.name
        target = (target_root / date_name / source.name).resolve()
        if not _is_within(target, target_root):
            failures.append(f"archive target is outside archive root: {target}")
            continue
        moved = False
        try:
            with exclusive_file_lock(session_lock_target(source)):
                state_path = source / "pipeline_state.json"
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
                    failures.append(f"session changed before archive: {source}: {exc}")
                    continue
                current_stage = str(state.get("stage", "unknown"))
                current_updated = _parse_updated_at(state.get("updated_at"))
                if (
                    current_stage in TERMINAL_STAGES
                    or current_stage != candidate.stage
                    or current_updated is None
                    or current_updated.isoformat() != candidate.updated_at
                ):
                    failures.append(f"session changed before archive: {source}")
                    continue
                if target.exists():
                    failures.append(f"archive target already exists: {target}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))
                archived.append(str(target))
                moved = True
        except (OSError, TimeoutError) as exc:
            failures.append(f"failed to archive {source}: {exc}")
        if moved:
            try:
                source.parent.rmdir()
            except OSError:
                pass

    return CleanupResult(archived=archived, failures=failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="examlex sessions-cleanup",
        description="Preview or archive stale ExamLex sessions.",
    )
    parser.add_argument("--sessions-root", type=Path, help="Session root to inspect.")
    parser.add_argument("--archive-root", type=Path, help="Archive root; defaults to a sibling directory.")
    parser.add_argument("--older-than-hours", type=float, default=24.0)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the selected archive or prune operation; default is dry-run.",
    )
    parser.add_argument(
        "--prune-terminal-artifacts",
        action="store_true",
        help=(
            "Target stale committed sessions and remove reproducible full text, "
            "audio, transcripts, and chapter extracts. Default is dry-run."
        ),
    )
    args = parser.parse_args(argv)

    if args.older_than_hours <= 0:
        parser.error("--older-than-hours must be positive")

    sessions_root = (args.sessions_root or TutorConfig().sessions_root).resolve()
    archive_root = (args.archive_root or sessions_root.parent / "session-archive").resolve()
    selected_stages = PRUNABLE_STAGES if args.prune_terminal_artifacts else None
    candidates = find_stale_sessions(
        sessions_root,
        args.older_than_hours,
        stages=selected_stages,
    )
    result = CleanupResult(archived=[], failures=[])
    prune_result = PruneResult(pruned=[], bytes_reclaimed=0, failures=[])
    if args.apply:
        if args.prune_terminal_artifacts:
            prune_result = prune_terminal_artifacts(candidates, sessions_root)
        else:
            result = archive_stale_sessions(candidates, sessions_root, archive_root)

    payload = {
        "applied": args.apply,
        "operation": "prune-terminal-artifacts" if args.prune_terminal_artifacts else "archive",
        "sessions_root": str(sessions_root),
        "archive_root": str(archive_root),
        "older_than_hours": args.older_than_hours,
        "candidate_count": len(candidates),
        "candidates": [
            {**asdict(candidate), "session_dir": str(candidate.session_dir)}
            for candidate in candidates
        ],
        "archived": result.archived,
        "pruned": prune_result.pruned,
        "bytes_reclaimed": prune_result.bytes_reclaimed,
        "failures": result.failures + prune_result.failures,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
