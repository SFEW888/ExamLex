from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from difflib import SequenceMatcher
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

try:
    from . import common
    from .file_lock import exclusive_file_lock
    from . import strategy_sqlite
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]
    from file_lock import exclusive_file_lock  # type: ignore[no-redef]
    import strategy_sqlite  # type: ignore[no-redef]


T = TypeVar("T")
_LOGGER = logging.getLogger(__name__)


def load_strategy_library(path: str | Path) -> dict[str, Any]:
    library_path = Path(path)
    if _is_sqlite_path(library_path):
        return strategy_sqlite.load_library(library_path)
    if library_path.exists():
        try:
            library = common.load_data(library_path)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"strategy library at {library_path} is corrupted - not valid JSON: {exc}"
            ) from exc
    else:
        library = {"strategies": []}
    if not isinstance(library, dict) or not isinstance(library.get("strategies"), list):
        raise ValueError("strategy library must contain a strategies list")
    return library


def _normalized_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.casefold().split())


def _sorted_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(sorted(item for item in value if isinstance(item, str)))


def _current_item(strategy: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy_id": str(strategy.get("strategy_id", "unknown")),
        "title": str(strategy.get("title", "")),
        "version": "current",
    }


def _candidate(
    reason: str,
    items: list[dict[str, Any]],
    *,
    requires_reference_check: bool = False,
    similarity: float | None = None,
) -> dict[str, Any]:
    serialized = json.dumps(
        [reason, [(item.get("strategy_id"), item.get("version")) for item in items]],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    visible_items = items[:5]
    result = {
        "candidate_id": hashlib.sha256(serialized).hexdigest()[:12],
        "reason": reason,
        "items": visible_items,
        "omitted_items": max(0, len(items) - len(visible_items)),
        "requires_reference_check": requires_reference_check,
    }
    if similarity is not None:
        result["similarity"] = round(similarity, 3)
    return result


def find_possible_duplicate_strategies(
    library: dict[str, Any],
    *,
    limit: int = 5,
    similarity_threshold: float = 0.88,
) -> list[dict[str, Any]]:
    """Return bounded, review-only duplicate candidates without modifying the library."""
    if limit <= 0:
        return []
    raw_entries = library.get("strategies", [])
    if not isinstance(raw_entries, list):
        raise ValueError("strategy library must contain a strategies list")
    entries = [entry for entry in raw_entries if isinstance(entry, dict)]
    candidates: list[dict[str, Any]] = []
    covered_current_groups: set[frozenset[str]] = set()

    def add_current_groups(reason: str, grouped: dict[object, list[dict[str, Any]]]) -> None:
        for group in grouped.values():
            if len(group) < 2:
                continue
            identifiers = frozenset(str(item.get("strategy_id", "unknown")) for item in group)
            if identifiers in covered_current_groups:
                continue
            covered_current_groups.add(identifiers)
            candidates.append(_candidate(reason, [_current_item(item) for item in group]))

    by_fingerprint: dict[object, list[dict[str, Any]]] = {}
    by_source_scope: dict[object, list[dict[str, Any]]] = {}
    by_content: dict[object, list[dict[str, Any]]] = {}
    by_title_scope: dict[object, list[dict[str, Any]]] = {}
    for entry in entries:
        provenance = entry.get("source_provenance")
        fingerprint = provenance.get("ingest_fingerprint") if isinstance(provenance, dict) else None
        if isinstance(fingerprint, str) and fingerprint:
            by_fingerprint.setdefault(fingerprint, []).append(entry)
        source_sha256 = provenance.get("sha256") if isinstance(provenance, dict) else None
        if isinstance(source_sha256, str) and source_sha256:
            source_scope = (
                source_sha256,
                _sorted_strings(entry.get("exam_types")),
                _sorted_strings(entry.get("modules")),
                entry.get("source_type"),
                entry.get("distillation_method"),
            )
            by_source_scope.setdefault(source_scope, []).append(entry)
        content = _normalized_text(entry.get("content"))
        if content:
            by_content.setdefault(content, []).append(entry)
        title = _normalized_text(entry.get("title"))
        if title:
            scope = (
                title,
                _sorted_strings(entry.get("exam_types")),
                _sorted_strings(entry.get("modules")),
            )
            by_title_scope.setdefault(scope, []).append(entry)

    add_current_groups("same_ingest_fingerprint", by_fingerprint)
    add_current_groups("same_source_hash_and_scope", by_source_scope)
    add_current_groups("same_normalized_content", by_content)
    add_current_groups("same_title_and_scope", by_title_scope)

    # The function returns candidates[:limit] and only ever appends candidates
    # (never reorders), so once the cheap exact-match groups above already fill
    # the quota, neither the O(n^2) approximate pass nor the revision pass can
    # change the sliced result. Skipping them keeps a pathological library
    # (many same-scope, near-identical strategies) from running up to 20k
    # SequenceMatcher comparisons this call cannot surface.
    if len(candidates) >= limit:
        return candidates[:limit]

    # Review-only approximate matching. Scope blocking and token overlap avoid
    # comparing every unrelated strategy in a growing library. Per-entry values
    # (normalized content, scope, tokens, length) are computed once here rather
    # than O(n^2) times inside the pair loop.
    prepared: list[tuple[dict[str, Any], str, tuple, set[str], int]] = []
    for entry in entries:
        content = _normalized_text(entry.get("content"))
        if not content:
            continue
        scope = (
            _sorted_strings(entry.get("exam_types")),
            _sorted_strings(entry.get("modules")),
        )
        tokens = set(content.split())
        prepared.append((entry, content, scope, tokens, len(content)))

    comparisons = 0
    for left_index in range(len(prepared)):
        if len(candidates) >= limit:
            break
        left, left_content, left_scope, left_tokens, left_len = prepared[left_index]
        for right_index in range(left_index + 1, len(prepared)):
            right, right_content, right_scope, right_tokens, right_len = prepared[right_index]
            if left_scope != right_scope:
                continue
            if right_content == left_content:
                continue
            union = left_tokens | right_tokens
            if not union or len(left_tokens & right_tokens) / len(union) < 0.55:
                continue
            comparisons += 1
            if comparisons > 20_000:
                break
            # Exact upper bound on SequenceMatcher.ratio() (difflib's
            # real_quick_ratio): a pair whose length ratio is already below the
            # threshold can never reach it, so skip building the matcher. Any
            # pair skipped here would fail the ratio() check below anyway, so
            # the recorded candidates are identical.
            if 2 * min(left_len, right_len) / (left_len + right_len) < similarity_threshold:
                continue
            similarity = SequenceMatcher(None, left_content, right_content, autojunk=False).ratio()
            if similarity < similarity_threshold:
                continue
            identifiers = frozenset(
                (str(left.get("strategy_id", "unknown")), str(right.get("strategy_id", "unknown")))
            )
            if identifiers in covered_current_groups:
                continue
            covered_current_groups.add(identifiers)
            candidates.append(
                _candidate(
                    "near_duplicate_content",
                    [_current_item(left), _current_item(right)],
                    similarity=similarity,
                    requires_reference_check=True,
                )
            )
            if len(candidates) >= limit:
                break
        if comparisons > 20_000:
            break

    if len(candidates) >= limit:
        return candidates[:limit]

    for entry in entries:
        if len(candidates) >= limit:
            break
        revisions = entry.get("revisions", [])
        if not isinstance(revisions, list):
            continue
        by_revision_content: dict[str, list[dict[str, Any]]] = {}
        for revision in revisions:
            if not isinstance(revision, dict):
                continue
            snapshot = revision.get("strategy")
            if not isinstance(snapshot, dict):
                continue
            content_key = _normalized_text(snapshot.get("content"))
            if not content_key and isinstance(revision.get("sha256"), str):
                content_key = f"sha256:{revision['sha256']}"
            if not content_key:
                continue
            by_revision_content.setdefault(content_key, []).append(
                {
                    "strategy_id": str(entry.get("strategy_id", "unknown")),
                    "title": str(snapshot.get("title", entry.get("title", ""))),
                    "version": revision.get("version", "unknown"),
                    "revision_sha256": revision.get("sha256"),
                }
            )
        for group in by_revision_content.values():
            if len(group) >= 2:
                candidates.append(
                    _candidate(
                        "same_content_across_revisions",
                        group,
                        requires_reference_check=True,
                    )
                )

    return candidates[:limit]


def format_duplicate_candidates(candidates: list[dict[str, Any]]) -> str:
    rendered: list[str] = []
    for candidate in candidates:
        labels = []
        for item in candidate.get("items", []):
            version = item.get("version")
            suffix = "" if version == "current" else f"@v{version}"
            labels.append(f"{item.get('strategy_id', 'unknown')}{suffix}")
        rendered.append(f"{candidate.get('reason')}: {', '.join(labels)}")
    return "; ".join(rendered)


def strategy_library_health(
    path: str | Path,
    *,
    warning_threshold_bytes: int,
    duplicate_limit: int = 5,
) -> dict[str, Any]:
    if warning_threshold_bytes <= 0:
        raise ValueError("warning_threshold_bytes must be positive")
    library_path = Path(path)
    size_bytes = _storage_size(library_path)
    threshold_reached = size_bytes >= warning_threshold_bytes
    library = load_strategy_library(library_path)
    candidates = (
        find_possible_duplicate_strategies(library, limit=duplicate_limit)
        if threshold_reached
        else []
    )
    return {
        "path": str(library_path),
        "size_bytes": size_bytes,
        "warning_threshold_bytes": warning_threshold_bytes,
        "threshold_reached": threshold_reached,
        "duplicate_candidates": candidates,
        "automatic_deletion": False,
        "storage_backend": "sqlite" if _is_sqlite_path(library_path) else "json",
    }


def warn_if_strategy_library_large(
    path: str | Path,
    *,
    warning_threshold_bytes: int,
    duplicate_limit: int = 5,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    report = strategy_library_health(
        path,
        warning_threshold_bytes=warning_threshold_bytes,
        duplicate_limit=duplicate_limit,
    )
    if report["threshold_reached"]:
        message = (
            "strategy library warning threshold reached: "
            f"{report['size_bytes']} >= {report['warning_threshold_bytes']} bytes; "
            "no strategies or revisions were deleted"
        )
        if report["duplicate_candidates"]:
            message += ". Possible duplicates for user review: " + format_duplicate_candidates(
                report["duplicate_candidates"]
            )
        message += f". Review with: examlex strategies --library {report['path']} --duplicates"
        (logger or _LOGGER).warning(message)
    return report


def warn_duplicate_candidates(
    candidates: list[dict[str, Any]],
    *,
    library_path: str | Path,
    logger: logging.Logger | None = None,
) -> None:
    if not candidates:
        return
    (logger or _LOGGER).warning(
        "possible duplicate strategy versions detected while writing %s; nothing was deleted: %s",
        library_path,
        format_duplicate_candidates(candidates),
    )


def mutate_strategy_library(
    path: str | Path,
    mutator: Callable[[dict[str, Any]], T],
) -> T:
    """Serialize a complete strategy-library read/modify/write transaction."""
    library_path = Path(path)
    if _is_sqlite_path(library_path):
        # Serialize the read/callback/write unit to prevent a lost update while
        # SQLite provides the atomic database transaction for the write.
        with exclusive_file_lock(library_path):
            return strategy_sqlite.mutate_library(library_path, mutator)
    with exclusive_file_lock(library_path):
        library = load_strategy_library(library_path)
        result = mutator(library)
        atomic_save_strategy_library(library, library_path)
        return result


def atomic_save_strategy_library(library: dict[str, Any], path: str | Path) -> Path:
    if not isinstance(library, dict) or not isinstance(library.get("strategies"), list):
        raise ValueError("strategy library must contain a strategies list")
    library_path = Path(path)
    if _is_sqlite_path(library_path):
        return strategy_sqlite.save_library(library, library_path)
    library_path.parent.mkdir(parents=True, exist_ok=True)
    if library_path.exists():
        backup = library_path.with_suffix(library_path.suffix + ".bak")
        _atomic_write_bytes(backup, library_path.read_bytes())
    payload = (
        json.dumps(library, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    _atomic_write_bytes(library_path, payload)
    return library_path


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _is_sqlite_path(path: Path) -> bool:
    return path.suffix.casefold() in {".db", ".sqlite", ".sqlite3"}


def _storage_size(path: Path) -> int:
    if not path.exists():
        return 0
    size = path.stat().st_size
    if _is_sqlite_path(path):
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(path) + suffix)
            if sidecar.exists():
                size += sidecar.stat().st_size
    return size
