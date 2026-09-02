"""
学习记录 API
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from pathlib import Path

from ..core.study_records import StudyRecordManager

router = APIRouter(prefix="/api/study", tags=["study"])

# 初始化记录管理器
DATA_DIR = Path(__file__).parent.parent / "data"
record_manager = StudyRecordManager(DATA_DIR)


@router.get("/heatmap")
async def get_heatmap_data(days: int = 365):
    """
    获取热力图数据

    Query Params:
        days: 获取最近多少天的数据（默认 365 天）
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    data = record_manager.get_heatmap_data(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )

    return {
        "success": True,
        "data": data,
        "total_days": len(data)
    }


@router.get("/statistics")
async def get_statistics(days: int = 30):
    """
    获取学习统计

    Query Params:
        days: 统计最近多少天（默认 30 天）
    """
    stats = record_manager.get_statistics(days)

    return {
        "success": True,
        **stats
    }


@router.post("/record")
async def record_activity(
    activity_type: str,
    duration: int = 0,
    count: int = 1
):
    """
    记录学习活动

    Body:
        activity_type: 活动类型 (cards/essay/listening/reading/words)
        duration: 持续时间（分钟）
        count: 数量
    """
    record_manager.record_activity(activity_type, duration, count)

    return {
        "success": True,
        "message": "学习记录已保存"
    }


@router.get("/today")
async def get_today_record():
    """获取今日学习记录"""
    today = datetime.now().strftime('%Y-%m-%d')
    record = record_manager.get_record(today)

    if record:
        return {
            "success": True,
            "record": record.dict(),
            "activity_score": record.get_activity_score()
        }

    return {
        "success": True,
        "record": None,
        "activity_score": 0
    }
