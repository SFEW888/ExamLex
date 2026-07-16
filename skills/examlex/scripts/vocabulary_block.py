from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MEMORY_TYPES = {"word-formation", "root-affix", "association", "contrast", "etymology"}
REQUIRED_FIELDS = {"sequence", "headword", "phonetics", "senses", "memory", "example", "word_family"}


def validate_vocabulary_block(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["vocabulary block must be a JSON object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - data.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
    if not isinstance(data.get("sequence"), int) or data.get("sequence", 0) < 1:
        errors.append("sequence must be a positive integer")
    for field in ("headword", "phonetics"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{field} must be a non-empty string")
    heat = data.get("heat_level", 0)
    if not isinstance(heat, int) or not 0 <= heat <= 5:
        errors.append("heat_level must be an integer from 0 to 5")
    senses = data.get("senses")
    if not isinstance(senses, list) or not senses:
        errors.append("senses must be a non-empty list")
    else:
        for index, sense in enumerate(senses, 1):
            if not isinstance(sense, dict) or not _text(sense.get("part_of_speech")):
                errors.append(f"senses[{index}] needs part_of_speech")
            if not isinstance(sense, dict) or not _text_list(sense.get("meanings")):
                errors.append(f"senses[{index}] needs non-empty meanings")
    memory = data.get("memory")
    if not isinstance(memory, dict):
        errors.append("memory must be an object")
    else:
        if memory.get("type") not in MEMORY_TYPES:
            errors.append("memory.type is unsupported")
        for field in ("breakdown", "explanation"):
            if not _text(memory.get(field)):
                errors.append(f"memory.{field} must be non-empty")
    example = data.get("example")
    if not isinstance(example, dict):
        errors.append("example must be an object")
    else:
        for field in ("sentence", "translation"):
            if not _text(example.get(field)):
                errors.append(f"example.{field} must be non-empty")
    family = data.get("word_family")
    if not isinstance(family, list) or not family:
        errors.append("word_family must be a non-empty list")
    else:
        for index, item in enumerate(family, 1):
            if not isinstance(item, dict):
                errors.append(f"word_family[{index}] must be an object")
                continue
            for field in ("word", "phonetics", "part_of_speech"):
                if not _text(item.get(field)):
                    errors.append(f"word_family[{index}].{field} must be non-empty")
            if not _text_list(item.get("meanings")):
                errors.append(f"word_family[{index}].meanings must be non-empty")
    return errors


def render_vocabulary_block(data: dict[str, Any]) -> str:
    errors = validate_vocabulary_block(data)
    if errors:
        raise ValueError("; ".join(errors))
    flames = " 🔥" * int(data.get("heat_level", 0))
    lines = [
        f"## {int(data['sequence']):02d}  {data['headword']}  {data['phonetics']}{flames}",
        "",
        "### 词义",
        "",
    ]
    for sense in data["senses"]:
        lines.append(f"- **{sense['part_of_speech']}** {'；'.join(sense['meanings'])}")
    memory = data["memory"]
    lines.extend([
        "",
        "### 记忆与构词",
        "",
        f"- **方法**：{memory['type']}",
        f"- **拆解**：{memory['breakdown']}",
        f"- **说明**：{memory['explanation']}",
        "",
        "### 语境例句",
        "",
        f"> {data['example']['sentence']}",
        ">",
        f"> {data['example']['translation']}",
    ])
    if _text(data["example"].get("exam_context")):
        lines.append(f"> 语境提示：{data['example']['exam_context']}")
    lines.extend(["", "### 派生与词族", ""])
    for item in data["word_family"]:
        meanings = "；".join(item["meanings"])
        lines.append(
            f"- **{item['word']}** {item['phonetics']} *{item['part_of_speech']}* {meanings}"
        )
    lines.extend([
        "",
        "### 主动回忆",
        "",
        "1. 遮住中文，根据词性说出核心义。",
        "2. 遮住单词，根据构词拆解拼写并朗读。",
        "3. 替换例句中的主题词，口头或书面造一个新句。",
        "",
    ])
    return "\n".join(lines)


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _text_list(value: object) -> list[str]:
    return [item.strip() for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and render a detailed vocabulary block.")
    parser.add_argument("--input", required=True, help="Vocabulary block JSON file.")
    parser.add_argument("--output", help="Markdown output path. Defaults to stdout.")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print validation report as JSON.")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        errors = validate_vocabulary_block(data)
    except (OSError, json.JSONDecodeError) as exc:
        errors = [f"could not load vocabulary block: {exc}"]
        data = None
    if errors:
        report = {"ok": False, "errors": errors}
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "ERROR: " + "; ".join(errors), file=sys.stderr)
        return 1
    if args.validate_only:
        report = {"ok": True, "errors": []}
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "Vocabulary block is valid.")
        return 0
    rendered = render_vocabulary_block(data)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
