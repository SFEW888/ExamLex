from __future__ import annotations

import argparse
import json
import re
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]


RULES: tuple[tuple[str | None, tuple[str, ...], str], ...] = (
    ("writing", ("article", "a/an", "an ", " a ", "the "), "WRITING_ARTICLE_OMISSION"),
    ("reading", ("paraphrase", "synonym", "同义", "替换"), "READING_PARAPHRASE_FAIL"),
    ("listening", ("number", "date", "time", "数字", "日期", "时间"), "LISTENING_NUMBER_DATE_FAIL"),
    ("translation", ("chinese-style", "chinglish", "中式", "中文式"), "TRANSLATION_CHINESE_ENGLISH"),
    ("reading", ("long sentence", "complex sentence", "长难句"), "READING_LONG_SENTENCE_FAIL"),
    ("listening", ("keyword", "key word", "关键词"), "LISTENING_KEYWORD_MISS"),
    ("writing", ("structure", "logic", "结构", "逻辑"), "WRITING_STRUCTURE_LOGIC_WEAK"),
    ("translation", ("word choice", "vocabulary choice", "选词"), "TRANSLATION_WORD_CHOICE_FAIL"),
)


def _keyword_in_text(keyword: str, text: str) -> bool:
    """Word-aware containment test.

    Avoids ASCII substring false positives (e.g. keyword ``"an "`` matching
    inside ``"than "``) by requiring that a keyword is not flanked by other
    ASCII letters. Non-ASCII keywords (e.g. Chinese) have no ASCII word
    boundaries, so the guards are always satisfied and the check degrades to
    plain containment, preserving the original behavior for them.
    """
    keyword = keyword.lower().strip()
    if not keyword:
        return False
    pattern = r"(?<![a-z])" + re.escape(keyword) + r"(?![a-z])"
    return re.search(pattern, text) is not None


def tag_error(text: str, module: str | None = None) -> dict[str, Any]:
    normalized_text = f" {text.lower()} "
    normalized_module = module.lower() if module else None
    tags: list[str] = []

    for rule_module, keywords, tag in RULES:
        if rule_module is not None and normalized_module not in {None, rule_module}:
            continue
        if any(_keyword_in_text(keyword, normalized_text) for keyword in keywords):
            tags.append(tag)

    unknown = common.validate_error_tags(tags)
    if unknown:
        raise ValueError(f"unknown error tags from rules: {', '.join(unknown)}")

    return {"module": module, "error_tags": tags}


def run_cli(argv: list[str] | None = None) -> str:
    parser = argparse.ArgumentParser(description="Tag an English exam error deterministically.")
    parser.add_argument("--text", required=True, help="Observed error text.")
    parser.add_argument("--module", help="Optional module context.")
    args = parser.parse_args(argv)
    return json.dumps(tag_error(args.text, args.module), ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    print(run_cli(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
