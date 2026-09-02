"""
词汇库 API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pathlib import Path
import json

router = APIRouter(prefix="/api/vocabulary", tags=["vocabulary"])

# 词汇数据目录
VOCAB_DIR = Path(__file__).parent.parent / "data" / "vocabulary"


@router.get("/high-frequency")
async def get_high_frequency_words(
    exam_type: str = "cet6",
    limit: int = 100,
    offset: int = 0
):
    """
    获取高频词汇

    Query Params:
        exam_type: 考试类型 (cet4/cet6/tem4/tem8/kaoyan)
        limit: 返回数量
        offset: 偏移量
    """
    file_path = VOCAB_DIR / f"{exam_type}_high_frequency.json"

    if not file_path.exists():
        return {
            "success": True,
            "words": [],
            "total": 0
        }

    with open(file_path, 'r', encoding='utf-8') as f:
        all_words = json.load(f)

    words = all_words[offset:offset + limit]

    return {
        "success": True,
        "words": words,
        "total": len(all_words),
        "exam_type": exam_type
    }


@router.get("/core")
async def get_core_vocabulary(exam_type: str = "cet6"):
    """
    获取核心词汇

    Query Params:
        exam_type: 考试类型
    """
    file_path = VOCAB_DIR / f"{exam_type}_core.json"

    if not file_path.exists():
        return {
            "success": True,
            "categories": []
        }

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return {
        "success": True,
        "categories": data
    }


@router.get("/collocations")
async def get_collocations(word: Optional[str] = None):
    """
    获取词汇搭配

    Query Params:
        word: 查询特定单词的搭配（可选）
    """
    file_path = VOCAB_DIR / "collocations.json"

    if not file_path.exists():
        return {
            "success": True,
            "collocations": []
        }

    with open(file_path, 'r', encoding='utf-8') as f:
        all_collocations = json.load(f)

    if word:
        # 查找特定单词
        result = [c for c in all_collocations if c.get('word', '').lower() == word.lower()]
        return {
            "success": True,
            "word": word,
            "collocations": result
        }

    return {
        "success": True,
        "collocations": all_collocations[:50]  # 默认返回前 50 个
    }


@router.get("/confusing")
async def get_confusing_words():
    """获取易混词"""
    file_path = VOCAB_DIR / "confusing_words.json"

    if not file_path.exists():
        return {
            "success": True,
            "groups": []
        }

    with open(file_path, 'r', encoding='utf-8') as f:
        groups = json.load(f)

    return {
        "success": True,
        "groups": groups
    }


@router.get("/context")
async def get_word_in_context(word: str):
    """
    获取单词在真题中的语境

    Query Params:
        word: 要查询的单词
    """
    file_path = VOCAB_DIR / "word_contexts.json"

    if not file_path.exists():
        return {
            "success": True,
            "word": word,
            "contexts": []
        }

    with open(file_path, 'r', encoding='utf-8') as f:
        all_contexts = json.load(f)

    contexts = all_contexts.get(word.lower(), [])

    return {
        "success": True,
        "word": word,
        "contexts": contexts
    }


@router.post("/initialize")
async def initialize_vocabulary_data():
    """初始化词汇数据（示例数据）"""
    VOCAB_DIR.mkdir(parents=True, exist_ok=True)

    # CET-6 高频词
    cet6_high_freq = [
        {
            "word": "accommodate",
            "phonetic": "/əˈkɒmədeɪt/",
            "meaning": "v. 容纳；提供住宿；使适应",
            "frequency": 95,
            "example": "The hotel can accommodate up to 500 guests."
        },
        {
            "word": "acknowledge",
            "phonetic": "/əkˈnɒlɪdʒ/",
            "meaning": "v. 承认；确认；致谢",
            "frequency": 92,
            "example": "He acknowledged his mistake and apologized."
        },
        {
            "word": "subsequent",
            "phonetic": "/ˈsʌbsɪkwənt/",
            "meaning": "adj. 随后的；后来的",
            "frequency": 90,
            "example": "Subsequent events proved him wrong."
        },
        {
            "word": "supplement",
            "phonetic": "/ˈsʌplɪmənt/",
            "meaning": "n./v. 补充；增补",
            "frequency": 88,
            "example": "She takes vitamin supplements daily."
        },
        {
            "word": "comprehensive",
            "phonetic": "/ˌkɒmprɪˈhensɪv/",
            "meaning": "adj. 综合的；全面的",
            "frequency": 87,
            "example": "We need a comprehensive solution."
        }
    ]

    # 保存 CET-6 高频词
    with open(VOCAB_DIR / "cet6_high_frequency.json", 'w', encoding='utf-8') as f:
        json.dump(cet6_high_freq, f, ensure_ascii=False, indent=2)

    # 核心词汇（按主题分类）
    core_vocab = [
        {
            "category": "学术类",
            "words": [
                {
                    "word": "analyze",
                    "meaning": "v. 分析",
                    "derivatives": ["analysis", "analytical", "analyst"]
                },
                {
                    "word": "evaluate",
                    "meaning": "v. 评估",
                    "derivatives": ["evaluation", "evaluative"]
                }
            ]
        },
        {
            "category": "经济类",
            "words": [
                {
                    "word": "economy",
                    "meaning": "n. 经济",
                    "derivatives": ["economic", "economical", "economist"]
                },
                {
                    "word": "financial",
                    "meaning": "adj. 金融的",
                    "derivatives": ["finance", "financially"]
                }
            ]
        }
    ]

    with open(VOCAB_DIR / "cet6_core.json", 'w', encoding='utf-8') as f:
        json.dump(core_vocab, f, ensure_ascii=False, indent=2)

    # 常用搭配
    collocations = [
        {
            "word": "make",
            "collocations": [
                {"phrase": "make a decision", "meaning": "做决定"},
                {"phrase": "make progress", "meaning": "取得进步"},
                {"phrase": "make sense", "meaning": "有意义；讲得通"}
            ]
        },
        {
            "word": "take",
            "collocations": [
                {"phrase": "take action", "meaning": "采取行动"},
                {"phrase": "take advantage of", "meaning": "利用"},
                {"phrase": "take into account", "meaning": "考虑到"}
            ]
        }
    ]

    with open(VOCAB_DIR / "collocations.json", 'w', encoding='utf-8') as f:
        json.dump(collocations, f, ensure_ascii=False, indent=2)

    # 易混词
    confusing = [
        {
            "group": ["affect", "effect"],
            "explanations": [
                {"word": "affect", "type": "v.", "meaning": "影响", "example": "The weather affects my mood."},
                {"word": "effect", "type": "n.", "meaning": "效果；影响", "example": "The medicine had no effect."}
            ]
        },
        {
            "group": ["economic", "economical"],
            "explanations": [
                {"word": "economic", "type": "adj.", "meaning": "经济的", "example": "economic growth"},
                {"word": "economical", "type": "adj.", "meaning": "节约的；经济实惠的", "example": "an economical car"}
            ]
        }
    ]

    with open(VOCAB_DIR / "confusing_words.json", 'w', encoding='utf-8') as f:
        json.dump(confusing, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "message": "词汇数据初始化完成",
        "files_created": 4
    }
