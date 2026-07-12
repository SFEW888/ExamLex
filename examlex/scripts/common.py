from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

EXAM_TYPES = {"CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8"}
ALL_EXAMS = frozenset(EXAM_TYPES)
DEFAULT_EXAM_TYPES: tuple[str, ...] = tuple(sorted(EXAM_TYPES))  # ("CET4","CET6","POSTGRADUATE_ENGLISH","TEM4","TEM8")
FOUNDATION_LEVELS = {"基础偏弱", "中等基础", "基础较好"}
CET_TARGET_BANDS = {"425~499", "500~550", "550+", "600+"}
POSTGRADUATE_TARGET_BANDS = {"50+", "70~80", "80+", "90+"}
TEM_TARGET_BANDS = {"60~69", "70~79", "80+"}

ABILITY_TREE = {
    "vocabulary": ["词义识别", "拼写", "听音辨词", "语境使用"],
    "listening": ["关键词捕捉", "连读弱读", "数字时间", "主旨推断"],
    "reading": ["阅读速度", "定位能力", "长难句", "推理判断"],
    "translation": ["语法准确度", "词汇选择", "中式英语", "句式多样性"],
    "writing": ["任务完成度", "结构逻辑", "语言准确性", "表达丰富度"],
    "language-knowledge": ["语法选择", "词汇辨析"],
    "proofreading": ["冠词错误", "搭配错误", "逻辑错误"],
    "dictation": ["听写准确率", "拼写速度"],
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
    # TEM-4 language-knowledge
    "LANG_GRAMMAR_SELECT_FAIL": ("language-knowledge", "语法选择"),
    "LANG_VOCAB_DISCRIMINATE_FAIL": ("language-knowledge", "词汇辨析"),
    # TEM-8 proofreading
    "PROOFREAD_ARTICLE_MISS": ("proofreading", "冠词错误"),
    "PROOFREAD_COLLOCATION_FAIL": ("proofreading", "搭配错误"),
    "PROOFREAD_LOGIC_INCOHERENT": ("proofreading", "逻辑错误"),
    # TEM-4 dictation
    "DICTATION_ACCURACY_LOW": ("dictation", "听写准确率"),
    "DICTATION_SPELLING_SPEED_LOW": ("dictation", "拼写速度"),
}


def canonical_json_sha256(value: Any) -> str:
    """Return a stable content digest for a JSON-compatible value."""
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_data(path: str | Path) -> Any:
    """Load JSON data from a file.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains malformed JSON.
        PermissionError: If the file cannot be read.
        OSError: For other I/O errors.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
        return json.loads(text)
    except FileNotFoundError:
        raise FileNotFoundError(f"Data file not found: {path}")
    except json.JSONDecodeError:
        raise
    except PermissionError:
        raise PermissionError(f"Permission denied reading: {path}")
    except OSError as e:
        raise OSError(f"Error reading data file '{path}': {e}") from e


def atomic_save_data(path: str | Path, data: Any) -> None:
    """Save JSON data to a file, creating parent directories if needed.

    Raises:
        TypeError: If the data is not JSON-serializable.
        PermissionError: If the file cannot be written.
        OSError: For other I/O errors.
    """
    try:
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    except TypeError as e:
        raise TypeError(f"Data is not JSON-serializable: {e}")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=p.parent,
            prefix=p.name + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(p)
    except PermissionError:
        raise PermissionError(f"Permission denied writing: {path}")
    except OSError as e:
        raise OSError(f"Error writing data file '{path}': {e}") from e
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_data(path: str | Path, data: Any) -> None:
    """Backward-compatible atomic JSON save."""
    atomic_save_data(path, data)


def target_bands_for(exam_type: str) -> set[str]:
    if exam_type in {"CET4", "CET6"}:
        return CET_TARGET_BANDS
    if exam_type == "POSTGRADUATE_ENGLISH":
        return POSTGRADUATE_TARGET_BANDS
    if exam_type in {"TEM4", "TEM8"}:
        return TEM_TARGET_BANDS
    return set()


def validate_error_tags(tags: list[str]) -> list[str]:
    """Return the *unrecognized* tags (those absent from ERROR_TAG_TO_ABILITY).

    An empty result means every tag is valid. Callers use this to report which
    tags failed validation.
    """
    return [tag for tag in tags if tag not in ERROR_TAG_TO_ABILITY]


# ============================================================
# 计时训练时间模板（分钟）
# ============================================================
EXAM_TIME_LIMITS: dict[str, dict[str, int]] = {
    "CET4": {
        "writing": 30, "listening": 25, "reading": 40, "translation": 30,
    },
    "CET6": {
        "writing": 30, "listening": 30, "reading": 40, "translation": 30,
    },
    "POSTGRADUATE_ENGLISH": {
        "reading": 60, "writing": 50, "translation": 30, "cloze": 20,
    },
    "TEM4": {
        "dictation": 15, "listening": 20, "language-knowledge": 10,
        "cloze": 10, "reading": 25, "writing": 35,
    },
    "TEM8": {
        "listening": 25, "reading": 30, "translation": 25,
        "writing": 45, "proofreading": 15,
    },
}


def get_time_limit(exam_type: str, module: str) -> int | None:
    """返回指定考试 + 模块的规定时间（分钟），未定义则返回 None。"""
    return EXAM_TIME_LIMITS.get(exam_type, {}).get(module)


# ============================================================
# 间隔复习 — 错误标签基础严重性权重 (0.0 ~ 1.0)
# ============================================================
ERROR_SEVERITY_WEIGHTS: dict[str, float] = {
    "WRITING_TASK_RESPONSE_WEAK": 0.9,
    "WRITING_STRUCTURE_LOGIC_WEAK": 0.9,
    "WRITING_LANGUAGE_ACCURACY_FAIL": 0.85,
    "WRITING_EXPRESSION_LIMITED": 0.7,
    "WRITING_ARTICLE_OMISSION": 0.6,
    "READING_SPEED_LOW": 0.8,
    "READING_LONG_SENTENCE_FAIL": 0.7,
    "READING_INFERENCE_FAIL": 0.75,
    "READING_LOCATION_FAIL": 0.65,
    "READING_PARAPHRASE_FAIL": 0.6,
    "LISTENING_KEYWORD_MISS": 0.75,
    "LISTENING_MAIN_IDEA_FAIL": 0.7,
    "LISTENING_LINKING_WEAK_FORM_FAIL": 0.65,
    "LISTENING_NUMBER_DATE_FAIL": 0.55,
    "TRANSLATION_GRAMMAR_FAIL": 0.7,
    "TRANSLATION_CHINESE_ENGLISH": 0.65,
    "TRANSLATION_WORD_CHOICE_FAIL": 0.55,
    "TRANSLATION_SENTENCE_VARIETY_LOW": 0.5,
    "VOCAB_CONTEXT_MISUSE": 0.6,
    "VOCAB_MEANING_RECOGNITION_FAIL": 0.55,
    "VOCAB_SPELLING_FAIL": 0.5,
    "VOCAB_AUDIO_RECOGNITION_FAIL": 0.5,
    "LANG_GRAMMAR_SELECT_FAIL": 0.65,
    "LANG_VOCAB_DISCRIMINATE_FAIL": 0.6,
    "PROOFREAD_ARTICLE_MISS": 0.55,
    "PROOFREAD_COLLOCATION_FAIL": 0.6,
    "PROOFREAD_LOGIC_INCOHERENT": 0.55,
    "DICTATION_ACCURACY_LOW": 0.7,
    "DICTATION_SPELLING_SPEED_LOW": 0.55,
}

# ============================================================
# 持续学习 — 多源蒸馏类型
# ============================================================
SOURCE_TYPES = {"text", "book", "video", "podcast", "person", "course", "conversation"}

DISTILLATION_METHODS = {
    "direct":  "直接文本摄入：读取纯文本/Markdown 策略文件，提取核心方法并写入",
    "book":    "内置书籍结构化提取：PDF/EPUB/DOCX → 章节树 + 术语表 + 模式库 + 速查表",
    "video":   "内置视频蒸馏：视频/播客/课程 → RIA-TV++ 六阶段（下载→ASR→Adler理解→并行提取→三重验证→RIA++构造→链接→压力测试）",
    "person":  "内置人物蒸馏：人物/教师 → 六路并行调研 → 三重验证 → 五层认知提取 → 双Agent精炼",
    "manual":  "手动整理：用户自行总结策略，Agent 辅助结构化后写入",
}
