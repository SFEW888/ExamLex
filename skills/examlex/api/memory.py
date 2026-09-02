"""
记忆卡 API 路由
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Optional
import json
from pathlib import Path

from ..core.spaced_repetition import (
    MemoryCard,
    SpacedRepetitionEngine,
    Rating
)

router = APIRouter(prefix="/api/memory", tags=["memory"])

# 内存存储（实际项目应该用数据库）
CARDS_STORE = []
engine = SpacedRepetitionEngine()

# 数据文件路径
DATA_DIR = Path(__file__).parent.parent / "data"
CARDS_FILE = DATA_DIR / "memory_cards.json"


def load_cards():
    """从文件加载卡片"""
    global CARDS_STORE
    if CARDS_FILE.exists():
        with open(CARDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            CARDS_STORE = [
                MemoryCard(**{
                    **card,
                    'due': datetime.fromisoformat(card['due']),
                    'last_reviewed': datetime.fromisoformat(card['last_reviewed']) if card.get('last_reviewed') else None,
                    'created_at': datetime.fromisoformat(card['created_at'])
                })
                for card in data
            ]


def save_cards():
    """保存卡片到文件"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CARDS_FILE, 'w', encoding='utf-8') as f:
        data = [
            {
                **card.dict(),
                'due': card.due.isoformat(),
                'last_reviewed': card.last_reviewed.isoformat() if card.last_reviewed else None,
                'created_at': card.created_at.isoformat()
            }
            for card in CARDS_STORE
        ]
        json.dump(data, f, ensure_ascii=False, indent=2)


# 启动时加载数据
try:
    load_cards()
except Exception as e:
    print(f"加载卡片数据失败: {e}")
    CARDS_STORE = []


@router.get("/due")
async def get_due_cards(deck: Optional[str] = None, limit: int = 20):
    """
    获取到期的记忆卡

    Query Params:
        deck: 可选的卡组过滤
        limit: 返回数量限制
    """
    due_cards = engine.get_due_cards(CARDS_STORE, deck)[:limit]

    return {
        "success": True,
        "due": len(due_cards),
        "cards": [card.dict() for card in due_cards]
    }


@router.post("/review")
async def review_card(card_id: str, rating: Rating):
    """
    复习记忆卡

    Body:
        card_id: 卡片 ID
        rating: 评分 (again/hard/good/easy)
    """
    # 查找卡片
    card = next((c for c in CARDS_STORE if c.id == card_id), None)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")

    # 复习卡片
    updated_card = engine.review_card(card, rating)

    # 更新存储
    for i, c in enumerate(CARDS_STORE):
        if c.id == card_id:
            CARDS_STORE[i] = updated_card
            break

    # 保存到文件
    save_cards()

    return {
        "success": True,
        "card": updated_card.dict(),
        "next_due": updated_card.due.isoformat(),
        "interval_days": updated_card.interval
    }


@router.post("/cards")
async def create_card(front: str, back: str, deck: str = "default", tags: List[str] = []):
    """
    创建新的记忆卡

    Body:
        front: 正面内容
        back: 背面内容
        deck: 卡组名称
        tags: 标签列表
    """
    import uuid

    card = MemoryCard(
        id=str(uuid.uuid4()),
        front=front,
        back=back,
        deck=deck,
        tags=tags,
        due=datetime.now()  # 新卡片立即可复习
    )

    CARDS_STORE.append(card)
    save_cards()

    return {
        "success": True,
        "card": card.dict()
    }


@router.get("/cards")
async def list_cards(deck: Optional[str] = None, tag: Optional[str] = None):
    """
    列出所有记忆卡

    Query Params:
        deck: 按卡组过滤
        tag: 按标签过滤
    """
    cards = CARDS_STORE

    if deck:
        cards = [c for c in cards if c.deck == deck]

    if tag:
        cards = [c for c in cards if tag in c.tags]

    return {
        "success": True,
        "total": len(cards),
        "cards": [card.dict() for card in cards]
    }


@router.get("/statistics")
async def get_statistics(deck: Optional[str] = None):
    """
    获取学习统计

    Query Params:
        deck: 可选的卡组过滤
    """
    cards = CARDS_STORE
    if deck:
        cards = [c for c in cards if c.deck == deck]

    stats = engine.get_statistics(cards)

    return {
        "success": True,
        **stats
    }


@router.delete("/cards/{card_id}")
async def delete_card(card_id: str):
    """删除记忆卡"""
    global CARDS_STORE

    original_len = len(CARDS_STORE)
    CARDS_STORE = [c for c in CARDS_STORE if c.id != card_id]

    if len(CARDS_STORE) == original_len:
        raise HTTPException(status_code=404, detail="卡片不存在")

    save_cards()

    return {
        "success": True,
        "message": "卡片已删除"
    }


@router.post("/import")
async def import_cards_from_text(text: str, deck: str = "vocabulary"):
    """
    批量导入卡片（从文本）

    格式：每行一张卡片，用 | 分隔正反面
    例如：apple|苹果
    """
    import uuid

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    imported = 0

    for line in lines:
        parts = line.split('|')
        if len(parts) >= 2:
            card = MemoryCard(
                id=str(uuid.uuid4()),
                front=parts[0].strip(),
                back=parts[1].strip(),
                deck=deck,
                due=datetime.now()
            )
            CARDS_STORE.append(card)
            imported += 1

    save_cards()

    return {
        "success": True,
        "imported": imported,
        "message": f"成功导入 {imported} 张卡片"
    }
