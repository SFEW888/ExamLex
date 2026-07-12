from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

try:
    from . import common
    from .file_lock import exclusive_file_lock
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]
    from file_lock import exclusive_file_lock  # type: ignore[no-redef]


T = TypeVar("T")


def load_strategy_library(path: str | Path) -> dict[str, Any]:
    library_path = Path(path)
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


def mutate_strategy_library(
    path: str | Path,
    mutator: Callable[[dict[str, Any]], T],
) -> T:
    """Serialize a complete strategy-library read/modify/write transaction."""
    library_path = Path(path)
    with exclusive_file_lock(library_path):
        library = load_strategy_library(library_path)
        result = mutator(library)
        atomic_save_strategy_library(library, library_path)
        return result


def atomic_save_strategy_library(library: dict[str, Any], path: str | Path) -> Path:
    if not isinstance(library, dict) or not isinstance(library.get("strategies"), list):
        raise ValueError("strategy library must contain a strategies list")
    library_path = Path(path)
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
