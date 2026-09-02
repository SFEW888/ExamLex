@echo off
echo ============================================================
echo ExamLex 桌面应用 - 打包为 Windows 安装程序
echo ============================================================
echo.

REM 检查依赖
if not exist "node_modules\" (
    echo ⚠️  Node.js 依赖未安装
    echo 正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo [1/2] 清理旧的构建文件...
if exist "dist\" rmdir /s /q dist
echo ✅ 清理完成
echo.

echo [2/2] 开始打包...
echo 这可能需要几分钟，请耐心等待...
echo.

npm run build:win

if errorlevel 1 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 🎉 打包完成！
echo ============================================================
echo.
echo 安装程序位置：
echo   dist\ExamLex Setup 2.0.0.exe
echo.
echo 双击安装程序即可安装 ExamLex 桌面应用
echo.

pause
