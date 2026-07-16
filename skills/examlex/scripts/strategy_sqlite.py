from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import Any, TypeVar


T = TypeVar("T")
SCHEMA_VERSION = 1


def connect(path: str | Path) -> sqlite3.Connection:
    database = Path(path)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    _initialize(connection)
    return connection


def _initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS strategies (
            strategy_id TEXT PRIMARY KEY,
            title_normalized TEXT NOT NULL,
            content_normalized TEXT NOT NULL,
            exam_scope TEXT NOT NULL,
            module_scope TEXT NOT NULL,
            strategy_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_strategies_title ON strategies(title_normalized);
        CREATE INDEX IF NOT EXISTS idx_strategies_scope ON strategies(exam_scope, module_scope);
        CREATE TABLE IF NOT EXISTS revisions (
            strategy_id TEXT NOT NULL,
            revision_key TEXT NOT NULL,
            version TEXT NOT NULL,
            content_normalized TEXT NOT NULL,
            revision_json TEXT NOT NULL,
            PRIMARY KEY(strategy_id, revision_key),
            FOREIGN KEY(strategy_id) REFERENCES strategies(strategy_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_revisions_content ON revisions(content_normalized);
        """
    )
    connection.execute(
        "INSERT OR REPLACE INTO metadata(key, value_json) VALUES(?, ?)",
        ("sqlite_schema_version", json.dumps(SCHEMA_VERSION)),
    )
    connection.commit()


def load_library(path: str | Path) -> dict[str, Any]:
    database = Path(path)
    if not database.exists():
        return {"strategies": []}
    with closing(connect(database)) as connection:
        metadata = {
            row["key"]: json.loads(row["value_json"])
            for row in connection.execute(
                "SELECT key, value_json FROM metadata WHERE key <> 'sqlite_schema_version'"
            )
        }
        # Fetch every revision in one pass and group in Python to avoid an
        # N+1 query (one revision query per strategy). ORDER BY strategy_id,
        # rowid preserves each strategy's original revision order.
        revisions_by_strategy: dict[str, list[dict[str, Any]]] = {}
        for revision in connection.execute(
            "SELECT strategy_id, revision_json FROM revisions ORDER BY strategy_id, rowid"
        ):
            revisions_by_strategy.setdefault(revision["strategy_id"], []).append(
                json.loads(revision["revision_json"])
            )
        strategies: list[dict[str, Any]] = []
        for row in connection.execute(
            "SELECT strategy_id, strategy_json FROM strategies ORDER BY rowid"
        ):
            strategy = json.loads(row["strategy_json"])
            revisions = revisions_by_strategy.get(row["strategy_id"])
            if revisions:
                strategy["revisions"] = revisions
            strategies.append(strategy)
    metadata["strategies"] = strategies
    return metadata


def save_library(library: dict[str, Any], path: str | Path) -> Path:
    if not isinstance(library, dict) or not isinstance(library.get("strategies"), list):
        raise ValueError("strategy library must contain a strategies list")
    database = Path(path)
    with closing(connect(database)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        current_ids: set[str] = set()
        for index, raw in enumerate(library["strategies"], 1):
            if not isinstance(raw, dict):
                raise ValueError(f"strategy {index} must be an object")
            strategy = dict(raw)
            revisions = strategy.pop("revisions", [])
            strategy_id = str(strategy.get("strategy_id") or f"strategy-{index}")
            strategy["strategy_id"] = strategy_id
            current_ids.add(strategy_id)
            connection.execute(
                """
                INSERT INTO strategies(
                    strategy_id, title_normalized, content_normalized,
                    exam_scope, module_scope, strategy_json
                ) VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(strategy_id) DO UPDATE SET
                    title_normalized=excluded.title_normalized,
                    content_normalized=excluded.content_normalized,
                    exam_scope=excluded.exam_scope,
                    module_scope=excluded.module_scope,
                    strategy_json=excluded.strategy_json
                """,
                (
                    strategy_id,
                    _normalized(strategy.get("title")),
                    _normalized(strategy.get("content")),
                    _scope(strategy.get("exam_types")),
                    _scope(strategy.get("modules")),
                    json.dumps(strategy, ensure_ascii=False, sort_keys=True, allow_nan=False),
                ),
            )
            connection.execute("DELETE FROM revisions WHERE strategy_id = ?", (strategy_id,))
            if isinstance(revisions, list):
                for revision_index, revision in enumerate(revisions, 1):
                    if not isinstance(revision, dict):
                        continue
                    snapshot = revision.get("strategy")
                    content = snapshot.get("content") if isinstance(snapshot, dict) else ""
                    revision_key = str(
                        revision.get("sha256")
                        or revision.get("version")
                        or revision_index
                    )
                    connection.execute(
                        """
                        INSERT INTO revisions(
                            strategy_id, revision_key, version,
                            content_normalized, revision_json
                        ) VALUES(?, ?, ?, ?, ?)
                        """,
                        (
                            strategy_id,
                            revision_key,
                            str(revision.get("version", revision_index)),
                            _normalized(content),
                            json.dumps(revision, ensure_ascii=False, sort_keys=True, allow_nan=False),
                        ),
                    )
        if current_ids:
            stored_ids = {
                row["strategy_id"]
                for row in connection.execute("SELECT strategy_id FROM strategies")
            }
            connection.executemany(
                "DELETE FROM strategies WHERE strategy_id = ?",
                ((strategy_id,) for strategy_id in sorted(stored_ids - current_ids)),
            )
        else:
            connection.execute("DELETE FROM strategies")
        for key, value in library.items():
            if key == "strategies":
                continue
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value_json) VALUES(?, ?)",
                (str(key), json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)),
            )
        connection.commit()
    return database


def mutate_library(path: str | Path, mutator: Callable[[dict[str, Any]], T]) -> T:
    database = Path(path)
    # The write itself is an IMMEDIATE SQLite transaction. The callback receives
    # a detached object so existing JSON mutators remain backward compatible.
    library = load_library(database)
    result = mutator(library)
    save_library(library, database)
    return result


def import_json(json_path: str | Path, database_path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    save_library(data, database_path)
    return {"strategies": len(data.get("strategies", [])), "database": str(database_path)}


def export_json(database_path: str | Path, json_path: str | Path) -> dict[str, Any]:
    data = load_library(database_path)
    output = Path(json_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {"strategies": len(data.get("strategies", [])), "output": str(output)}


def _normalized(value: object) -> str:
    return " ".join(value.casefold().split()) if isinstance(value, str) else ""


def _scope(value: object) -> str:
    if not isinstance(value, list):
        return ""
    return "|".join(sorted(item for item in value if isinstance(item, str)))
