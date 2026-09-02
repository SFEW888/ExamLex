@echo off
echo ============================================================
echo ExamLex 2.0 - AI 驱动的英语备考系统
echo ============================================================
echo.

REM 检查虚拟环境
if not exist "venv\" (
    echo [1/4] 创建虚拟环境...
    python -m venv venv
    echo ✅ 虚拟环境创建完成
    echo.
)

REM 激活虚拟环境
echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat
echo ✅ 虚拟环境已激活
echo.

REM 安装依赖
echo [3/4] 检查依赖...
pip list | findstr /C:"fastapi" >nul
if errorlevel 1 (
    echo 正在安装依赖，这可能需要几分钟...
    pip install -r requirements.txt -q
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖已安装
)
echo.

REM .env 仅用于启用模型模式；没有配置时仍可使用本地 deterministic fallback。
if not exist ".env" echo [提示] 未找到 .env，将使用离线 Agent 模式。

REM 启动服务
echo [4/4] 启动 ExamLex 2.0...
echo.
echo ============================================================
echo 🚀 服务启动成功！
echo ============================================================
echo 📍 前端界面: http://localhost:8765
echo 📚 API 文档: http://localhost:8765/docs
echo 🔧 供应商管理: http://localhost:8765/api/providers
echo 🤖 Agent API: http://localhost:8765/api/agent
echo ============================================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python -m skills.examlex.scripts.web_app --host 127.0.0.1 --port 8765

pause
