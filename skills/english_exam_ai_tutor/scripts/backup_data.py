from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDES = [".env*", "*private*"]


def create_backup(data_dir: str | Path, output: str | Path, exclude: list[str] | None = None) -> dict[str, Any]:
    source = Path(data_dir).resolve()
    if not source.is_dir():
        raise ValueError("--data-dir must be an existing directory")
    patterns = exclude or DEFAULT_EXCLUDES
    files = [path for path in source.rglob("*") if path.is_file() and not _excluded(path, source, patterns)]
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, Any] = {
        "backup_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(files),
        "total_size_bytes": sum(path.stat().st_size for path in files),
        "exclude_patterns": patterns,
        "source_data_dir": str(data_dir),
        "contents": [path.relative_to(source).as_posix() for path in files],
    }

    with tarfile.open(target, "w:gz") as archive:
        encoded = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")
        info = tarfile.TarInfo("backup-metadata.json")
        info.size = len(encoded)
        archive.addfile(info, io.BytesIO(encoded))
        for path in files:
            archive.add(path, arcname=path.relative_to(source).as_posix())

    metadata["checksum_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    return metadata


def list_backup(input_path: str | Path) -> dict[str, Any]:
    with tarfile.open(input_path, "r:gz") as archive:
        metadata = _metadata(archive)
        metadata["archive_members"] = [member.name for member in archive.getmembers()]
        return metadata


def restore_backup(
    input_path: str | Path,
    data_dir: str | Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    destination = Path(data_dir).resolve()
    restored: list[str] = []
    skipped: list[str] = []
    with tarfile.open(input_path, "r:gz") as archive:
        _metadata(archive)
        for member in archive.getmembers():
            if member.name == "backup-metadata.json":
                continue
            target = (destination / member.name).resolve()
            if not str(target).startswith(str(destination)):
                raise ValueError(f"unsafe archive path: {member.name}")
            if target.exists() and not force:
                skipped.append(member.name)
                continue
            restored.append(member.name)
            if not dry_run:
                archive.extract(member, destination)
    return {"restored": restored, "skipped": skipped, "dry_run": dry_run}


def _excluded(path: Path, root: Path, patterns: list[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(rel, pattern) for pattern in patterns)


def _metadata(archive: tarfile.TarFile) -> dict[str, Any]:
    try:
        member = archive.getmember("backup-metadata.json")
    except KeyError as exc:
        raise ValueError("backup is missing backup-metadata.json") from exc
    extracted = archive.extractfile(member)
    if extracted is None:
        raise ValueError("backup metadata cannot be read")
    data = json.loads(extracted.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("backup metadata must be an object")
    return data


def backup_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backup learner data to tar.gz.")
    parser.add_argument("data_dir_pos", nargs="?", help="Directory to back up.")
    parser.add_argument("--data-dir", help="Directory to back up.")
    parser.add_argument("--output", help="Output tar.gz path.")
    parser.add_argument("--exclude", help="Comma-separated glob patterns.")
    parser.add_argument("--list", dest="list_path", help="List backup contents instead of creating a backup.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.list_path:
        result = list_backup(args.list_path)
    else:
        data_dir = args.data_dir or args.data_dir_pos
        if not data_dir:
            parser.error("--data-dir is required unless --list is used")
        output = args.output or f"backup-{datetime.now(timezone.utc).date().isoformat()}.tar.gz"
        exclude = [item.strip() for item in args.exclude.split(",") if item.strip()] if args.exclude else None
        result = create_backup(data_dir, output, exclude=exclude)
        result["output"] = output

    if args.json:
        _print_json(result)
    else:
        _print_json(result)
    return 0


def restore_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore learner data from tar.gz.")
    parser.add_argument("input_pos", nargs="?", help="Input tar.gz backup path.")
    parser.add_argument("data_dir_pos", nargs="?", help="Destination data directory.")
    parser.add_argument("--input", help="Input tar.gz backup path.")
    parser.add_argument("--data-dir", help="Destination data directory.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    input_path = args.input or args.input_pos
    data_dir = args.data_dir or args.data_dir_pos
    if not input_path:
        parser.error("--input or input positional argument is required")
    if not data_dir:
        parser.error("--data-dir or data directory positional argument is required")
    result = restore_backup(input_path, data_dir, force=args.force, dry_run=args.dry_run)
    _print_json(result)
    return 0


def _print_json(data: Any) -> None:
    sys.stdout.buffer.write((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
