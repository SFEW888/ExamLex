# ExamLex 2.0 - AI 驱动的英语备考系统

**学习管理系统 + 可选 LangGraph AI Agent + 多供应商支持**

---

## 🎯 核心特性

### 1. Agent 系统
- ✅ **全局 AI Assistant** - 任意页面通过右下角入口或 `Ctrl/⌘ + J` 唤醒，按当前路由自动选择专属场景 Agent
- ✅ **统一 Agent runtime** - 写作、听力、阅读、翻译、词汇、基础知识、规划和错题复盘
- ✅ **离线 deterministic fallback** - 没有 API Key 也可运行并保留证据结构
- ✅ **可选 LangGraph** - 安装后自动使用 StateGraph 编排相同节点
- ✅ **本地 RAG 检索** - 每次运行从考试内容、基础知识、练习记录、记忆卡、上传资料和持续学习队列检索可追溯证据

> 当前 RAG 使用标准库实现的本地 lexical retrieval（词法检索），不是向量数据库。模型未配置或调用失败时会自动回退到本地证据分析，不会伪造模型结果。

### 2. 多供应商 LLM 支持
- ✅ OpenAI (GPT-4, GPT-3.5-Turbo)
- ✅ Anthropic (Claude 3)
- ✅ DeepSeek
- ✅ Kimi (Moonshot)
- ✅ 通义千问 (Qwen)
- ✅ 本地模型 (Ollama)
- ✅ 自定义供应商

### 3. 学习管理功能
- ✅ 学习热力图
- ✅ 待办事项
- ✅ 记忆卡系统
- ✅ 错题分析
- ✅ 每日总结
- ✅ 记忆卡只从练习记录或确认后的上传资料生成，不预置固定卡片

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，至少配置一个供应商的 API Key
# 例如：
OPENAI_API_KEY=sk-your-key-here
# 或
DEEPSEEK_API_KEY=sk-your-key-here
```

### 3. 启动服务

```bash
# 本地优先 Web 服务（无需 FastAPI/模型 Key 即可运行）
python -m skills.examlex.scripts.web_app --host 127.0.0.1 --port 8765
```

### 4. 访问应用

- **前端界面**: http://localhost:8765
- **Agent API**: `POST /api/agent/run`
- **Agent 清单**: `GET /api/agent/manifest`

---

## 📁 项目结构

```
ExamLex/
├── skills/examlex/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── providers.py          # 供应商配置
│   ├── core/
│   │   ├── __init__.py
│   │   └── provider_manager.py   # 供应商管理器
│   ├── agents/
│   │   ├── __init__.py
│   │   └── writing_agent.py      # 写作 Agent (LangGraph)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI 主应用
│   │   ├── providers.py          # 供应商 API
│   │   └── agents.py             # Agent API
│   └── assets/web/
│       ├── index.html            # 前端页面
│       ├── styles.css
│       ├── components.css
│       └── app.js
├── .env.example                  # 环境变量模板
├── requirements.txt              # Python 依赖
└── README.md                     # 本文件
```

---

## 🔧 使用示例

### 1. 切换 LLM 供应商

```bash
# 列出所有供应商
curl http://localhost:8765/api/providers

# 设置当前供应商
curl -X POST http://localhost:8765/api/providers/set \
  -H "Content-Type: application/json" \
  -d '{"provider": "deepseek", "model": "deepseek-chat"}'

# 测试连接
curl -X POST http://localhost:8765/api/providers/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "deepseek"}'
```

### 2. Agent 运行

```bash
curl -X POST http://localhost:8765/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "exam": "CET6",
    "module": "writing",
    "input": "Nowadays, many people think that social media is very important...",
    "use_model": false
  }'
```

返回示例：
```json
{
  "success": true,
  "run": {
    "mode": "deterministic",
    "output": {"findings": [...], "next_action": "...", "evidence": [...]}
  }
}
```

---

## 🤖 LangGraph 工作流

### Writing Agent 流程

```
用户提交作文
    ↓
Orchestrator (初始化)
    ↓
Writing Agent (结构分析)
    ↓
Grammar Agent (语法检查)
    ↓
Vocabulary Agent (词汇建议)
    ↓
Synthesize (综合反馈)
    ↓
Should Refine? (分数 < 75?)
    ↙        ↘
  Yes        No
   ↓          ↓
 Refine     END
   ↓
(循环回 Writing Agent)
```

---

## 📊 API 端点

## Evidence-first answer rendering

All detailed answer output follows [`answer-explanation-standard.md`](skills/examlex/references/answer-explanation-standard.md). The `image-mapped-answerbook-contract` keeps each bilingual question, evidence anchor, reasoning steps, and distractor analysis in the same item block instead of replacing source-backed analysis with a summary.

Local strategy data grows in a controlled way as effective new material is added. Duplicate review remains explicit through `--duplicates`; important strategy and history records are never deleted automatically.

### 供应商管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/providers` | 列出所有供应商 |
| GET | `/api/providers/{provider}` | 获取供应商详情 |
| POST | `/api/providers/set` | 设置当前供应商 |
| POST | `/api/providers/test` | 测试供应商连接 |
| POST | `/api/providers/custom` | 添加自定义供应商 |
| GET | `/api/providers/current/info` | 获取当前供应商信息 |

### Agent API

| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/agent/writing` | 作文批改 | ✅ 已实现 |
| POST | `/api/agent/listening` | 听力分析 | ⏳ 开发中 |
| POST | `/api/agent/reading` | 阅读理解 | ⏳ 开发中 |
| POST | `/api/agent/vocabulary` | 词汇分析 | ⏳ 开发中 |
| POST | `/api/agent/translation` | 翻译优化 | ⏳ 开发中 |

---

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代化 Web 框架
- **LangGraph** - AI Agent 工作流编排
- **LangChain** - LLM 应用开发框架
- **Pydantic** - 数据验证
- **SQLAlchemy** - 数据库 ORM

### 前端
- **纯 HTML/CSS/JS** - 无框架依赖
- **响应式设计** - 移动端适配

### LLM 供应商
- OpenAI、Anthropic、DeepSeek、Kimi、Qwen、Ollama

---

## 📝 开发计划

### ✅ Phase 1: 核心架构（已完成）
- [x] 供应商管理系统
- [x] LangGraph 工作流
- [x] Writing Agent
- [x] FastAPI 后端
- [x] 前端界面

### ⏳ Phase 2: 其他 Agent（进行中）
- [ ] Listening Agent
- [ ] Reading Agent
- [ ] Vocabulary Agent
- [ ] Translation Agent

### 📅 Phase 3: 私人版边界
- [x] 本地 RAG 检索与 ExamLex 题源/解析标准
- [x] 本地数据持久化与学习进度追踪
- [x] 多 Provider 配置与离线 fallback
- [ ] 题源采集、视频处理、备份恢复等后台任务

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent 工作流
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Anki](https://github.com/ankitects/anki) - 间隔重复算法
- [zsb-study-tracker](https://github.com/Han050912/zsb-study-tracker) - UI 设计灵感

---

**ExamLex 2.0** - 用 AI 驱动的学习系统，让备考更高效！🚀
