"""
间隔重复记忆卡系统 - Anki SM-2 算法实现

基于 Anki 的 SM-2 算法，支持：
- Again/Hard/Good/Easy 四级评分
- 自动计算下次复习时间
- 难度因子调整
- 复习队列管理
"""

from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class Rating(str, Enum):
    """复习评分"""
    AGAIN = "again"  # 完全不记得，重新学习
    HARD = "hard"    # 困难，记得但不清晰
    GOOD = "good"    # 良好，记得比较清楚
    EASY = "easy"    # 简单，完全记得


class MemoryCard(BaseModel):
    """记忆卡"""
    id: str
    front: str  # 正面（问题/单词）
    back: str   # 背面（答案/释义）

    # SM-2 算法参数
    ease_factor: float = 2.5  # 难度因子（1.3-2.5）
    interval: int = 0         # 间隔天数
    repetitions: int = 0      # 连续正确次数

    # 时间相关
    due: datetime             # 下次复习时间
    last_reviewed: Optional[datetime] = None
    created_at: datetime = datetime.now()

    # 分类
    deck: str = "default"     # 所属卡组
    tags: List[str] = []      # 标签

    # 学习统计
    total_reviews: int = 0    # 总复习次数
    lapses: int = 0          # 遗忘次数


class SpacedRepetitionEngine:
    """间隔重复引擎（SM-2 算法）"""

    # SM-2 算法常量
    MIN_EASE_FACTOR = 1.3
    INITIAL_EASE_FACTOR = 2.5

    # 新卡片的初始间隔（分钟）
    LEARNING_STEPS = [1, 10]  # 1分钟后，10分钟后

    # 毕业间隔（天）
    GRADUATING_INTERVAL = 1   # 学习阶段完成后的间隔
    EASY_INTERVAL = 4         # 直接点击 Easy 的间隔

    def calculate_next_interval(
        self,
        card: MemoryCard,
        rating: Rating
    ) -> tuple[datetime, float, int, int]:
        """
        计算下次复习时间

        Returns:
            (next_due, new_ease_factor, new_interval, new_repetitions)
        """
        now = datetime.now()

        # 新卡片（第一次学习）
        if card.repetitions == 0:
            return self._handle_new_card(now, rating)

        # 学习阶段（repetitions < 2）
        if card.repetitions < 2:
            return self._handle_learning_card(card, now, rating)

        # 复习阶段（已经学会的卡片）
        return self._handle_review_card(card, now, rating)

    def _handle_new_card(
        self,
        now: datetime,
        rating: Rating
    ) -> tuple[datetime, float, int, int]:
        """处理新卡片"""
        if rating == Rating.AGAIN:
            # 1分钟后再次复习
            return (
                now + timedelta(minutes=self.LEARNING_STEPS[0]),
                self.INITIAL_EASE_FACTOR,
                0,
                0
            )
        elif rating == Rating.HARD:
            # 10分钟后复习
            return (
                now + timedelta(minutes=self.LEARNING_STEPS[1]),
                self.INITIAL_EASE_FACTOR,
                0,
                1
            )
        elif rating == Rating.GOOD:
            # 1天后复习（毕业）
            return (
                now + timedelta(days=self.GRADUATING_INTERVAL),
                self.INITIAL_EASE_FACTOR,
                1,
                2
            )
        else:  # EASY
            # 4天后复习（跳过学习阶段）
            return (
                now + timedelta(days=self.EASY_INTERVAL),
                self.INITIAL_EASE_FACTOR + 0.15,
                4,
                2
            )

    def _handle_learning_card(
        self,
        card: MemoryCard,
        now: datetime,
        rating: Rating
    ) -> tuple[datetime, float, int, int]:
        """处理学习阶段的卡片"""
        if rating == Rating.AGAIN:
            # 重新开始
            return (
                now + timedelta(minutes=self.LEARNING_STEPS[0]),
                max(card.ease_factor - 0.2, self.MIN_EASE_FACTOR),
                0,
                0
            )
        elif rating == Rating.HARD:
            # 继续学习
            step_index = min(card.repetitions, len(self.LEARNING_STEPS) - 1)
            return (
                now + timedelta(minutes=self.LEARNING_STEPS[step_index]),
                max(card.ease_factor - 0.15, self.MIN_EASE_FACTOR),
                0,
                card.repetitions
            )
        elif rating == Rating.GOOD:
            # 毕业到复习阶段
            return (
                now + timedelta(days=self.GRADUATING_INTERVAL),
                card.ease_factor,
                1,
                2
            )
        else:  # EASY
            # 直接毕业，长间隔
            return (
                now + timedelta(days=self.EASY_INTERVAL),
                card.ease_factor + 0.15,
                4,
                2
            )

    def _handle_review_card(
        self,
        card: MemoryCard,
        now: datetime,
        rating: Rating
    ) -> tuple[datetime, float, int, int]:
        """处理复习阶段的卡片（SM-2 算法核心）"""
        if rating == Rating.AGAIN:
            # 遗忘，重新学习
            return (
                now + timedelta(minutes=self.LEARNING_STEPS[0]),
                max(card.ease_factor - 0.2, self.MIN_EASE_FACTOR),
                0,
                0  # 重置 repetitions
            )

        # 计算新的难度因子
        ease_delta = {
            Rating.HARD: -0.15,
            Rating.GOOD: 0,
            Rating.EASY: 0.15
        }[rating]

        new_ease = max(card.ease_factor + ease_delta, self.MIN_EASE_FACTOR)

        # 计算新的间隔
        if rating == Rating.HARD:
            # Hard: 间隔 * 1.2
            new_interval = max(1, int(card.interval * 1.2))
        elif rating == Rating.GOOD:
            # Good: 间隔 * 难度因子
            new_interval = int(card.interval * new_ease)
        else:  # EASY
            # Easy: 间隔 * 难度因子 * 1.3
            new_interval = int(card.interval * new_ease * 1.3)

        return (
            now + timedelta(days=new_interval),
            new_ease,
            new_interval,
            card.repetitions + 1
        )

    def review_card(self, card: MemoryCard, rating: Rating) -> MemoryCard:
        """
        复习卡片，更新状态

        Args:
            card: 要复习的卡片
            rating: 复习评分

        Returns:
            更新后的卡片
        """
        # 计算新的状态
        next_due, new_ease, new_interval, new_reps = self.calculate_next_interval(
            card, rating
        )

        # 更新卡片
        card.due = next_due
        card.ease_factor = new_ease
        card.interval = new_interval
        card.last_reviewed = datetime.now()
        card.total_reviews += 1

        # 更新遗忘次数
        if rating == Rating.AGAIN:
            card.lapses += 1
            card.repetitions = 0
        else:
            card.repetitions = new_reps

        return card

    def get_due_cards(
        self,
        cards: List[MemoryCard],
        deck: Optional[str] = None
    ) -> List[MemoryCard]:
        """
        获取到期的卡片

        Args:
            cards: 所有卡片
            deck: 可选的卡组过滤

        Returns:
            到期的卡片列表（按优先级排序）
        """
        now = datetime.now()

        # 过滤到期的卡片
        due_cards = [
            card for card in cards
            if card.due <= now and (deck is None or card.deck == deck)
        ]

        # 排序：遗忘次数多的优先，然后是到期时间早的
        due_cards.sort(key=lambda c: (c.lapses, c.due), reverse=True)

        return due_cards

    def get_statistics(self, cards: List[MemoryCard]) -> dict:
        """
        获取学习统计

        Returns:
            统计信息字典
        """
        now = datetime.now()

        # 分类统计
        new_cards = [c for c in cards if c.total_reviews == 0]
        learning_cards = [c for c in cards if 0 < c.repetitions < 2]
        review_cards = [c for c in cards if c.repetitions >= 2]

        due_cards = [c for c in cards if c.due <= now]

        return {
            "total": len(cards),
            "new": len(new_cards),
            "learning": len(learning_cards),
            "review": len(review_cards),
            "due": len(due_cards),
            "average_ease": sum(c.ease_factor for c in cards) / len(cards) if cards else 0,
            "total_reviews_today": sum(
                1 for c in cards
                if c.last_reviewed and c.last_reviewed.date() == now.date()
            )
        }
