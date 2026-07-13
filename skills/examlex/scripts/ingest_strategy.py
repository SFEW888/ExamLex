from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import re
import sys
from functools import wraps
from pathlib import Path
from typing import Any

try:
    from . import common
    from .file_lock import exclusive_file_lock
    from .strategy_store import atomic_save_strategy_library
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]
    from file_lock import exclusive_file_lock  # type: ignore[no-redef]
    from strategy_store import atomic_save_strategy_library  # type: ignore[no-redef]

_LOGGER = logging.getLogger(__name__)


def _locked_library_update(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        library_path = Path(kwargs["library_path"])
        with exclusive_file_lock(library_path):
            return function(*args, **kwargs)

    return wrapped


@_locked_library_update
def ingest_strategy(
    *,
    file_path: str | Path,
    library_path: str | Path,
    exam_types: list[str] | None = None,
    modules: list[str] | None = None,
    source_type: str = "text",
    distillation_method: str = "direct",
    source_url: str | None = None,
    ria_structure: dict[str, Any] | None = None,
    mental_model: dict[str, Any] | None = None,
    heuristic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = Path(file_path)
    if not source.is_file():
        raise FileNotFoundError(f"strategy source file not found: {source}")
    raw_source = source.read_bytes()
    text = raw_source.decode("utf-8").lstrip("﻿")
    source_sha256 = hashlib.sha256(raw_source).hexdigest()
    chosen_exam_types = exam_types if exam_types else common.DEFAULT_EXAM_TYPES
    chosen_modules = modules if modules else sorted(common.ABILITY_TREE.keys())
    _validate_values(chosen_exam_types, common.EXAM_TYPES, "exam type")
    _validate_values(chosen_modules, set(common.ABILITY_TREE), "module")
    if source_type not in common.SOURCE_TYPES:
        raise ValueError(f"invalid source_type '{source_type}'. Valid: {sorted(common.SOURCE_TYPES)}")
    if distillation_method not in common.DISTILLATION_METHODS:
        raise ValueError(f"invalid distillation_method '{distillation_method}'. Valid: {sorted(common.DISTILLATION_METHODS)}")

    path = Path(library_path)
    if path.exists():
        library = common.load_data(path)
        existing_entries = library.get("strategies", []) if isinstance(library, dict) else []
    else:
        existing_entries = []
    if not isinstance(existing_entries, list):
        raise ValueError("strategy library must contain a strategies list")
    ingest_fingerprint = _ingest_fingerprint(
        source_sha256=source_sha256,
        exam_types=chosen_exam_types,
        modules=chosen_modules,
        source_type=source_type,
        distillation_method=distillation_method,
        source_url=source_url,
        ria_structure=ria_structure,
        mental_model=mental_model,
        heuristic=heuristic,
    )
    duplicate = _find_duplicate_ingest(
        existing_entries,
        ingest_fingerprint=ingest_fingerprint,
        source_sha256=source_sha256,
        exam_types=chosen_exam_types,
        modules=chosen_modules,
        source_type=source_type,
        distillation_method=distillation_method,
    )
    if duplicate is not None:
        _LOGGER.info(
            "strategy source already ingested with the same scope: %s",
            duplicate.get("strategy_id", source.name),
        )
        return duplicate
    existing_ids = {
        entry.get("strategy_id") for entry in existing_entries if isinstance(entry, dict)
    }

    # When distillation_method implies structured output, parse the text
    ria_parsed = False
    if distillation_method in ("ria", "video") and ria_structure is None:
        ria_structure = _parse_ria_structure(text)
        if ria_structure and ria_structure.get("e_execution"):
            ria_parsed = True
    steps = ria_structure["e_execution"] if ria_parsed and ria_structure else _extract_steps(text)
    if distillation_method in ("cognitive", "person") and mental_model is None and heuristic is None:
        mental_model, heuristic = _parse_nuwa_structure(text)

    content = text.strip()
    if len(content) > 5000:
        _LOGGER.warning(
            "strategy '%s' content truncated from %d to 5000 chars",
            source.name, len(content),
        )
    strategy: dict[str, Any] = {
        "strategy_id": _strategy_id(
            source.name,
            chosen_exam_types[0] if chosen_exam_types else "unknown",
            chosen_modules[0] if chosen_modules else "unknown",
            content,
            existing_ids,
        ),
        "title": source.stem,
        "source_file": source.name,
        "source_type": source_type,
        "distillation_method": distillation_method,
        "added_at": dt.date.today().isoformat(),
        "exam_types": chosen_exam_types,
        "modules": chosen_modules,
        "ability_nodes": [],
        "content": content[:5000],
        "steps": steps,
        "tags": [],
        "lifecycle_status": "draft",
        "source_provenance": {
            "source_file": source.name,
            "source_url": source_url,
            "sha256": source_sha256,
            "ingest_fingerprint": ingest_fingerprint,
            "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
    }
    if source_url:
        strategy["source_url"] = source_url
    if ria_structure:
        strategy["ria_structure"] = ria_structure
    if mental_model:
        strategy["mental_model"] = mental_model
    if heuristic:
        strategy["heuristic"] = heuristic

    path = Path(library_path)
    if path.exists():
        try:
            library = common.load_data(path)
        except json.JSONDecodeError as exc:
            raise ValueError(f"strategy library at {path} is corrupted — not valid JSON: {exc}") from exc
    else:
        library = {"strategies": []}
    strategies = library.setdefault("strategies", [])
    if not isinstance(strategies, list):
        raise ValueError("strategy library must contain a strategies list")
    # Deduplicate by strategy_id: replace an existing entry rather than append.
    existing = next(
        (i for i, s in enumerate(strategies)
         if isinstance(s, dict) and s.get("strategy_id") == strategy["strategy_id"]),
        None,
    )
    if existing is not None:
        strategies[existing] = strategy
    else:
        strategies.append(strategy)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_save(path, library)
    return strategy


def _atomic_save(path: Path, data: Any) -> None:
    """Write a complete library with a unique, fsynced temporary file."""
    atomic_save_strategy_library(data, path)


def _validate_values(values: list[str], allowed: set[str], label: str) -> None:
    invalid = [value for value in values if value not in allowed]
    if invalid:
        raise ValueError(f"invalid {label}: {', '.join(invalid)}")


def _ingest_fingerprint(
    *,
    source_sha256: str,
    exam_types: list[str],
    modules: list[str],
    source_type: str,
    distillation_method: str,
    source_url: str | None,
    ria_structure: dict[str, Any] | None,
    mental_model: dict[str, Any] | None,
    heuristic: dict[str, Any] | None,
) -> str:
    payload = {
        "source_sha256": source_sha256,
        "exam_types": sorted(set(exam_types)),
        "modules": sorted(set(modules)),
        "source_type": source_type,
        "distillation_method": distillation_method,
        "source_url": source_url,
        "ria_structure": ria_structure,
        "mental_model": mental_model,
        "heuristic": heuristic,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _find_duplicate_ingest(
    entries: list[Any],
    *,
    ingest_fingerprint: str,
    source_sha256: str,
    exam_types: list[str],
    modules: list[str],
    source_type: str,
    distillation_method: str,
) -> dict[str, Any] | None:
    expected_exams = sorted(set(exam_types))
    expected_modules = sorted(set(modules))
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        provenance = entry.get("source_provenance")
        if not isinstance(provenance, dict):
            continue
        stored_fingerprint = provenance.get("ingest_fingerprint")
        if stored_fingerprint == ingest_fingerprint:
            return entry
        # Backward-compatible matching for libraries created before fingerprints.
        if stored_fingerprint is not None or provenance.get("sha256") != source_sha256:
            continue
        if sorted(set(entry.get("exam_types", []))) != expected_exams:
            continue
        if sorted(set(entry.get("modules", []))) != expected_modules:
            continue
        if entry.get("source_type") != source_type:
            continue
        if entry.get("distillation_method") != distillation_method:
            continue
        return entry
    return None


def _strategy_id(
    filename: str,
    exam_type: str,
    module: str,
    content: str = "",
    existing_ids: set[object] | None = None,
) -> str:
    exam = "pg" if exam_type == "POSTGRADUATE_ENGLISH" else exam_type.lower()
    # Incorporate leading content so two files sharing a base name get distinct ids.
    payload = filename + (content[:200] if content else "")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    prefix = f"{exam}-{module}-{digest}"
    known_ids = {value for value in (existing_ids or set()) if isinstance(value, str)}
    sequence = 1
    while f"{prefix}-{sequence:03d}" in known_ids:
        sequence += 1
    return f"{prefix}-{sequence:03d}"


def _extract_steps(text: str) -> list[str]:
    steps: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        bullet = re.match(r"^[-*]\s+(.*)", stripped)
        numbered = re.match(r"^\d+[.、]\s*(.*)", stripped)
        if bullet:
            steps.append(bullet.group(1).strip())
        elif numbered:
            steps.append(numbered.group(1).strip())
    result = [step for step in steps if step]
    if len(result) > 10:
        _LOGGER.warning("step extraction truncated from %d to 10 steps", len(result))
    return result[:10]


# ── RIA++ parser (structured six-section format) ──────────────
_RIA_SECTIONS = [
    ("r_reading",       re.compile(r"#+\s*R\b.*?(?:原文|Reading)", re.I)),
    ("i_interpretation", re.compile(r"#+\s*I\b.*?(?:自述|Interpretation)", re.I)),
    ("a1_past",         re.compile(r"#+\s*A1\b.*?(?:案例|Past|Application)", re.I)),
    ("a2_trigger",      re.compile(r"#+\s*A2\b.*?(?:触发|Trigger)", re.I)),
    ("e_execution",     re.compile(r"#+\s*E\b.*?(?:执行|步骤|Execution)", re.I)),
    ("b_boundary",      re.compile(r"#+\s*B\b.*?(?:边界|盲点|Boundary)", re.I)),
]


def _store_ria_section(result: dict[str, Any], section: str, section_lines: list[str]) -> None:
    content = "\n".join(section_lines).strip()
    if section == "e_execution":
        result[section] = _extract_steps(content)
    else:
        if len(content) > 2000:
            _LOGGER.warning(
                "RIA section '%s' truncated from %d to 2000 chars",
                section, len(content),
            )
        result[section] = content[:2000]


def _parse_ria_structure(text: str) -> dict[str, Any] | None:
    """Parse RIA++ six-section format from pre-structured text."""
    result: dict[str, Any] = {}
    lines = text.splitlines()
    current_section: str | None = None
    section_lines: list[str] = []

    for line in lines:
        matched = False
        for key, pattern in _RIA_SECTIONS:
            if pattern.search(line):
                if current_section and section_lines:
                    _store_ria_section(result, current_section, section_lines)
                current_section = key
                section_lines = []
                matched = True
                break
        if not matched and current_section:
            section_lines.append(line)

    # Flush last section
    if current_section and section_lines:
        _store_ria_section(result, current_section, section_lines)

    return result if len(result) >= 2 else None  # need at least 2 sections


# ── Cognitive extraction parser (mental models + heuristics) ─
_MODEL_HEADER = re.compile(r"#+\s*(?:心智)?模型\d*\s*[:：]\s*(.+)", re.I)
_HEURISTIC_HEADER = re.compile(r"^\d+\.\s*\*?\*?(.+?)\*?\*?\s*[:：]", re.I)


def _parse_nuwa_structure(text: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Parse cognitive extraction output: mental models and decision heuristics."""
    model: dict[str, Any] | None = None
    heuristic: dict[str, Any] | None = None

    # Detect mental_model section
    if "心智模型" in text or "mental model" in text.lower():
        model = {"name": "", "one_liner": "", "evidence": "", "application": "", "limitations": ""}
        for line in text.splitlines():
            m = _MODEL_HEADER.search(line)
            if m and not model["name"]:
                model["name"] = m.group(1).strip()
            if "证据" in line or "evidence" in line.lower():
                model["evidence"] = _extract_value(text, line)
            if "应用" in line or "application" in line.lower():
                model["application"] = _extract_value(text, line)
            if "局限" in line or "limitation" in line.lower():
                model["limitations"] = _extract_value(text, line)
        if not model["name"]:
            model = None

    # Detect heuristic section
    if "决策启发" in text or "decision heuristic" in text.lower():
        heuristic = {"name": "", "rule": "", "scenario": "", "example": ""}
        for line in text.splitlines():
            m = _HEURISTIC_HEADER.search(line)
            if m and not heuristic["name"]:
                heuristic["name"] = m.group(1).strip()
            if "规则" in line or "rule" in line.lower():
                heuristic["rule"] = _extract_value(text, line)
            if "场景" in line or "scenario" in line.lower():
                heuristic["scenario"] = _extract_value(text, line)
            if "案例" in line or "example" in line.lower():
                heuristic["example"] = _extract_value(text, line)
        if not heuristic["name"]:
            heuristic = None

    return model, heuristic


def _extract_value(text: str, header_line: str) -> str:
    """Extract the paragraph following a header line."""
    lines = text.splitlines()
    found = False
    buf: list[str] = []
    for line in lines:
        if line.strip() == header_line.strip():
            found = True
            continue
        if found:
            # Collect until the next section header (markdown heading or
            # numbered heuristic item) rather than stopping at a blank line,
            # so multi-paragraph values are not prematurely truncated.
            if line.strip().startswith("#") or _HEURISTIC_HEADER.search(line):
                break
            if line.strip():
                buf.append(line.strip())
    return " ".join(buf)[:2000]


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_json_arg(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest a strategy note into a strategy library.")
    parser.add_argument("--file", required=True, help="Source strategy text file.")
    parser.add_argument("--library", required=True, help="Strategy library JSON path.")
    parser.add_argument("--exam-types", help="Comma-separated exam types.")
    parser.add_argument("--modules", help="Comma-separated modules.")
    parser.add_argument("--source-type", default="text",
                        choices=sorted(common.SOURCE_TYPES),
                        help="Strategy source type.")
    parser.add_argument("--distillation-method", default="direct",
                        choices=sorted(common.DISTILLATION_METHODS),
                        help="Distillation tool used.")
    parser.add_argument("--source-url", help="Original source URL.")
    parser.add_argument("--ria-json", help="JSON string with RIA++ six-section structure.")
    parser.add_argument("--model-json", help="JSON string with cognitive extraction mental model.")
    parser.add_argument("--heuristic-json", help="JSON string with cognitive extraction heuristic.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    ria = _parse_json_arg(args.ria_json)
    model = _parse_json_arg(args.model_json)
    heuristic = _parse_json_arg(args.heuristic_json)

    strategy = ingest_strategy(
        file_path=args.file,
        library_path=args.library,
        exam_types=_split_csv(args.exam_types),
        modules=_split_csv(args.modules),
        source_type=args.source_type,
        distillation_method=args.distillation_method,
        source_url=args.source_url,
        ria_structure=ria,
        mental_model=model,
        heuristic=heuristic,
    )
    if args.json:
        _print_json(strategy)
    else:
        print(f"ingested: {strategy['strategy_id']} {strategy['title']}")
    return 0


def _print_json(data: Any) -> None:
    sys.stdout.buffer.write((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
