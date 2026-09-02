# ExamLex 桌面客户端

## 🎯 桌面应用架构

```
ExamLex Desktop
├── Electron 主进程
│   ├── 窗口管理
│   ├── 自动启动 Python 后端
│   └── IPC 通信
├── Python 本地 Web 后端（标准库，LangGraph/FSRS 可选）
│   ├── LangGraph Agent
│   ├── 供应商管理
│   └── API 服务
└── Web 前端（Renderer）
    ├── HTML/CSS/JS
    └── 与后端通信
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 运行安装脚本
.\install-desktop.bat

# 或手动安装
npm install
pip install -r requirements.txt
```

### 2. 配置 API Key

编辑 `.env` 文件，添加至少一个 LLM 供应商的 API Key：

```bash
OPENAI_API_KEY=sk-your-key-here
# 或
DEEPSEEK_API_KEY=sk-your-key-here
```

### 3. 启动应用

```bash
# 方式 1: 双击启动脚本
双击 start-desktop.bat

# 方式 2: 命令行启动
npm start
```

---

## 📦 打包为可执行文件

### 打包 Windows 安装程序

```bash
# 方式 1: 使用打包脚本
.\build-desktop.bat

# 方式 2: 命令行打包
npm run build:win
```

打包完成后，安装程序位于：`dist\ExamLex Setup 2.0.0.exe`

### 打包其他平台

```bash
# macOS
npm run build:mac

# Linux
npm run build:linux
```

---

## 🎯 桌面应用特性

✅ **双击启动** - 无需手动启动服务器  
✅ **自动后端** - Electron 自动启动 Python 后端  
✅ **加载动画** - 启动时显示漂亮的加载界面  
✅ **错误处理** - 后端启动失败时显示错误页面  
✅ **跨平台** - 支持 Windows/Mac/Linux  
✅ **打包安装** - 可打包成 .exe 安装程序  

---

## 🛠️ 技术栈

- **Electron** - 桌面应用框架
- **Node.js** - JavaScript 运行时
- **Python** - 后端服务
- **Python http.server** - 本地优先 Web 服务
- **LangGraph / FSRS** - 可选 Agent 编排与复习调度
- **LangGraph** - AI Agent 工作流

---

## 📁 目录结构

```
ExamLex/
├── desktop/
│   ├── main.js              # Electron 主进程
│   ├── preload.js           # 预加载脚本
│   ├── loading.html         # 加载页面
│   ├── error.html           # 错误页面
│   └── icon.png             # 应用图标
├── skills/examlex/          # Python 后端
├── package.json             # Node.js 配置
├── install-desktop.bat      # 安装脚本
├── start-desktop.bat        # 启动脚本
└── build-desktop.bat        # 打包脚本
```

---

## 🐛 常见问题

### Q: 启动失败 "Python 后端启动失败"

**A**: 
1. 确保安装了 Python 3.8+：`python --version`
2. 安装 Python 依赖：`pip install -r requirements.txt`
3. 检查 .env 文件是否配置了 API Key

### Q: 打包失败

**A**: 
1. 确保安装了所有依赖：`npm install`
2. 检查磁盘空间是否充足（至少 500MB）
3. 关闭杀毒软件重试

### Q: 应用启动慢

**A**: 
- 第一次启动需要加载 Python 环境，约 10-30 秒
- 后续启动会更快（约 5-10 秒）

### Q: 端口被占用

**A**: 
- 修改 `desktop/main.js` 中的 `BACKEND_PORT = 8765` 为其他端口

---

## 🎨 自定义应用图标

1. 准备图标文件：
   - Windows: `desktop/icon.ico` (256x256)
   - Mac: `desktop/icon.icns`
   - Linux: `desktop/icon.png` (512x512)

2. 重新打包：
   ```bash
   npm run build:win
   ```

---

## 📊 打包体积优化

打包后的应用大小约：
- Windows 安装程序：约 150-200 MB
- Mac DMG：约 180-220 MB
- Linux AppImage：约 170-210 MB

优化建议：
1. 使用 `asar` 打包（已默认启用）
2. 排除不必要的文件
3. 压缩 Python 依赖

---

## 🔄 更新应用

### 方式 1: 手动更新
1. 下载新版本安装程序
2. 运行安装程序覆盖安装

### 方式 2: 自动更新（待实现）
- 集成 `electron-updater`
- 应用启动时自动检查更新

---

## 🎉 完成！

现在你有：
- ✅ 完整的桌面应用
- ✅ 一键启动脚本
- ✅ 打包安装程序

**立即体验**：双击 `start-desktop.bat` 启动应用！ 🚀
