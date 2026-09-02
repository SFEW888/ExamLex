"""
Agent API 端点
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..agents.writing_agent import writing_workflow

router = APIRouter(prefix="/api/agent", tags=["agents"])

class EssayReviewRequest(BaseModel):
    essay: str
    exam_type: str = "CET-6"
    user_id: str = "default"

@router.post("/writing")
async def review_essay(request: EssayReviewRequest):
    """
    作文批改 API

    使用 LangGraph 工作流分析作文：
    1. 结构分析
    2. 语法检查
    3. 词汇建议
    4. 综合反馈
    5. 自动优化（如果分数低于75分）
    """
    try:
        # 执行 LangGraph 工作流
        result = writing_workflow.invoke({
            "essay": request.essay,
            "exam_type": request.exam_type,
            "user_id": request.user_id
        })

        return {
            "success": True,
            "score": result["score"],
            "feedback": result["final_feedback"],
            "revised_essay": result.get("revised_essay"),
            "iteration_count": result["iteration_count"],
            "details": {
                "structure": result["structure_analysis"],
                "grammar": result["grammar_issues"],
                "vocabulary": result["vocabulary_suggestions"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"作文批改失败: {str(e)}")

@router.get("/writing/status")
async def get_writing_agent_status():
    """获取 Writing Agent 状态"""
    return {
        "agent": "writing_agent",
        "status": "active",
        "workflow": "LangGraph",
        "nodes": [
            "orchestrator",
            "writing_agent",
            "grammar_agent",
            "vocabulary_agent",
            "synthesize",
            "refine"
        ]
    }

# 预留其他 Agent 端点
@router.post("/listening")
async def listening_analysis(data: dict):
    """听力分析 API（待实现）"""
    raise HTTPException(status_code=501, detail="听力 Agent 开发中...")

@router.post("/reading")
async def reading_analysis(data: dict):
    """阅读分析 API（待实现）"""
    raise HTTPException(status_code=501, detail="阅读 Agent 开发中...")

@router.post("/vocabulary")
async def vocabulary_analysis(data: dict):
    """词汇分析 API（待实现）"""
    raise HTTPException(status_code=501, detail="词汇 Agent 开发中...")

@router.post("/translation")
async def translation_analysis(data: dict):
    """翻译分析 API（待实现）"""
    raise HTTPException(status_code=501, detail="翻译 Agent 开发中...")
