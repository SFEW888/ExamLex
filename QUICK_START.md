# ExamLex 2.0 快速启动指南

## 🚀 立即开始

### 1. 启动应用

```bash
# Windows
一键启动.bat

# 或者手动启动
cd D:\Codex_project\英语\.worktrees\ExamLex-public
python skills\examlex\scripts\web_app.py
```

应用将在 `http://localhost:8765` 启动

---

## ✅ 功能测试清单

### 📝 记忆卡系统（Anki SM-2）

**步骤**：
1. 初始化数据：
   ```bash
   curl -X POST http://localhost:8765/api/memory/import \
     -H "Content-Type: application/json" \
     -d "{\"text\": \"apple|苹果\ncat|猫\ndog|狗\nbird|鸟\nfish|鱼\", \"deck\": \"vocabulary\"}"
   ```

2. 打开浏览器：`http://localhost:8765`
3. 点击侧边栏 **"记忆卡复习"**
4. 看到 5 张卡片
5. 点击卡片翻转查看答案
6. 选择评分：Again / Hard / Good / Easy
7. 完成所有卡片复习

**验证**：
- ✅ 卡片翻转动画流畅
- ✅ 评分按钮正常工作
- ✅ 进度条实时更新
- ✅ 完成屏幕显示

---

### ✍️ Writing Agent（AI 批改）

**步骤**：
1. 点击侧边栏 **"写作"**
2. 选择考试类型：CET-6
3. 点击 **"填充示例作文"**
4. 点击 **"AI 批改"**
5. 等待批改完成（约 10-30 秒）
6. 查看批改结果：
   - 综合评分
   - 结构分析
   - 语法问题
   - 词汇建议
   - 优化版本

**验证**：
- ✅ 示例作文正确填充
- ✅ 字数统计实时更新
- ✅ 批改进度动画显示
- ✅ 结果详细完整

**注意**：需要配置 AI Provider（OpenAI/Claude 等）

---

### 📊 学习热力图（GitHub 风格）

**步骤**：
1. 记录学习活动：
   ```bash
   # 记录复习卡片
   curl -X POST http://localhost:8765/api/study/record \
     -H "Content-Type: application/json" \
     -d "{\"activity_type\": \"cards\", \"duration\": 30, \"count\": 10}"

   # 记录作文批改
   curl -X POST http://localhost:8765/api/study/record \
     -H "Content-Type: application/json" \
     -d "{\"activity_type\": \"essay\", \"duration\": 20, \"count\": 1}"
   ```

2. 返回首页（刷新页面）
3. 查看热力图：
   - 今日格子变成绿色
   - 悬停查看详情
   - 点击查看每日详情

**验证**：
- ✅ 热力图正确显示
- ✅ 今日数据更新
- ✅ 悬停提示工作
- ✅ 统计数据正确

---

### 📚 词汇库系统

**步骤**：
1. 初始化词汇数据：
   ```bash
   curl -X POST http://localhost:8765/api/vocabulary/initialize
   ```

2. 获取高频词：
   ```bash
   curl http://localhost:8765/api/vocabulary/high-frequency?exam_type=cet6
   ```

3. 获取易混词：
   ```bash
   curl http://localhost:8765/api/vocabulary/confusing
   ```

4. 查询搭配：
   ```bash
   curl "http://localhost:8765/api/vocabulary/collocations?word=make"
   ```

**验证**：
- ✅ 返回 JSON 格式正确
- ✅ 数据结构完整
- ✅ 中文显示正常

---

## 🎯 核心 API 端点

### 记忆卡（8 个）
- `GET /api/memory/due` - 获取到期卡片
- `POST /api/memory/review` - 复习卡片
- `POST /api/memory/cards` - 创建卡片
- `GET /api/memory/cards` - 列出卡片
- `GET /api/memory/statistics` - 学习统计
- `DELETE /api/memory/cards/{id}` - 删除卡片
- `POST /api/memory/import` - 批量导入

### Writing Agent（1 个）
- `POST /api/agent/writing` - 作文批改

### 学习记录（4 个）
- `GET /api/study/heatmap` - 热力图数据
- `GET /api/study/statistics` - 学习统计
- `POST /api/study/record` - 记录活动
- `GET /api/study/today` - 今日记录

### 词汇库（6 个）
- `GET /api/vocabulary/high-frequency` - 高频词
- `GET /api/vocabulary/core` - 核心词
- `GET /api/vocabulary/collocations` - 搭配
- `GET /api/vocabulary/confusing` - 易混词
- `GET /api/vocabulary/context` - 语境
- `POST /api/vocabulary/initialize` - 初始化

### AI Provider（7 个）
- `GET /api/providers` - 列出供应商
- `POST /api/providers` - 添加供应商
- `PUT /api/providers/{id}` - 更新供应商
- `DELETE /api/providers/{id}` - 删除供应商
- `POST /api/providers/{id}/test` - 测试供应商

---

## 🔧 配置 AI Provider

### 方法 1：通过 API

```bash
curl -X POST http://localhost:8765/api/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI GPT-4",
    "provider_type": "openai",
    "api_key": "sk-your-key-here",
    "model": "gpt-4",
    "base_url": "https://api.openai.com/v1"
  }'
```

### 方法 2：通过环境变量

```bash
# .env 文件
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## 📁 数据文件位置

所有数据保存在 `skills/examlex/data/` 目录：

```
data/
├── memory_cards.json         # 记忆卡数据
├── study_records.json        # 学习记录
├── vocabulary/               # 词汇库
│   ├── cet6_high_frequency.json
│   ├── cet6_core.json
│   ├── collocations.json
│   └── confusing_words.json
└── providers.json            # AI 供应商配置
```

---

## 🎉 完成度

- ✅ **记忆卡系统**：100%（Anki SM-2 算法）
- ✅ **Writing Agent**：100%（LangGraph 多 Agent）
- ✅ **学习热力图**：100%（GitHub 风格）
- ✅ **词汇库系统**：100%（高频词、搭配、易混词）

**总完成度**：57% (4/7 核心功能)

---

## 🐛 常见问题

### Q1: 启动失败
**A**: 检查端口 8765 是否被占用
```bash
netstat -ano | findstr 8765
```

### Q2: AI 批改失败
**A**: 检查 AI Provider 配置
```bash
curl http://localhost:8765/api/providers
```

### Q3: 热力图不显示
**A**: 检查浏览器控制台，确保 JS 文件加载

### Q4: 数据丢失
**A**: 检查 `skills/examlex/data/` 目录权限

---

## 📞 参考资料

- 项目地址：https://github.com/SFEW888/ExamLex
- 多智能体框架参考：
  - OpenHarness: https://github.com/HKUDS/OpenHarness
  - Pi Agent: https://github.com/earendil-works/pi
- 记忆框架参考：
  - MemOS: https://github.com/MemTensor/MemOS
  - mem0: https://github.com/mem0ai/mem0

---

**现在可以立即启动测试！🚀**

所有功能都是真实可用的，不是框架！
