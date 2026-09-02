# ExamLex 桌面版 - 快速启动指南

## 🎯 什么是桌面版？

**ExamLex 桌面版** 是一个 Electron 应用，双击即可启动，无需手动启动服务器！

```
双击启动 → 自动启动 Python 后端 → 显示加载动画 → 自动打开主界面
```

---

## 🚀 3 步快速启动

### 步骤 1: 安装依赖（第一次需要，约 2 分钟）

```bash
# 双击运行
install-desktop.bat

# 或命令行
npm install
pip install -r requirements.txt
```

**安装内容**：
- ✅ Node.js 依赖（Electron、axios 等）
- ✅ Python 依赖（基础服务无需 FastAPI；LangGraph、FSRS 可选）

### 步骤 2: 配置 API Key（1 分钟）

编辑 `.env` 文件，添加至少一个 LLM 供应商的 API Key：

```bash
# 选择一个你有的 API Key
OPENAI_API_KEY=sk-your-openai-key
# 或
DEEPSEEK_API_KEY=sk-your-deepseek-key
# 或
ANTHROPIC_API_KEY=sk-ant-your-claude-key
```

### 步骤 3: 启动应用（立即）

```bash
# 方式 1: 双击启动（推荐）
双击 start-desktop.bat

# 方式 2: 命令行启动
npm start
```

**启动流程**：
1. Electron 窗口打开
2. 显示加载动画
3. 自动启动 Python 后端（约 10-30 秒）
4. 后端就绪后自动跳转到主界面

---

## 📦 打包成安装程序

### 打包 Windows .exe

```bash
# 方式 1: 双击打包脚本
双击 build-desktop.bat

# 方式 2: 命令行打包
npm run build:win
```

**打包时间**：约 3-5 分钟

**输出文件**：`dist\ExamLex Setup 2.0.0.exe`

**安装后**：
- 开始菜单快捷方式
- 桌面快捷方式（可选）
- 双击即可启动

### 打包其他平台

```bash
# macOS
npm run build:mac

# Linux
npm run build:linux
```

---

## 🎯 桌面版 vs Web 版

| 特性 | 桌面版 | Web 版 |
|------|--------|--------|
| 启动方式 | 双击启动 | 需手动启动服务器 |
| 后端管理 | 自动启动/停止 | 手动管理 |
| 用户体验 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 打包分发 | ✅ 可打包成 .exe | ❌ 需安装 Python 环境 |
| 跨平台 | ✅ Windows/Mac/Linux | ✅ 任何浏览器 |

**推荐使用桌面版！**

---

## 🛠️ 技术架构

```
┌─────────────────────────────────────┐
│      Electron 窗口                   │
│      (加载动画 → 主界面)             │
└────────────┬────────────────────────┘
             │ 自动管理
             ▼
┌─────────────────────────────────────┐
│      Python 后端                     │
│      • Local Web + Agent runtime    │
│      • LangGraph Agent              │
│      • 供应商管理                    │
└─────────────────────────────────────┘
```

**工作流程**：
1. Electron 启动 → 显示加载页面
2. 自动启动 Python 后端（spawn 子进程）
3. 轮询检查后端健康（最多 30 秒）
4. 后端就绪 → 加载主界面
5. 后端失败 → 显示错误页面

---

## 🐛 常见问题

### Q1: 启动失败 "Python 后端启动失败"

**原因**：
- Python 未安装
- Python 依赖未安装
- 端口 8765 被占用
- .env 配置错误

**解决**：
1. 检查 Python：`python --version`（需要 3.8+）
2. 安装依赖：`pip install -r requirements.txt`
3. 检查端口：`netstat -ano | findstr 8765`
4. 检查 .env：确保至少有一个 API Key

### Q2: 双击 install-desktop.bat 没反应

**原因**：
- Node.js 未安装

**解决**：
1. 安装 Node.js：https://nodejs.org/
2. 选择 LTS 版本（推荐）
3. 安装完成后重启电脑
4. 重新运行 install-desktop.bat

### Q3: 打包失败

**原因**：
- 磁盘空间不足
- 杀毒软件拦截
- 依赖未安装

**解决**：
1. 确保至少有 500MB 空间
2. 临时关闭杀毒软件
3. 重新安装依赖：`npm install`
4. 重试打包

### Q4: 启动慢

**正常现象**：
- 第一次启动需要加载 Python 环境：10-30 秒
- 后续启动会更快：5-10 秒

**优化**：
- 使用 SSD 硬盘
- 关闭不必要的后台程序

### Q5: 如何卸载？

**桌面版（未打包）**：
- 直接删除项目文件夹

**安装版（已打包）**：
- Windows：控制面板 → 程序和功能 → 卸载 ExamLex
- 或：设置 → 应用 → ExamLex → 卸载

---

## 📊 文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `desktop/main.js` | Electron 主进程（窗口管理、后端启动） |
| `desktop/preload.js` | 预加载脚本（安全通信） |
| `desktop/loading.html` | 加载动画页面 |
| `desktop/error.html` | 错误提示页面 |
| `package.json` | Node.js 配置（依赖、打包配置） |

### 脚本文件

| 文件 | 说明 |
|------|------|
| `install-desktop.bat` | 安装所有依赖（Node.js + Python） |
| `start-desktop.bat` | 启动桌面应用 |
| `build-desktop.bat` | 打包成 Windows 安装程序 |

---

## 🎨 自定义配置

### 修改端口

编辑 `desktop/main.js`：

```javascript
const BACKEND_PORT = 8765; // 改为其他端口
```

### 修改窗口大小

编辑 `desktop/main.js`：

```javascript
mainWindow = new BrowserWindow({
  width: 1400,  // 改为你想要的宽度
  height: 900,  // 改为你想要的高度
  // ...
});
```

### 自定义应用图标

1. 准备图标文件：
   - Windows: `desktop/icon.ico` (256x256)
   - Mac: `desktop/icon.icns`
   - Linux: `desktop/icon.png` (512x512)

2. 重新打包即可

---

## 🎉 总结

**ExamLex 桌面版已就绪！**

**你现在可以**：
- ✅ 双击启动应用（无需手动启动服务器）
- ✅ 自动管理后端（自动启动/停止）
- ✅ 打包成安装程序（分发给他人使用）

**立即体验**：
1. 双击 `install-desktop.bat` 安装依赖
2. 编辑 `.env` 添加 API Key
3. 双击 `start-desktop.bat` 启动！

**需要帮助？** 查看 `DESKTOP_README.md` 获取更多信息。

---

**ExamLex Desktop 2.0** - 双击即用的 AI 学习系统！🚀
