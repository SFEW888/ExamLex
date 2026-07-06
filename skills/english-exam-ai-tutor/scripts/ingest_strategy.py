from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


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
    text = source.read_text(encoding="utf-8").lstrip("﻿")
    chosen_exam_types = exam_types if exam_types else common.DEFAULT_EXAM_TYPES
    chosen_modules = modules if modules else sorted(common.ABILITY_TREE.keys())
    _validate_values(chosen_exam_types, common.EXAM_TYPES, "exam type")
    _validate_values(chosen_modules, set(common.ABILITY_TREE), "module")
    if source_type not in common.SOURCE_TYPES:
        raise ValueError(f"invalid source_type '{source_type}'. Valid: {sorted(common.SOURCE_TYPES)}")
    if distillation_method not in common.DISTILLATION_METHODS:
        raise ValueError(f"invalid distillation_method '{distillation_method}'. Valid: {sorted(common.DISTILLATION_METHODS)}")

    # When distillation_method implies structured output, parse the text
    steps = _extract_steps(text)
    if distillation_method in ("ria", "video") and ria_structure is None:
        ria_structure = _parse_ria_structure(text)
        if ria_structure and ria_structure.get("e_execution"):
            steps = ria_structure["e_execution"]
    if distillation_method in ("cognitive", "person") and mental_model is None and heuristic is None:
        mental_model, heuristic = _parse_nuwa_structure(text)

    strategy: dict[str, Any] = {
        "strategy_id": _strategy_id(source.name, chosen_exam_types[0], chosen_modules[0]),
        "title": source.stem,
        "source_file": source.name,
        "source_type": source_type,
        "distillation_method": distillation_method,
        "added_at": dt.date.today().isoformat(),
        "exam_types": chosen_exam_types,
        "modules": chosen_modules,
        "ability_nodes": [],
        "content": text.strip()[:5000],
        "steps": steps,
        "tags": [],
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
    library = common.load_data(path) if path.exists() else {"strategies": []}
    strategies = library.setdefault("strategies", [])
    if not isinstance(strategies, list):
        raise ValueError("strategy library must contain a strategies list")
    strategies.append(strategy)
    path.parent.mkdir(parents=True, exist_ok=True)
    common.save_data(path, library)
    return strategy


def _validate_values(values: list[str], allowed: set[str], label: str) -> None:
    invalid = [value for value in values if value not in allowed]
    if invalid:
        raise ValueError(f"invalid {label}: {', '.join(invalid)}")


def _strategy_id(filename: str, exam_type: str, module: str) -> str:
    exam = "pg" if exam_type == "POSTGRADUATE_ENGLISH" else exam_type.lower()
    digest = hashlib.sha1(filename.encode("utf-8")).hexdigest()[:6]
    return f"{exam}-{module}-{digest}-001"


def _extract_steps(text: str) -> list[str]:
    steps: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("-", "*")):
            steps.append(stripped.lstrip("-* ").strip())
        elif len(stripped) >= 3 and stripped[0].isdigit() and stripped[1] in {".", "、"}:
            steps.append(stripped[2:].strip())
    return [step for step in steps if step][:10]


# ── RIA++ parser (structured six-section format) ──────────────
_RIA_SECTIONS = [
    ("r_reading",       re.compile(r"#+\s*R\b.*?(?:原文|Reading)", re.I)),
    ("i_interpretation", re.compile(r"#+\s*I\b.*?(?:自述|Interpretation)", re.I)),
    ("a1_past",         re.compile(r"#+\s*A1\b.*?(?:案例|Past|Application)", re.I)),
    ("a2_trigger",      re.compile(r"#+\s*A2\b.*?(?:触发|Trigger)", re.I)),
    ("e_execution",     re.compile(r"#+\s*E\b.*?(?:执行|步骤|Execution)", re.I)),
    ("b_boundary",      re.compile(r"#+\s*B\b.*?(?:边界|盲点|Boundary)", re.I)),
]


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
                    content = "\n".join(section_lines).strip()
                    if current_section == "e_execution":
                        result[current_section] = _extract_steps(content)
                    else:
                        result[current_section] = content[:2000]
                current_section = key
                section_lines = []
                matched = True
                break
        if not matched and current_section:
            section_lines.append(line)

    # Flush last section
    if current_section and section_lines:
        content = "\n".join(section_lines).strip()
        if current_section == "e_execution":
            result[current_section] = _extract_steps(content)
        else:
            result[current_section] = content[:2000]

    return result if len(result) >= 2 else None  # need at least 2 sections


# ── Cognitive extraction parser (mental models + heuristics) ─
_MODEL_HEADER = re.compile(r"#+\s*模型\d*\s*[:：]\s*(.+)", re.I)
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
            if "场景" in line or "scenario" in line.lower():
                heuristic["scenario"] = _extract_value(text, line)
            if "案例" in line or "example" in line.lower():
                heuristic["example"] = _extract_value(text, line)
        heuristic["rule"] = text.strip()[:500]
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
            if line.strip().startswith("#") or (buf and not line.strip() and len(buf) > 3):
                break
            if line.strip():
                buf.append(line.strip())
    return " ".join(buf)[:2000]


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in re.split(r"[,\s]+", value) if item.strip()]


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
