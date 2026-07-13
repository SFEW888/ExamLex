from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO


DEFAULT_EXCLUDES = [".env*", "*private*"]
HASH_CHUNK_BYTES = 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10_000
MAX_ARCHIVE_MEMBER_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_BACKUP_METADATA_BYTES = 1024 * 1024


def create_backup(data_dir: str | Path, output: str | Path, exclude: list[str] | None = None) -> dict[str, Any]:
    source = Path(data_dir).resolve()
    if not source.is_dir():
        raise ValueError("--data-dir must be an existing directory")
    target = Path(output).expanduser().resolve(strict=False)
    if target.is_relative_to(source):
        raise ValueError("backup output must not be inside the source data directory")
    patterns = exclude or DEFAULT_EXCLUDES
    files = sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and not _excluded(path, source, patterns)
    )
    target.parent.mkdir(parents=True, exist_ok=True)

    if len(files) + 1 > MAX_ARCHIVE_MEMBERS:
        raise ValueError(f"backup member count exceeds limit {MAX_ARCHIVE_MEMBERS}")
    source_fingerprints = {path: _file_fingerprint(path) for path in files}
    source_sizes = {
        path: fingerprint[0]
        for path, fingerprint in source_fingerprints.items()
    }
    oversized = next(
        (path for path, size in source_sizes.items() if size > MAX_ARCHIVE_MEMBER_BYTES),
        None,
    )
    if oversized is not None:
        raise ValueError(
            f"backup member size exceeds limit {MAX_ARCHIVE_MEMBER_BYTES}: "
            f"{oversized.relative_to(source).as_posix()}"
        )
    total_size = sum(source_sizes.values())
    if total_size > MAX_ARCHIVE_TOTAL_BYTES:
        raise ValueError(f"backup total size exceeds limit {MAX_ARCHIVE_TOTAL_BYTES}")

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=target.parent,
            prefix=target.name + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
        with tarfile.open(temporary, "w:gz") as archive:
            file_hashes: dict[str, str] = {}
            for path in files:
                relative = path.relative_to(source).as_posix()
                file_hashes[relative] = _archive_file(
                    archive,
                    path,
                    relative,
                    source_fingerprints[path],
                )

            metadata: dict[str, Any] = {
                "backup_version": "1.2",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "total_files": len(files),
                "total_size_bytes": total_size,
                "exclude_patterns": patterns,
                "source_data_dir": str(data_dir),
                "contents": [path.relative_to(source).as_posix() for path in files],
                "file_hashes": file_hashes,
            }
            encoded = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")
            if len(encoded) > MAX_BACKUP_METADATA_BYTES:
                raise ValueError(
                    f"backup metadata size exceeds limit {MAX_BACKUP_METADATA_BYTES}"
                )
            info = tarfile.TarInfo("backup-metadata.json")
            info.size = len(encoded)
            archive.addfile(info, io.BytesIO(encoded))

        metadata["checksum_sha256"] = _sha256_file(temporary)
        verification = verify_backup(
            temporary,
            expected_checksum=metadata["checksum_sha256"],
        )
        if not verification["verified"]:
            raise ValueError(
                "source data changed during backup: "
                + ", ".join(verification["mismatches"])
            )
        os.replace(temporary, target)
        temporary = None
        _write_checksum_sidecar(target, metadata["checksum_sha256"])
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return metadata


def verify_backup(input_path: str | Path, *, expected_checksum: str | None = None) -> dict[str, Any]:
    """Verify archive membership, member digests, and an external archive digest."""
    path = Path(input_path)
    with tarfile.open(path, "r:gz") as archive:
        members = _validated_archive_members(archive)
        metadata = _metadata(archive)
        expected = metadata.get("file_hashes")
        if not isinstance(expected, dict):
            return {"verified": False, "legacy": True, "checked_files": 0, "mismatches": []}
        mismatches: list[str] = []
        if sum(member.name == "backup-metadata.json" for member in members) != 1:
            mismatches.append("backup-metadata.json")
        content_members = [member for member in members if member.name != "backup-metadata.json"]
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
            if stream is None or _sha256_stream(stream) != digest:
                mismatches.append(name)
        for name in actual_names:
            if name not in expected_names:
                mismatches.append(name)
        actual_checksum = _sha256_file(path)
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
        members = _validated_archive_members(archive)
        metadata = _metadata(archive)
        metadata["archive_members"] = [member.name for member in members]
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
    if destination.exists() and not destination.is_dir():
        raise ValueError("--data-dir must be a directory")
    restored: list[str] = []
    skipped: list[str] = []
    verification = verify_backup(input_path, expected_checksum=expected_checksum)
    if not verification["legacy"] and not verification["verified"]:
        raise ValueError(f"backup integrity verification failed: {', '.join(verification['mismatches'])}")
    if not verification["legacy"] and not expected_checksum:
        raise ValueError("expected checksum is required to restore a verified backup")
    with tarfile.open(input_path, "r:gz") as archive:
        members = _validated_archive_members(archive)
        _metadata(archive)
        for member in members:
            if member.name == "backup-metadata.json":
                continue
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination):
                raise ValueError(f"unsafe archive path: {member.name}")
            if target.exists() and not force:
                skipped.append(member.name)
                continue
            restored.append(member.name)
        if dry_run:
            return {
                "restored": restored,
                "skipped": skipped,
                "dry_run": True,
                "verification": verification,
            }

        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(
                dir=destination.parent,
                prefix=f".{destination.name}.restore-",
            )
        )
        rollback: Path | None = None
        try:
            if destination.exists():
                shutil.copytree(destination, staging, dirs_exist_ok=True)
            by_name = {member.name: member for member in members}
            for name in restored:
                member = by_name[name]
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"archive member cannot be read: {member.name}")
                target = (staging / member.name).resolve()
                if not target.is_relative_to(staging):
                    raise ValueError(f"unsafe archive path: {member.name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as output:
                    shutil.copyfileobj(stream, output, length=HASH_CHUNK_BYTES)

            if destination.exists():
                rollback = Path(
                    tempfile.mkdtemp(
                        dir=destination.parent,
                        prefix=f".{destination.name}.rollback-",
                    )
                )
                rollback.rmdir()
                os.replace(destination, rollback)
            try:
                os.replace(staging, destination)
            except OSError:
                if rollback is not None and rollback.exists() and not destination.exists():
                    os.replace(rollback, destination)
                    rollback = None
                raise
            if rollback is not None:
                shutil.rmtree(rollback)
                rollback = None
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            if rollback is not None and rollback.exists():
                if not destination.exists():
                    os.replace(rollback, destination)
                else:
                    shutil.rmtree(rollback, ignore_errors=True)
    return {"restored": restored, "skipped": skipped, "dry_run": dry_run, "verification": verification}


def _excluded(path: Path, root: Path, patterns: list[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(rel, pattern) for pattern in patterns)


def _checksum_path(path: Path) -> Path:
    return Path(f"{path}.sha256")


def _write_checksum_sidecar(path: Path, checksum: str) -> None:
    sidecar = _checksum_path(path)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="ascii",
            dir=sidecar.parent,
            prefix=sidecar.name + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(checksum + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, sidecar)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _read_checksum_sidecar(path: Path) -> str | None:
    try:
        return _checksum_path(path).read_text(encoding="ascii").strip()
    except OSError:
        return None


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _sha256_stream(stream) -> str:
    digest = hashlib.sha256()
    while True:
        chunk = stream.read(HASH_CHUNK_BYTES)
        if not chunk:
            return digest.hexdigest()
        digest.update(chunk)


def _sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return _sha256_stream(stream)


class _HashingReader:
    """Hash a source file while tarfile consumes it in bounded chunks."""

    def __init__(self, stream: BinaryIO):
        self._stream = stream
        self._digest = hashlib.sha256()
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self._stream.read(size)
        self._digest.update(chunk)
        self.bytes_read += len(chunk)
        return chunk

    def hexdigest(self) -> str:
        return self._digest.hexdigest()


def _file_fingerprint(path: Path) -> tuple[int, int, int]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _archive_file(
    archive: tarfile.TarFile,
    path: Path,
    arcname: str,
    expected_fingerprint: tuple[int, int, int],
) -> str:
    """Archive one regular file while hashing and checking snapshot stability."""
    if path.is_symlink():
        raise ValueError(f"unsafe backup source: {arcname}")
    before = _file_fingerprint(path)
    if before != expected_fingerprint:
        raise ValueError(f"source data changed during backup: {arcname}")
    info = archive.gettarinfo(str(path), arcname=arcname)
    if not info.isfile():
        raise ValueError(f"unsafe backup source: {arcname}")
    with path.open("rb") as source_stream:
        hashing_stream = _HashingReader(source_stream)
        archive.addfile(info, hashing_stream)
    after = _file_fingerprint(path)
    if before != after or hashing_stream.bytes_read != info.size:
        raise ValueError(f"source data changed during backup: {arcname}")
    return hashing_stream.hexdigest()


def _validated_archive_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members: list[tarfile.TarInfo] = []
    total_size = 0
    for member in archive:
        members.append(member)
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise ValueError(
                f"backup member count exceeds limit {MAX_ARCHIVE_MEMBERS}"
            )
        if not member.isfile():
            raise ValueError(f"unsafe archive member: {member.name}")
        if member.size < 0:
            raise ValueError(f"unsafe archive member size: {member.name}")
        if "\\" in member.name:
            raise ValueError(f"unsafe archive path: {member.name}")
        member_path = Path(member.name)
        if member_path.is_absolute() or ".." in member_path.parts:
            raise ValueError(f"unsafe archive path: {member.name}")
        if member.name == "backup-metadata.json":
            if member.size > MAX_BACKUP_METADATA_BYTES:
                raise ValueError(
                    f"backup metadata size exceeds limit {MAX_BACKUP_METADATA_BYTES}"
                )
            continue
        if member.size > MAX_ARCHIVE_MEMBER_BYTES:
            raise ValueError(
                f"backup member size exceeds limit {MAX_ARCHIVE_MEMBER_BYTES}: {member.name}"
            )
        total_size += member.size
        if total_size > MAX_ARCHIVE_TOTAL_BYTES:
            raise ValueError(
                f"backup total size exceeds limit {MAX_ARCHIVE_TOTAL_BYTES}"
            )
    return members


def _metadata(archive: tarfile.TarFile) -> dict[str, Any]:
    try:
        member = archive.getmember("backup-metadata.json")
    except KeyError as exc:
        raise ValueError("backup is missing backup-metadata.json") from exc
    extracted = archive.extractfile(member)
    if extracted is None:
        raise ValueError("backup metadata cannot be read")
    payload = bytearray()
    while len(payload) <= MAX_BACKUP_METADATA_BYTES:
        chunk = extracted.read(min(HASH_CHUNK_BYTES, MAX_BACKUP_METADATA_BYTES + 1 - len(payload)))
        if not chunk:
            break
        payload.extend(chunk)
    if len(payload) > MAX_BACKUP_METADATA_BYTES:
        raise ValueError(
            f"backup metadata size exceeds limit {MAX_BACKUP_METADATA_BYTES}"
        )
    data = json.loads(bytes(payload).decode("utf-8"))
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
