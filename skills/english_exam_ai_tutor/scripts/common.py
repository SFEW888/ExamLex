from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXAM_TYPES = {"CET4", "CET6", "POSTGRADUATE_ENGLISH"}
FOUNDATION_LEVELS = {"基础偏弱", "中等基础", "基础较好"}
CET_TARGET_BANDS = {"425~499", "500~550", "550+", "600+"}
POSTGRADUATE_TARGET_BANDS = {"50+", "70~80", "80+", "90+"}

ABILITY_TREE = {
    "vocabulary": ["词义识别", "拼写", "听音辨词", "语境使用"],
    "listening": ["关键词捕捉", "连读弱读", "数字时间", "主旨推断"],
    "reading": ["阅读速度", "定位能力", "长难句", "推理判断"],
    "translation": ["语法准确度", "词汇选择", "中式英语", "句式多样性"],
    "writing": ["任务完成度", "结构逻辑", "语言准确性", "表达丰富度"],
}

ERROR_TAG_TO_ABILITY = {
    "VOCAB_MEANING_RECOGNITION_FAIL": ("vocabulary", "词义识别"),
    "VOCAB_SPELLING_FAIL": ("vocabulary", "拼写"),
    "VOCAB_AUDIO_RECOGNITION_FAIL": ("vocabulary", "听音辨词"),
    "VOCAB_CONTEXT_MISUSE": ("vocabulary", "语境使用"),
    "LISTENING_KEYWORD_MISS": ("listening", "关键词捕捉"),
    "LISTENING_LINKING_WEAK_FORM_FAIL": ("listening", "连读弱读"),
    "LISTENING_NUMBER_DATE_FAIL": ("listening", "数字时间"),
    "LISTENING_MAIN_IDEA_FAIL": ("listening", "主旨推断"),
    "READING_SPEED_LOW": ("reading", "阅读速度"),
    "READING_LOCATION_FAIL": ("reading", "定位能力"),
    "READING_LONG_SENTENCE_FAIL": ("reading", "长难句"),
    "READING_INFERENCE_FAIL": ("reading", "推理判断"),
    "READING_PARAPHRASE_FAIL": ("reading", "定位能力"),
    "TRANSLATION_GRAMMAR_FAIL": ("translation", "语法准确度"),
    "TRANSLATION_WORD_CHOICE_FAIL": ("translation", "词汇选择"),
    "TRANSLATION_CHINESE_ENGLISH": ("translation", "中式英语"),
    "TRANSLATION_SENTENCE_VARIETY_LOW": ("translation", "句式多样性"),
    "WRITING_TASK_RESPONSE_WEAK": ("writing", "任务完成度"),
    "WRITING_STRUCTURE_LOGIC_WEAK": ("writing", "结构逻辑"),
    "WRITING_LANGUAGE_ACCURACY_FAIL": ("writing", "语言准确性"),
    "WRITING_EXPRESSION_LIMITED": ("writing", "表达丰富度"),
    "WRITING_ARTICLE_OMISSION": ("writing", "语言准确性"),
}


def load_data(path: str | Path) -> Any:
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)


def save_data(path: str | Path, data: Any) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def target_bands_for(exam_type: str) -> set[str]:
    if exam_type in {"CET4", "CET6"}:
        return CET_TARGET_BANDS
    if exam_type == "POSTGRADUATE_ENGLISH":
        return POSTGRADUATE_TARGET_BANDS
    return set()


def validate_error_tags(tags: list[str]) -> list[str]:
    return [tag for tag in tags if tag not in ERROR_TAG_TO_ABILITY]
