"""
ExamLex FastAPI 主应用
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入路由
from .providers import router as providers_router
from .agents import router as agents_router
from .memory import router as memory_router
from .study import router as study_router
from .vocabulary import router as vocabulary_router

# 创建 FastAPI 应用
app = FastAPI(
    title="ExamLex API",
    description="学习管理 + AI Agent 系统",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(providers_router)
app.include_router(agents_router)
app.include_router(memory_router)
app.include_router(study_router)
app.include_router(vocabulary_router)

# 静态文件服务
ASSETS_DIR = Path(__file__).parent.parent / "assets" / "web"
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

@app.get("/")
async def root():
    """返回前端页面"""
    index_html = ASSETS_DIR / "index.html"
    if index_html.exists():
        return FileResponse(str(index_html))
    return {"message": "ExamLex API is running"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "LangGraph Agent System",
            "Multi-Provider Support",
            "Learning Management"
        ]
    }

@app.get("/api/config")
async def get_config():
    """获取前端配置"""
    return {
        "app_name": "ExamLex",
        "version": "2.0.0",
        "features": {
            "agents": ["writing", "listening", "reading", "vocabulary", "translation"],
            "providers": ["openai", "anthropic", "deepseek", "kimi", "qwen", "local"]
        }
    }

# 错误处理
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "未找到资源"}
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误"}
    )

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8765))

    print("=" * 60)
    print("🚀 ExamLex 2.0 启动中...")
    print("=" * 60)
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"📚 API 文档: http://{host}:{port}/docs")
    print(f"🔧 供应商管理: http://{host}:{port}/api/providers")
    print(f"🤖 Agent API: http://{host}:{port}/api/agent")
    print("=" * 60)

    uvicorn.run(
        "skills.examlex.api.main:app",
        host=host,
        port=port,
        reload=True
    )
