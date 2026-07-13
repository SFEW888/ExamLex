#!/usr/bin/env python3
"""Preview or archive stale ExamLex pipeline sessions."""

from __future__ import annotations

import argparse
import json
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
) -> list[StaleSession]:
    """Return non-terminal sessions older than the requested threshold."""
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
        if stage in TERMINAL_STAGES:
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
    parser.add_argument("--apply", action="store_true", help="Archive candidates; default is dry-run.")
    args = parser.parse_args(argv)

    if args.older_than_hours <= 0:
        parser.error("--older-than-hours must be positive")

    sessions_root = (args.sessions_root or TutorConfig().sessions_root).resolve()
    archive_root = (args.archive_root or sessions_root.parent / "session-archive").resolve()
    candidates = find_stale_sessions(sessions_root, args.older_than_hours)
    result = CleanupResult(archived=[], failures=[])
    if args.apply:
        result = archive_stale_sessions(candidates, sessions_root, archive_root)

    payload = {
        "applied": args.apply,
        "sessions_root": str(sessions_root),
        "archive_root": str(archive_root),
        "older_than_hours": args.older_than_hours,
        "candidate_count": len(candidates),
        "candidates": [
            {**asdict(candidate), "session_dir": str(candidate.session_dir)}
            for candidate in candidates
        ],
        "archived": result.archived,
        "failures": result.failures,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if result.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
