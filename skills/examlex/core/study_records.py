"""
学习记录系统 - 用于热力图数据
"""

from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import json
from pathlib import Path


class StudyRecord(BaseModel):
    """学习记录"""
    date: str  # YYYY-MM-DD
    duration: int  # 学习时长（分钟）
    cards_reviewed: int = 0  # 复习卡片数
    essays_written: int = 0  # 写作批改数
    listening_exercises: int = 0  # 听力练习数
    reading_exercises: int = 0  # 阅读练习数
    words_learned: int = 0  # 学习单词数

    # 计算当天总活跃度（0-100）
    def get_activity_score(self) -> int:
        """计算活跃度分数"""
        score = 0
        score += min(self.duration // 5, 20)  # 最多 20 分（100分钟）
        score += min(self.cards_reviewed * 2, 20)  # 最多 20 分（10张卡片）
        score += min(self.essays_written * 10, 20)  # 最多 20 分（2篇作文）
        score += min(self.listening_exercises * 5, 15)  # 最多 15 分
        score += min(self.reading_exercises * 5, 15)  # 最多 15 分
        score += min(self.words_learned, 10)  # 最多 10 分
        return min(score, 100)


class StudyRecordManager:
    """学习记录管理器"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.records_file = data_dir / "study_records.json"
        self.records: List[StudyRecord] = []
        self.load_records()

    def load_records(self):
        """从文件加载记录"""
        if self.records_file.exists():
            with open(self.records_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.records = [StudyRecord(**r) for r in data]

    def save_records(self):
        """保存记录到文件"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.records_file, 'w', encoding='utf-8') as f:
            data = [r.dict() for r in self.records]
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_record(self, date: str) -> Optional[StudyRecord]:
        """获取指定日期的记录"""
        for record in self.records:
            if record.date == date:
                return record
        return None

    def add_or_update_record(self, date: str, **updates) -> StudyRecord:
        """添加或更新记录"""
        record = self.get_record(date)

        if record:
            # 更新现有记录
            for key, value in updates.items():
                if hasattr(record, key):
                    current = getattr(record, key)
                    setattr(record, key, current + value)
        else:
            # 创建新记录
            record = StudyRecord(date=date, **updates)
            self.records.append(record)

        self.save_records()
        return record

    def get_heatmap_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取热力图数据

        Returns:
            [
                {"date": "2026-09-01", "value": 85},
                {"date": "2026-09-02", "value": 60},
                ...
            ]
        """
        # 默认获取最近 365 天
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if not start_date:
            start = datetime.now() - timedelta(days=365)
            start_date = start.strftime('%Y-%m-%d')

        # 生成日期范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        result = []
        current = start_dt

        while current <= end_dt:
            date_str = current.strftime('%Y-%m-%d')
            record = self.get_record(date_str)

            value = 0
            if record:
                value = record.get_activity_score()

            result.append({
                "date": date_str,
                "value": value,
                "duration": record.duration if record else 0,
                "cards": record.cards_reviewed if record else 0,
                "essays": record.essays_written if record else 0
            })

            current += timedelta(days=1)

        return result

    def get_statistics(self, days: int = 30) -> dict:
        """
        获取统计数据

        Args:
            days: 统计最近多少天
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        total_duration = 0
        total_cards = 0
        total_essays = 0
        active_days = 0

        for record in self.records:
            record_date = datetime.strptime(record.date, '%Y-%m-%d')
            if start_date <= record_date <= end_date:
                if record.get_activity_score() > 0:
                    active_days += 1
                total_duration += record.duration
                total_cards += record.cards_reviewed
                total_essays += record.essays_written

        return {
            "period_days": days,
            "active_days": active_days,
            "total_duration": total_duration,
            "avg_duration": total_duration // max(active_days, 1),
            "total_cards": total_cards,
            "total_essays": total_essays,
            "streak": self.get_current_streak()
        }

    def get_current_streak(self) -> int:
        """获取当前连续学习天数"""
        today = datetime.now().date()
        streak = 0

        current_date = today
        while True:
            date_str = current_date.strftime('%Y-%m-%d')
            record = self.get_record(date_str)

            if record and record.get_activity_score() > 0:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break

        return streak

    def record_activity(
        self,
        activity_type: str,
        duration: int = 0,
        count: int = 1
    ):
        """
        记录学习活动

        Args:
            activity_type: 活动类型 (cards/essay/listening/reading/words)
            duration: 持续时间（分钟）
            count: 数量
        """
        today = datetime.now().strftime('%Y-%m-%d')

        updates = {"duration": duration}

        if activity_type == "cards":
            updates["cards_reviewed"] = count
        elif activity_type == "essay":
            updates["essays_written"] = count
        elif activity_type == "listening":
            updates["listening_exercises"] = count
        elif activity_type == "reading":
            updates["reading_exercises"] = count
        elif activity_type == "words":
            updates["words_learned"] = count

        self.add_or_update_record(today, **updates)
