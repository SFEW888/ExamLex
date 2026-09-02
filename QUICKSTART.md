# ExamLex 2.0 快速启动指南

## 🚀 5分钟快速上手

### 步骤 1：安装依赖（1分钟）

```bash
pip install -r requirements.txt
```

### 步骤 2：配置 API Key（1分钟）

编辑 `.env` 文件，添加至少一个供应商的 API Key：

```bash
# 选择一个你有的 API Key 配置
OPENAI_API_KEY=sk-your-key-here
# 或
DEEPSEEK_API_KEY=sk-your-key-here
# 或
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 步骤 3：启动服务（立即）

```bash
python -m skills.examlex.api.main
```

看到以下输出表示启动成功：

```
============================================================
🚀 ExamLex 2.0 启动中...
============================================================
📍 服务地址: http://0.0.0.0:8765
📚 API 文档: http://0.0.0.0:8765/docs
🔧 供应商管理: http://0.0.0.0:8765/api/providers
🤖 Agent API: http://0.0.0.0:8765/api/agent
============================================================
```

### 步骤 4：访问应用

打开浏览器访问：
- **前端界面**: http://localhost:8765
- **API 文档**: http://localhost:8765/docs

---

## 🧪 快速测试

### 1. 测试健康检查

```bash
curl http://localhost:8765/health
```

### 2. 列出所有供应商

```bash
curl http://localhost:8765/api/providers
```

### 3. 设置供应商

```bash
curl -X POST http://localhost:8765/api/providers/set \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "model": "gpt-4"}'
```

### 4. 作文批改（核心功能）

```bash
curl -X POST http://localhost:8765/api/agent/writing \
  -H "Content-Type: application/json" \
  -d '{
    "essay": "Nowadays, many people think that social media is very important. I agree with this opinion. There are a lot of reasons. First, social media helps us connect with friends. We can talk to them anytime. Second, we can learn a lot of things from social media. In conclusion, social media is very important for our life.",
    "exam_type": "CET-6",
    "user_id": "test_user"
  }'
```

你会看到详细的批改结果：
- 综合分数
- 结构分析
- 语法问题
- 词汇建议
- 优化后的作文

---

## 🎯 核心功能演示

### Writing Agent 工作流

```
用户提交作文
    ↓
Orchestrator (初始化状态)
    ↓
Writing Agent (结构分析)
    ↓
Grammar Agent (语法检查)
    ↓
Vocabulary Agent (词汇建议)
    ↓
Synthesize (综合反馈)
    ↓
判断：分数 < 75?
    ↙        ↘
  Yes        No
   ↓          ↓
 Refine     END
   ↓
(循环回 Writing Agent)
```

---

## ❓ 常见问题

### Q: 启动时报错 "未找到 API Key"

**A**: 检查 `.env` 文件是否正确配置了 API Key。

### Q: 如何切换供应商？

**A**: 
1. 前端界面：点击设置 → 选择供应商
2. API 调用：`POST /api/providers/set`

### Q: 支持哪些 LLM 供应商？

**A**:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- DeepSeek
- Kimi (Moonshot)
- 通义千问 (Qwen)
- 本地模型 (Ollama)
- 自定义供应商

### Q: 如何使用本地模型？

**A**: 
1. 安装 Ollama: https://ollama.ai
2. 启动模型: `ollama run llama3`
3. 设置供应商为 `local`

---

## 📚 下一步

1. ✅ 测试 Writing Agent
2. ✅ 切换不同的 LLM 供应商
3. ✅ 查看 API 文档学习更多功能
4. ⏳ 等待其他 Agent 开发完成（听力、阅读等）
5. ⏳ 集成 RAG 知识库

---

**享受 AI 驱动的学习体验！** 🎉
