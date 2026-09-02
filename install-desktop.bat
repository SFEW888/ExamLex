@echo off
echo ============================================================
echo ExamLex 桌面应用 - 安装依赖
echo ============================================================
echo.

REM 检查 Node.js
where node >nul 2>nul
if errorlevel 1 (
    echo ❌ 未安装 Node.js
    echo 请从 https://nodejs.org/ 下载安装 Node.js
    pause
    exit /b 1
)

echo ✅ Node.js 已安装
node --version
echo.

REM 检查 Python
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ 未安装 Python
    echo 请从 https://www.python.org/ 下载安装 Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python 已安装
python --version
echo.

REM 安装 Node.js 依赖
echo [1/3] 安装 Node.js 依赖...
call npm install
if errorlevel 1 (
    echo ❌ Node.js 依赖安装失败
    pause
    exit /b 1
)
echo ✅ Node.js 依赖安装完成
echo.

REM 安装 Python 依赖
echo [2/3] 安装 Python 依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ❌ Python 依赖安装失败
    pause
    exit /b 1
)
echo ✅ Python 依赖安装完成
echo.

REM 检查 .env 文件
echo [3/3] 检查配置文件...
if not exist ".env" (
    echo ⚠️  未找到 .env 文件
    echo 已从 .env.example 创建 .env
    copy .env.example .env
    echo.
    echo ⚠️  请编辑 .env 文件，添加至少一个 LLM 供应商的 API Key
    echo 例如：OPENAI_API_KEY=sk-...
    echo.
)
echo ✅ 配置文件检查完成
echo.

echo ============================================================
echo 🎉 所有依赖安装完成！
echo ============================================================
echo.
echo 下一步：
echo 1. 编辑 .env 文件，添加 API Key
echo 2. 运行 npm start 启动应用
echo 3. 或运行 npm run build:win 打包成 .exe
echo.

pause
