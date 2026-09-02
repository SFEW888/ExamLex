@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║            ExamLex 2.0 - 一键安装并启动                          ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM 检查 .env 文件
if not exist ".env" echo [提示] 未找到 .env，将使用离线 Agent 模式。

echo [1/3] 正在安装 Python 依赖...
echo 这可能需要 1-2 分钟，请耐心等待...
echo.

pip install -r requirements.txt -q

if errorlevel 1 (
    echo.
    echo [错误] Python 依赖安装失败
    echo 请检查网络连接或手动运行：
    echo pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo ✅ Python 依赖安装完成
echo.

echo [2/3] 正在检查配置...
findstr /C:"OPENAI_API_KEY" .env | findstr /V /C:"your-key" >nul
if errorlevel 1 (
    findstr /C:"DEEPSEEK_API_KEY" .env | findstr /V /C:"your-key" >nul
    if errorlevel 1 (
        findstr /C:"ANTHROPIC_API_KEY" .env | findstr /V /C:"your-key" >nul
        if errorlevel 1 (
            echo.
            echo [警告] 未在 .env 中找到有效的 API Key
            echo 请编辑 .env 文件，添加至少一个 API Key
            echo.
            pause
            exit /b 1
        )
    )
)

echo ✅ 配置检查完成
echo.

echo [3/3] 正在启动 ExamLex...
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                    ExamLex 2.0 已启动！                          ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo 📍 访问地址: http://localhost:8765
echo 📚 API 文档: http://localhost:8765/docs
echo.
echo ⚠️  请不要关闭此窗口！
echo 按 Ctrl+C 可以停止服务
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python -m skills.examlex.scripts.web_app --host 127.0.0.1 --port 8765

pause
