@echo off
echo ============================================================
echo ExamLex 桌面应用 - 启动中
echo ============================================================
echo.

REM 检查依赖是否安装
if not exist "node_modules\" (
    echo ⚠️  Node.js 依赖未安装
    echo 正在运行安装脚本...
    call install-desktop.bat
    if errorlevel 1 (
        pause
        exit /b 1
    )
)

REM 检查 .env 文件
if not exist ".env" echo [提示] 未找到 .env，将使用离线 Agent 模式。

echo ✅ 正在启动 ExamLex...
echo.

npm start
