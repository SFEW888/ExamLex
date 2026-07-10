from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import shutil
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

    file_hashes = {
        path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }
    metadata: dict[str, Any] = {
        "backup_version": "1.2",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(files),
        "total_size_bytes": sum(path.stat().st_size for path in files),
        "exclude_patterns": patterns,
        "source_data_dir": str(data_dir),
        "contents": [path.relative_to(source).as_posix() for path in files],
        "file_hashes": file_hashes,
    }

    with tarfile.open(target, "w:gz") as archive:
        encoded = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")
        info = tarfile.TarInfo("backup-metadata.json")
        info.size = len(encoded)
        archive.addfile(info, io.BytesIO(encoded))
        for path in files:
            archive.add(path, arcname=path.relative_to(source).as_posix())

    metadata["checksum_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    _checksum_path(target).write_text(metadata["checksum_sha256"] + "\n", encoding="ascii")
    return metadata


def verify_backup(input_path: str | Path, *, expected_checksum: str | None = None) -> dict[str, Any]:
    """Verify archive membership, member digests, and an external archive digest."""
    path = Path(input_path)
    with tarfile.open(path, "r:gz") as archive:
        metadata = _metadata(archive)
        expected = metadata.get("file_hashes")
        if not isinstance(expected, dict):
            return {"verified": False, "legacy": True, "checked_files": 0, "mismatches": []}
        mismatches: list[str] = []
        if sum(member.name == "backup-metadata.json" for member in archive.getmembers()) != 1:
            mismatches.append("backup-metadata.json")
        content_members = [member for member in archive.getmembers() if member.name != "backup-metadata.json"]
        actual_names: list[str] = []
        for member in content_members:
            if not member.isfile() or member.name in actual_names:
                mismatches.append(member.name)
                continue
            actual_names.append(member.name)
        expected_names = set()
        for name, digest in expected.items():
            if not isinstance(name, str) or not isinstance(digest, str) or not _is_sha256(digest):
                mismatches.append(str(name))
                continue
            expected_names.add(name)
            if name not in actual_names:
                mismatches.append(name)
                continue
            member = archive.getmember(name)
            stream = archive.extractfile(member)
            if stream is None or hashlib.sha256(stream.read()).hexdigest() != digest:
                mismatches.append(name)
        for name in actual_names:
            if name not in expected_names:
                mismatches.append(name)
        actual_checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        supplied_checksum = expected_checksum or _read_checksum_sidecar(path)
        if not supplied_checksum or not _is_sha256(supplied_checksum) or supplied_checksum != actual_checksum:
            mismatches.append("archive checksum")
        return {
            "verified": not mismatches,
            "legacy": False,
            "checked_files": len(expected),
            "mismatches": mismatches,
            "checksum_sha256": actual_checksum,
            "trusted_checksum": expected_checksum is not None,
        }


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
    expected_checksum: str | None = None,
) -> dict[str, Any]:
    destination = Path(data_dir).resolve()
    restored: list[str] = []
    skipped: list[str] = []
    verification = verify_backup(input_path, expected_checksum=expected_checksum)
    if not verification["legacy"] and not verification["verified"]:
        raise ValueError(f"backup integrity verification failed: {', '.join(verification['mismatches'])}")
    if not verification["legacy"] and not expected_checksum:
        raise ValueError("expected checksum is required to restore a verified backup")
    with tarfile.open(input_path, "r:gz") as archive:
        _metadata(archive)
        for member in archive.getmembers():
            if member.name == "backup-metadata.json":
                continue
            if not member.isfile():
                raise ValueError(f"unsafe archive member: {member.name}")
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination):
                raise ValueError(f"unsafe archive path: {member.name}")
            if target.exists() and not force:
                skipped.append(member.name)
                continue
            restored.append(member.name)
            if not dry_run:
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"archive member cannot be read: {member.name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as output:
                    shutil.copyfileobj(stream, output)
    return {"restored": restored, "skipped": skipped, "dry_run": dry_run, "verification": verification}


def _excluded(path: Path, root: Path, patterns: list[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(rel, pattern) for pattern in patterns)


def _checksum_path(path: Path) -> Path:
    return Path(f"{path}.sha256")


def _read_checksum_sidecar(path: Path) -> str | None:
    try:
        return _checksum_path(path).read_text(encoding="ascii").strip()
    except OSError:
        return None


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


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
        _print_human(result)
    return 0


def restore_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore learner data from tar.gz.")
    parser.add_argument("input_pos", nargs="?", help="Input tar.gz backup path.")
    parser.add_argument("data_dir_pos", nargs="?", help="Destination data directory.")
    parser.add_argument("--input", help="Input tar.gz backup path.")
    parser.add_argument("--data-dir", help="Destination data directory.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--expected-checksum", help="Checksum returned when the backup was created.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    input_path = args.input or args.input_pos
    data_dir = args.data_dir or args.data_dir_pos
    if not input_path:
        parser.error("--input or input positional argument is required")
    if not data_dir:
        parser.error("--data-dir or data directory positional argument is required")
    result = restore_backup(
        input_path, data_dir, force=args.force, dry_run=args.dry_run,
        expected_checksum=args.expected_checksum,
    )
    if args.json:
        _print_json(result)
    else:
        _print_human(result)
    return 0


def _print_json(data: Any) -> None:
    sys.stdout.buffer.write((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _print_human(data: Any) -> None:
    if not isinstance(data, dict):
        print(data)
        return
    for key, value in data.items():
        if isinstance(value, list):
            print(f"{key}: {len(value)}")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"{key}: {value}")
