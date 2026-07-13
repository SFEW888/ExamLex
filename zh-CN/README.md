# ExamLex

[![CI](https://github.com/SFEW888/ExamLex/actions/workflows/ci.yml/badge.svg)](https://github.com/SFEW888/ExamLex/actions/workflows/ci.yml)
[![CodeQL](https://github.com/SFEW888/ExamLex/actions/workflows/codeql.yml/badge.svg)](https://github.com/SFEW888/ExamLex/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10--3.13-blue.svg)](https://www.python.org/)
[![Skills](https://img.shields.io/badge/Skills-9-brightgreen.svg)](#八个助教角色)
[![Platforms](https://img.shields.io/badge/Platforms-4-blue.svg)](#平台集成)

**语言：** [English](../README.md)

> **项目状态：** ExamLex 已在 [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex) 以 MIT 许可证开源。

> **四级 / 六级 / 专四 / 专八 / 考研英语备考一站式 AI Agent Skill 与自动化工具包——支持上传策略文件持续学习进化**
> *CET-4 · CET-6 · TEM-4 · TEM-8 · Postgraduate English — Public-Safe Agent Skills + Deterministic Automation + Continuous Learning*

**一句话**：把"英语备考不知道从哪开始"的痛点，变成「词汇估算 → 摄入知识 → 诊断 → 计划（含词汇池+间隔复习） → 计时练习 → 归因 → 更新 → 进度可视化 → 迭代」的确定性学习闭环——你喂给它的每一份策略和方法，都会被吸收并在下一次备考中使用。

---

## 适合谁用

- 🎓 **大学生**：备考四级（CET-4）、六级（CET-6），需要系统化复习计划而非零散刷题
- 📖 **考研党**：准备考研英语，需要基于证据的每日任务分配和薄弱点追踪
- 👨‍🏫 **自学辅导者**：希望用 AI 辅助规划自己或他人的英语学习路径
- 🔧 **Agent Skill 开发者**：想了解 public-safe Skill 设计模式——角色边界 + 占位符 + 确定性脚本的架构思路
- 📥 **想沉淀个人备考方法论的用户**：手头有各种考试策略、做题技巧、作文模板文件，希望 AI 吸收后自动应用，而不是每次重新口述
- 🤖 **AI 编程助手用户**：Claude Code / Codex / Cursor 用户，想一键安装开箱即用的英语备考 Skill

---

## 快速开始

> **两种使用方式，不要混淆：**
> - **作为 Agent Skill**（在对话中用 `/examlex` 调用）→ 从当前本地目录运行安装脚本。这是完整助教体验。
> - **独立 CLI**（仅命令行工具）→ 安装当前本地目录后使用 `examlex` 命令。不注册 Agent Skill，只安装脚本引擎。

### 环境要求

- **Python 3.10 / Python 3.11 / Python 3.12 / Python 3.13**
- **Git**
- 以下任一 AI 编程助手：**Claude Code** / **Codex CLI** / **Codex App** / **Cursor**

### 按功能安装的依赖

核心助教功能和纯文本摄入不需要第三方 Python 包。只有使用对应的书籍或视频功能时，才需要下列工具。

| 功能 | 工具 | Windows 安装 | macOS/Linux 安装 |
|------|------|--------------|------------------|
| `text` / `person` | 无 | — | — |
| `book`（PDF） | [pdftotext（Poppler）](https://poppler.freedesktop.org/) | `winget install poppler` | `brew install poppler` / `apt install poppler-utils` |
| `book`（DOCX） | python-docx | `pip install python-docx` | `pip3 install python-docx` |
| `book`（EPUB DRM） | [Calibre / ebook-convert](https://calibre-ebook.com/download) | `winget install calibre` | `brew install calibre` |
| `video`（下载/元数据） | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | `pip install yt-dlp` | `pip3 install yt-dlp` |
| `video`（合并/转换/抽取音频） | [FFmpeg](https://ffmpeg.org/download.html) | `winget install ffmpeg` | `brew install ffmpeg` / `apt install ffmpeg` |
| `video`（语音识别） | 本地 [Whisper](https://github.com/openai/whisper)，或显式选择 SiliconFlow 并配置 `SILICONFLOW_API_KEY` | `pip install openai-whisper` | `pip3 install openai-whisper` |

`ffmpeg` 就是视频链路需要的开源媒体转换器：`yt-dlp` 下载到分离的视频流和音频流时可能需要它完成合并；ExamLex 在语音识别前也用它抽取并转换音频。只下载某些单文件视频时可能暂时用不到，但完整的“视频 → 音频 → 转写”流程必须安装 `ffmpeg`。

运行 `bin/examlex check-deps` 可检查本机工具是否齐全。

### 作为 Agent Skill 安装（推荐）

克隆公共仓库，然后在项目根目录运行对应 Agent 的安装脚本：

```powershell
git clone https://github.com/SFEW888/ExamLex.git
Set-Location ExamLex
```

```powershell
.\install.ps1 claude  # 也可替换为 codex 或 cursor
```

```bash
./install.sh claude   # 也可替换为 codex 或 cursor
```

安装脚本默认保留已有 Skill 目录。如需明确覆盖已有安装，请为 `install.sh` 添加 `--force`，或为 `install.ps1` 添加 `-Force`。

然后重启 Claude Code，在对话中调用：

```text
/examlex 帮我为 CET4 550+ 制定一周计划
/learning-planner 给基础偏弱、目标 CET4 550+ 的学习者制定 30 天计划
/grammar-corrector 批改这段作文并输出批改报告
```

```text
/examlex 帮我为 CET6 600+ 制定一周计划
/learning-planner 给基础偏弱、目标 CET4 550+ 的学习者制定 30 天计划
```

### 安装后验证

```text
# 重启 Agent 后
Claude Code:  /skills list → 应看到 examlex 和 8 个快捷 Skill
Codex CLI:    /skills → 应看到 /examlex 和 8 个快捷 Skill

# 快速测试
/examlex 你好，介绍一下你能帮我做什么
```

复制后的主 Skill 自带 CLI 入口。在已安装的 `examlex` Skill 目录中运行
`python run.py --help`，无需保留仓库检出，也无需另行安装 `examlex` Python 包。

### 安装目录速查

| 平台 | 全局路径 | 项目级路径 |
|------|----------|-----------|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex CLI / Codex App | `~/.agents/skills/` | `.agents/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

### 独立 CLI 安装（可选）

如果你只需要命令行工具（脱离 Agent 使用脚本）：

```bash
python -m pip install "git+https://github.com/SFEW888/ExamLex.git"
```

安装后可用：

```bash
# 简短命令
examlex plan learner-profile.json --ability ability-profile.json
examlex errors practice-ledger.json --days 30

# 或完整 Python 命令
examlex daily-plan --profile learner-profile.json --ability ability-profile.json
python -m examlex daily-plan --profile learner-profile.json --ability ability-profile.json
```

> Git 安装只安装 CLI 脚本引擎，不注册 Agent Skill。Agent 对话功能需要先克隆仓库并运行上方安装脚本。贡献者可在本地检出目录使用 `python -m pip install -e .`。
>
> 完整安装说明见 [快速开始指南](docs/getting-started.md)。

---

## 使用流程

```
                        ┌──────────────────────────────────────┐
                        │  0. 知识摄入（可选）                    │
                        │  用户上传策略/方法文件 → Agent 读取     │
                        │  → ingest_strategy.py → 存入策略库     │
                        └───────────────┬──────────────────────┘
                                        │ 后续所有步骤自动引用策略库
                                        ▼
学习者档案 (learner_id / exam_type / foundation_level / target_band / time_budget)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  1. 诊断          validate_profile.py                       │
│     校验档案合法性，拒绝不支持的考试类型、目标区间和缺失字段      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  2. 计划          generate_daily_plan.py                     │
│     约束求解：时间预算 × 能力状态 × 错误证据 → 模块分配        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  3. 练习          八大助教 + record_practice.py              │
│     词汇/听力/阅读/翻译/写作任务 → 记录 total_items/correct_items│
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  4. 归因          tag_error.py + summarize_errors.py         │
│     按标签/模块/维度统计重复错误，生成错误汇总                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  5. 更新          update_ability_profile.py + analyze_trends │
│     练习证据 → 能力画像更新 → 趋势分析（有足够数据点时）       │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │ 6a. 作文  │  │ 6b. 评分  │  │ 6c. 下一计划  │
   │ 版本管理  │  │ 规则估算  │  │ 回到步骤 2   │
   └──────────┘  └──────────┘  │ 优先处理重复  │
                               │ 高影响错误    │
                               └──────────────┘
```

---

## 核心功能

### 八个助教角色

内置八个专业助教，覆盖英语备考全场景。公开仓库发布角色边界、占位符和机器可读的 [助教角色契约](../skills/examlex/references/tutor-role-contracts.json)；私有提示词正文仅存于用户本地。

| 助教 | 快捷 Skill | 核心职责 | 职责边界 |
|------|:---------:|----------|----------|
| 🎯 **学习规划师** | `learning-planner` | 从档案、能力画像和错误统计生成基于证据的学习计划 | 不编造练习结果，不忽略脚本生成的约束 |
| 📝 **词汇拓展家** | `vocabulary-builder` | 词义辨识、拼写、听辨、搭配、短语运用和考试语境示例 | 不越权判断听力/阅读/翻译/写作分数 |
| 🔍 **阅读领航员** | `reading-navigator` | 阅读速度、信息定位、长难句拆解、推断和同义改写识别 | 不以主观判断替代已完成的练习记录 |
| 🏗️ **结构规划师** | `structure-planner` | 作文、段落、翻译和答题结构规划 | 不覆盖作文版本，不将结构指导包装为官方评分 |
| ✏️ **语法纠错官** | `grammar-corrector` | 诊断和纠正冠词、时态、主谓一致、从句、句型等语法问题 | 不在 public-safe 模式下包含私有提示词正文 |
| ✨ **润色魔法师** | `polish-wizard` | 在语义和结构稳定后提升清晰度、表达丰富度和考试得体性 | 不改变学习者原意，不掩盖实质性语法问题 |
| 🎭 **情景对话师** | `scenario-dialog` | 创建和引导考试相关情景对话，练习口语式反应和应用词汇 | 不伪造官方音频文本、分数或练习证据 |
| 🌏 **文化万事通** | `culture-guide` | 解释文化语境、背景知识、习语、典故和跨文化表达 | 不将文化注释包装为无依据的考试预测 |

### 快捷 Skill 速查

| 场景 | 快捷 Skill | 调用方式 |
|------|:---------:|---------|
| 完整助教工作流 | `examlex` | `/examlex` |
| 学习规划 | `learning-planner` | `/learning-planner` |
| 词汇拓展 | `vocabulary-builder` | `/vocabulary-builder` |
| 阅读拆解 | `reading-navigator` | `/reading-navigator` |
| 写作结构 | `structure-planner` | `/structure-planner` |
| 语法纠错 | `grammar-corrector` | `/grammar-corrector` |
| 表达润色 | `polish-wizard` | `/polish-wizard` |
| 情景对话 | `scenario-dialog` | `/scenario-dialog` |
| 文化解释 | `culture-guide` | `/culture-guide` |

> Claude Code、Codex CLI、Codex App、Cursor 均使用 `/` 前缀调用 Skill。

### 九大自动化脚本

确定性脚本覆盖学习闭环关键节点，所有输出可审计、可复现：

| 阶段 | 脚本 | 说明 |
|:----:|------|------|
| 🔬 **诊断** | `validate_profile.py` | 校验学习者档案：CET4/6/TEM4/8/考研、基础水平、目标区间 |
| 📚 **词汇** | `estimate_vocabulary.py` | Yes/No 抽样法估算词汇量，含虚报校正和置信区间 |
| 📋 **计划** | `generate_daily_plan.py` | 约束求解每日计划 + 词汇池分配 + 间隔复习任务加权 |
| 📊 **记录** | `record_practice.py` | 结构化记录练习数据，支持计时训练模式（超时统计） |
| 🏷️ **归因** | `tag_error.py` + `summarize_errors.py` | 按标签统计错误，输出间隔复习紧迫度和速度分析 |
| 📈 **更新** | `update_ability_profile.py` + `analyze_trends.py` | 从练习证据更新能力画像，积累足够数据后分析趋势 |
| ✍️ **作文** | `manage_writing_versions.py` + `score_writing_rubric.py` | 版本化管理作文草稿，支持范文库锚定评分 |
| 📊 **可视化** | `visualize.py` | 生成独立 HTML 进度报告（雷达图+趋势折线图+错误统计表） |
| 🔄 **迭代** | 回到计划阶段 | 将更新的能力画像和错误统计反馈至下一轮计划 |

### 知识摄入与持续学习

除学习闭环自动化外，项目还提供三个知识管理脚本，让 Skill 具备持续学习能力——用户上传考试策略、做题方法、作文模板等文件，Agent 自动提取结构化知识存入策略库，后续计划和建议自动引用：

| 脚本 | 说明 |
|:----:|------|
| 📥 **`ingest_strategy.py`** | Agent 读取用户上传的文件后，提取结构化策略（标题/适用考试/模块/方法步骤）并写入策略库 |
| 📋 **`list_strategies.py`** | 列出/搜索策略库：支持按关键词检索、按考试/模块分布统计、最新条目 |
| ✅ **`validate_strategy.py`** | 校验策略库字段、生命周期状态和引用完整性 |

**联动机制**：`generate_daily_plan.py` 新增可选 `--strategies` 参数——生成每日计划时自动检索策略库，为每个模块附上用户沉淀的对应方法论。详见下方「持续学习」章节。

高级蒸馏管线和运维检查命令：

```powershell
examlex extract --input <url|file|name> --type <auto|video|book|text|person>
examlex validate --artifacts-dir <path>
examlex commit --artifacts-dir <path> --library strategy-library.json
examlex ops-check
examlex ops-check --offline    # 不发起真实网络请求的确定性检查
```

---

## 适用场景

| 你的需求 | 推荐方式 | 说明 |
|----------|---------|------|
| 🎯 **制定备考计划** | `learning-planner` + `generate_daily_plan.py` | 输入基础/目标/时间预算，输出约束求解的每日任务 |
| 📖 **背单词记不住** | `vocabulary-builder` + `tag_error.py` | 按词义/拼写/听辨/语境四个维度精准定位薄弱点 |
| 📚 **阅读理解提分** | `reading-navigator` + `summarize_errors.py` | 长难句/定位/推断/同义改写分项诊断 |
| ✍️ **作文不知道怎么写** | `structure-planner` → `grammar-corrector` → `polish-wizard` + 作文脚本 | 结构规划→语法纠错→表达润色三阶段，版本化迭代 |
| 🔍 **语法错误反复犯** | `grammar-corrector` + `update_ability_profile.py` | 标签化归因 → 能力画像更新 → 下一轮计划优先修复 |
| 📊 **想知道进步了多少** | `analyze_trends.py` + `update_ability_profile.py` | 练习台账 → 能力趋势可视化分析 |
| 🗣️ **口语/听力薄弱** | `scenario-dialog` + `culture-guide` | 情景对话练习 + 文化语境理解 |
| 🔄 **需要完整学习闭环** | `examlex`（主 Skill） | 诊断→计划→练习→归因→更新→迭代，七步自动流转 |
| 📥 **沉淀个人备考方法论** | 拖入策略文件 → `ingest_strategy.py` → 后续备考自动引用 | 上传「四级阅读技巧.md」「考研作文模板.pdf」等，Skill 吸收后在计划和辅导中自动应用 |
| 📚 **整本备考书→策略库** | Agent 读取 PDF → structural 提取 → `ingest_strategy.py` | 300 页《四级真题解析》→ 三重验证 → 8 条方法论自动融入每日计划 |
| 🎬 **备考视频→策略库** | Agent RIA++ 蒸馏 → `ingest_strategy.py --source-type video` | B站字幕→并行提取→三重验证通过 5/15→自动引用 |
| 👤 **名师方法论→策略库** | Agent 认知提取 → `ingest_strategy.py --source-type person` | 分析赖世雄→4个心智模型+6条启发式→备考引用 |

### 使用示例

**场景一：作文不知道怎么写**

```text
你：/structure-planner 我要写一篇 CET4 关于环保的议论文，不知道怎么组织

Agent：好的，我来帮你规划结构。
      题目建议方向：The Importance of Environmental Protection
      推荐三段式结构：
      ┌─────────────────────────────────────────────┐
      │ 第一段（开头 3-4 句）                         │
      │ · 背景引入：环境问题日益严峻                     │
      │ · 观点陈述：保护环境人人有责                     │
      │ · 预告结构：将从个人和政府两个层面展开             │
      ├─────────────────────────────────────────────┤
      │ 第二段（主体 5-6 句）                         │
      │ · 个人层面：减少塑料使用、绿色出行、节约水电         │
      │ · 政府层面：立法监管、推广清洁能源、建立保护区         │
      ├─────────────────────────────────────────────┤
      │ 第三段（结尾 2-3 句）                         │
      │ · 总结观点：个人行动 + 政策支持 = 可持续未来        │
      │ · 呼吁行动：从现在做起，从身边小事做起              │
      └─────────────────────────────────────────────┘
      你可以先按这个框架写初稿，写完后再帮你润色。

你：（写完初稿后）/polish-wizard 帮我润色这段作文

Agent：[分析初稿]
      已润色，主要改动：
      · 第 2 句 "pollution is bad" → "environmental degradation poses an increasingly
        serious threat to public health and ecosystems"（提升表达丰富度）
      · 第 5 句 "we should..." → "it is imperative that individuals adopt..."
       （增加句式多样性）
      · 增加衔接词 "Furthermore"、"Consequently"，逻辑更流畅
      [展示润色后全文 + 改动对照]
```

**场景二：语法错误反复犯**

```text
你：/grammar-corrector 帮我检查这段作文的语法

Agent：已检查，发现 3 类共 5 处语法问题：
      ❌ 冠词遗漏 ×2："I went to store." → "I went to the store."
      ❌ 主谓一致 ×2："The students studies hard." → "The students study hard."
      ❌ 时态混乱 ×1：上句过去时，下句突然一般现在时

      [调用 tag_error.py 归因]
      → WRITING_ARTICLE_OMISSION（冠词遗漏）×2
      → WRITING_LANGUAGE_ACCURACY_FAIL（主谓一致）×2
      → WRITING_LANGUAGE_ACCURACY_FAIL（时态混乱）×1

      [写入练习台账 → summarize_errors.py 发现]
      过去 30 天冠词遗漏已出现 12 次，是你最高频的错误标签。

你：帮我制定明天的计划，重点修冠词

Agent：[调用 generate_daily_plan.py]
      明日计划（专项矫正版）：
      · 语法专项 25min：冠词规则速览 + 10 道冠词填空题（📥 运用常见错误库「汉语无冠词系统」策略）
      · 写作 20min：写一段 80 词短文，写完后自查每个单数可数名词是否有冠词
      · 阅读 25min：快速阅读 ×1 篇，关注文中冠词用法并标注
      └── 本次计划优先修复冠词遗漏（review_urgency: 0.85，30 天内 12 次）
```

---

## 支持对象

| 考试类型 | 标识 | 目标区间 |
|----------|------|----------|
| 大学英语四级 | `CET4` | `425~499`、`500~550`、`550+`、`600+` |
| 大学英语六级 | `CET6` | `425~499`、`500~550`、`550+`、`600+` |
| 考研英语 | `POSTGRADUATE_ENGLISH` | `50+`、`70~80`、`80+`、`90+` |
| 英语专业四级 | `TEM4` | `60~69`、`70~79`、`80+` |
| 英语专业八级 | `TEM8` | `60~69`、`70~79`、`80+` |

**基础水平分级与策略**：

| 水平 | 标识 | 策略重点 |
|------|------|----------|
| 🟢 基础偏弱 | `基础偏弱` | 高频词汇、语法修补、慢速阅读支持、引导式输出——短任务优先 |
| 🟡 中等基础 | `中等基础` | 常规任务 + 准确度提升、速度训练、考试策略——平衡新练习与纠错 |
| 🔴 基础较好 | `基础较好` | 高价值重复错误、写作/翻译质量、考试时间管理——精准打磨薄弱点 |

> ⚠️ 脚本帮助确保每日任务在学习者时间预算内切实可行，不代表官方考试成绩。

---

## 架构设计

### 架构概览

```
Agent 对话层 (Claude Code / Codex / Cursor)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Skill 层 (skills/examlex/)               │
│  助教角色 · 参考文档 · 模板 · Schema · 工作流定义        │
│  八个快捷 Skill (skills/*/)                              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  脚本层 (examlex/)                  │
│  validate · daily-plan · record · tag-error · summarize  │
│  update-ability · analyze-trends · writing-version       │
│  score-writing · CLI 统一入口                             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  数据层                                                  │
│  学习者档案 · 能力画像 · 练习台账 · 错误汇总 · 作文版本    │
│  📥 策略库 (strategy-library.json) ← 持续学习摄入        │
│  JSON/YAML 兼容格式 · 字段与脚本严格对应                  │
└─────────────────────────────────────────────────────────┘
```

### 项目结构

```
.
├── SKILL.md                         # 根级 Skill 入口
├── install.sh / install.ps1         # 跨平台克隆安装入口
│
├── skills/examlex/    # 可移植 public-safe Skill 包
│   ├── SKILL.md                     #   主 Skill 定义
│   ├── run.py                       #   复制安装后可直接使用的 CLI 入口
│   ├── assets/
│   │   ├── schemas/                 #   JSON Schema（档案/记录/作文版本）
│   │   └── templates/              #   模板（档案/画像/计划/记录/错误日志/作文版本）
│   ├── references/                  #   参考文档（助教名册/数据模型/错误分类/考试配置/工作流/提示词模式）
│   └── scripts/                     #   确定性脚本（校验/计划/记录/归因/更新/趋势/作文/评分）
│
├── skills/*/                        # 八个快捷 Agent Skill
│
├── examlex/    # 可导入 Python 镜像（测试与 CLI 使用）
│   ├── cli.py                       #   统一 CLI 入口
│   └── scripts/                     #   镜像脚本（与 Skill 脚本字段兼容）
│
├── integrations/                    # 平台适配说明
│   ├── claude-code/                 #   Claude Code 集成
│   ├── codex-cli/                   #   Codex CLI 集成
│   ├── codex-app/                   #   Codex App 集成
│   └── cursor/                      #   Cursor 集成
│
├── docs/                            # 英文文档
├── zh-CN/                           # 中文文档目录
│   ├── docs/                        #   中文版设计/配置/开发/排错/发布/项目质量
│   └── skill/references/            #   中文版参考文档
│
├── examples/                        # 示例文件（档案/画像/记录/作文版本）
├── tests/                           # 333+ 项单元测试
├── scripts/                         # 维护者验证器与底层安装器
├── .github/                         # Issue/PR 模板、CI/CD、Dependabot
└── pyproject.toml                   # 包元数据
```

### 设计原则

- **生成式双轨分离**：`skills/examlex/` 是唯一人工维护、可移植的 Agent Skill 源码；`examlex/` 是供测试、打包和 CLI 使用的自动生成 Python 镜像，CI 会拒绝缺失、被改动或多余的镜像文件。
- **确定性优先**：脚本刻意避免概率式规划或评分逻辑，所有自动化输出可审计、可复现。
- **公开安全**：GitHub 仓库仅发布角色边界、模板、Schema、脚本接口和占位符；原始八个助教提示词正文不进入公开仓库。

---

## 数据模型

项目使用 JSON 兼容格式组织学习者状态数据。YAML/Markdown 模板为编辑便利提供，字段名须与脚本兼容：

| 数据文件 | 用途 | 模板 |
|----------|------|------|
| **学习者档案** | 考试类型、基础水平、目标区间、每日时间预算 | `learner-profile.json` / `.yaml` |
| **能力画像** | 各模块能力节点级别、状态、准确率统计（5 模块 × 多节点） | `ability-profile.yaml` |
| **练习台账** | 日期、模块、任务、时长、总量、正确量、错误标签 | `exercise-record.json` / `.yaml` |
| **错误汇总** | 按标签/模块/维度的错误统计（20+ 标签，5 模块） | 由 `summarize_errors.py` 生成 |
| **作文版本** | 版本化草稿（V1/V2/V3…）、修改说明、版本链 | `writing-version-record.yaml` |
| **作文评分** | 确定性规则估算（注明非官方评分），含维度分项 | 由 `score_writing_rubric.py` 生成 |
| **策略库** | 用户上传的考试策略、做题方法、作文模板的结构化存储 | `strategy-library.json`，由 `ingest_strategy.py` 写入 |

---

## 持续学习（Knowledge Ingestion）

Skill 支持**多源持续学习**——不限于文本文件。书籍、长视频、播客、名师方法论、与学霸的对话……任何形式的备考知识都能蒸馏进策略库，下次备考自动用上。

### 多源蒸馏架构

```
                        持续学习 — 多源摄入
                              │
    ┌─────────────┬───────────┼───────────┬─────────────┐
    ▼             ▼           ▼           ▼             ▼
  📝 文本       📚 书籍     🎬 视频     👤 人物       💬 对话
  (策略笔记)    (PDF/EPUB)  (B站/YT)   (名师/学霸)   (聊天记录)
    │             │           │           │             │
    ▼             ▼           ▼           ▼             ▼
  direct        book        video       person        manual
  (直接摄入)                                        (手动整理)
  │               │           │           │             │
  └───────────────┴───────────┼───────────┴─────────────┘
                              │
                              ▼
                  ┌──────────────────┐
                  │ ingest_strategy  │
                  │  .py             │
                  │ --source-type    │
                  │ --distillation   │
                  │   -method        │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ strategy-library │
                  │   .json          │
                  │ (统一策略库)      │
                  └────────┬─────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐ ┌─────────┐ ┌──────────┐
         │ 每日计划  │ │ 助教辅导  │ │ 策略检索  │
         │ 自动引用  │ │ 调用策略  │ │ 搜索/列表  │
         └─────────┘ └─────────┘ └──────────┘
```

### 策略库结构

每条策略记录包含完整的来源追溯：

| 字段 | 说明 | 示例 |
|------|------|------|
| `strategy_id` | 唯一标识 | `cet4-reading-speed-001` |
| `title` | 策略名称 | 四级阅读快速定位法 |
| `source_type` | 来源类型 | `text` / `book` / `video` / `person` / `conversation` |
| `distillation_method` | 蒸馏方法 | `direct`（直接）/ `structural`（结构化提取）/ `ria`（RIA++）/ `cognitive`（认知提取）/ `manual`（手动） |
| `source_file` | 来源文件 | `四级阅读技巧.md` |
| `source_url` | 原始链接 | B站视频 URL / 书籍 ISBN / 人物主页 |
| `exam_types` | 适用考试 | `["CET4", "CET6"]` |
| `modules` | 关联模块 | `["reading"]` |
| `ability_nodes` | 关联能力节点 | `["阅读速度", "定位能力"]` |
| `content` | 核心方法描述 | 先读题干再回原文定位… |
| `steps` | 步骤拆解 | `["1. 快速扫读题干", "2. 按序定位", …]` |

### 使用示例

**场景一：从备考书籍提取方法论**

```text
你：我刚买了《四级阅读高分攻略》PDF，帮我提取里面的做题方法

Agent：[读取 PDF 全文 → 应用结构化提取]
      扫描到 12 个候选方法 → 三重验证通过 8 个（通过率 67%）：
      · 快速定位法（第3章+第5章独立提及，可预测新题型解答策略）
      · 长难句拆解法（第2章详述+第7章案例，非通用建议）
      · 选项排除法（第4章方法论+第6章真题应用）
      ...（5 个未通过：2 个仅有单一出处，3 个为通用建议）

      [ingest_strategy.py × 8 --source-type book --distillation-method structural]
      已全部写入策略库
```

**场景二：从备考视频蒸馏技巧**

```text
你：我下载了 B站「四级听力满分技巧」系列视频的字幕文件，帮我提取方法论

Agent：[读取字幕 → RIA++ 蒸馏]
      Phase 0: 识别出 4 个主要论题，核心术语 12 个
      Phase 1: 并行提取到 15 个候选方法
      Phase 1.5: 三重验证通过 5 个（通过率 33%）：
      · Section A 预读法（≥2 处独立引用 + 可预测新题型 + 非通用建议）
      · 连读弱读识别训练法
      · 数字日期快速记录法
      ...（10 个未通过：6 个单一出处，3 个常识，1 个无法预测）
      Phase 2: 5 个方法已完成 RIA++ 六段构造（含触发场景 + 边界）

      [ingest_strategy.py × 5 --source-type video --distillation-method ria]
      已全部写入策略库
```

**场景三：蒸馏名师方法论**

```text
你：帮我分析赖世雄的英语学习方法论，提取能用的策略

Agent：[认知提取]
      多角度采集：著作×3、访谈×5、教学视频×8、学生评价×12
      三重验证通过 4 个心智模型 + 6 条启发式：
      心智模型：
      · "慢就是快"——每个音标彻底搞懂再前进（≥3 处独立来源）
      · "语法内化于对话"——不背规则，在对话中自然习得
      启发式：
      · "模仿→录音→对比→修正"四步发音训练法
      · "每天只听 10 分钟，但连续 30 天不间断"
      ...

      [ingest_strategy.py --source-type person --distillation-method cognitive]
      已写入策略库（4 个心智模型 + 6 条启发式）
```

**场景四：沉淀与学霸的对话**

```text
你：昨天和六级 600+ 的学长聊了半小时，他分享了几个很有用的方法

Agent：请告诉我具体内容

你：[描述…阅读先做 Section C、听力趁 Direction 预读选项、背 5 个万能开头句…]

Agent：[提取 3 条策略 → ingest_strategy.py --source-type conversation]
      已写入策略库
```

### 与现有工作流的融合

- **有策略文件时**：选择对应的蒸馏工具→摄入策略库→后续计划/辅导自动引用
- **没有策略文件时**：Skill 照常工作，策略库为空不报错
- **随时可补充**：任何阶段都可以摄入新知识，立即生效
- **全局共享**：一份策略库服务于所有学习者档案，喂一次所有人受益
- **来源可追溯**：每条策略记录 `source_type` + `distillation_method` + `source_url`

> 详细的多源蒸馏工作流和字段规范见 [多源蒸馏参考](skill/references/multi-source-distillation.md)。

---

## 错误标签体系

脚本内置三级错误分类，覆盖五大模块、20+ 标签：

| 模块 | 标签示例 | 覆盖维度 |
|------|---------|----------|
| 📖 词汇 | `VOCAB_MEANING_RECOGNITION_FAIL` · `VOCAB_SPELLING_FAIL` · `VOCAB_CONTEXT_MISUSE` | 词义辨识 / 拼写 / 听辨 / 语境运用 |
| 🎧 听力 | `LISTENING_KEYWORD_MISS` · `LISTENING_LINKING_WEAK_FORM_FAIL` · `LISTENING_MAIN_IDEA_FAIL` | 关键词捕捉 / 连读弱读 / 数字日期 / 主旨推断 |
| 📚 阅读 | `READING_LONG_SENTENCE_FAIL` · `READING_INFERENCE_FAIL` · `READING_PARAPHRASE_FAIL` | 长难句 / 信息定位 / 推断 / 同义改写 |
| 🌐 翻译 | `TRANSLATION_GRAMMAR_FAIL` · `TRANSLATION_WORD_CHOICE_FAIL` · `TRANSLATION_CHINESE_ENGLISH` | 语法准确度 / 选词 / 中英转换 / 句式变化 |
| ✍️ 写作 | `WRITING_STRUCTURE_LOGIC_WEAK` · `WRITING_LANGUAGE_ACCURACY_FAIL` · `WRITING_EXPRESSION_LIMITED` | 任务完成度 / 结构逻辑 / 语言准确度 / 表达丰富度 |

> 详见 [错误分类参考](skill/references/error-taxonomy.md)。

---

## 平台集成

| 平台 | 调用方式 | 快捷 Skill 前缀 | 适配说明 |
|------|----------|:------------:|----------|
| **Claude Code** | `/examlex` | `/` | [集成说明](integrations/claude-code.md) |
| **Codex CLI** | `/examlex` | `/` | [集成说明](integrations/codex-cli.md) |
| **Codex App** | `/examlex` | `/` | [集成说明](integrations/codex-app.md) |
| **Cursor** | 通过 Skill 目录配置 | — | [集成说明](integrations/cursor.md) |

内部 CLI 仅用于开发调试与测试，不作为普通用户入口：

```powershell
python -m examlex --help
```

### CLI 快捷封装

项目提供了 `examlex` 封装脚本，用简短命令替代长串 Python 调用，适合脱离 Agent 时在终端直接使用：

```bash
# bash
examlex plan learner-profile.json --ability ability-profile.json
examlex errors practice-ledger.json --days 30
examlex backup ./local/data

# PowerShell
.\examlex.ps1 plan learner-profile.json --ability ability-profile.json
.\examlex.ps1 errors practice-ledger.json --days 30
.\examlex.ps1 backup .\local\data
```

| 类别 | 快捷命令 | Agent 对话等价 |
|------|---------|---------------|
| 校验档案 | `examlex check <file>` | 「帮我检查这份档案」 |
| 生成计划 | `examlex plan <file> --ability ...` | 「帮我制定今天的计划」 |
| 错误汇总 | `examlex errors <file>` | 「最近哪些错误最频繁」 |
| 趋势分析 | `examlex trends <file>` | 「我最近进步了吗」 |
| 作文评分 | `examlex score <essay>` | 「这篇作文能打多少分」 |
| 摄入策略 | `examlex ingest <file>` | 「记住这份技巧文件」 |
| 数据备份 | `examlex backup <dir>` | 「备份我的学习数据」 |
| 进度报告 | `examlex report --ability-history ...` | 「生成一份学习报告」 |

> 完整命令签名见 [CLI 参考文档](cli-reference.md)。封装脚本位于 `bin/examlex`（bash）和 `bin/examlex.ps1`（PowerShell）。

---

## 环境变量参考

无需密钥即可使用。ExamLex 不会自动加载 `.env`；请在 Shell 中导出变量，或使用你自己的环境加载工具读取 `.env.example`：

| 变量 | 必填 | 默认值 | 说明 |
|------|:--:|--------|------|
| `SILICONFLOW_API_KEY` | 否 | — | SiliconFlow 云端语音识别密钥；仅显式设置 `asr_backend="siliconflow"` 时上传音频。 |
| `EXAMLEX_PYTHON` | 否 | `python` | 本地 ExamLex 封装脚本使用的 Python 解释器 |

> ⚠️ **安全提醒**：不要提交 `.env`、学习者身份信息、私有提示词正文、Token、密码或本地数据库凭据到公开仓库。

---

## 提示词模式

| 模式 | 适用场景 | 说明 |
|------|----------|------|
| 🔓 **public-safe**（默认） | GitHub、示例、文档、演示、Issue、PR、发布包 | 仅包含角色边界、占位符、模板、Schema 和脚本接口 |
| 🔒 **full-local** | 用户本机私有环境 | 可路由到仓库外的私有提示词资产 |

> **重要约束**：原始八个助教提示词正文不发布、不重写、不重构进任何公开文件。公开文档中的占位符（如 `[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]`）仅为接口标记。详见 [提示词策略](docs/prompt-policy.md)。

使用 full-local 模式时，在仓库外的一个目录中严格保存八个 `<role-id>.md` 文件，然后在不暴露正文的前提下校验：

```powershell
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts"
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --json
```

检查只输出文件大小与 SHA-256 哈希。运行时会在内存中组合选定的私有正文、公开角色契约和明确分隔的不可信学习者上下文。绝不能提交私有目录；严格文件名与边界详见 [提示词策略](docs/prompt-policy.md)。

---

## 常见问题

**"脚本的输出是官方考试成绩吗？"**

不是。所有脚本输出都是基于你提供的数据（练习记录、能力画像）的确定性计算或规则估算。`score_writing_rubric.py` 评分是规则估算，`analyze_trends.py` 趋势分析反映的是台账数据本身的变化趋势。项目不做、也不会做官方考试分数保证预测。

**"我必须手动运行 CLI 命令吗？"**

不需要。绝大多数情况下你在 Agent 对话中说自然语言即可——Agent 读取 SKILL.md 中的工作流说明后，自动按需调用脚本。CLI 和 `examlex` 封装命令主要用于调试、脚本集成和脱离 Agent 的独立使用场景。

**"策略库里的数据会被上传到云端吗？"**

不会。策略库是本地 JSON 文件，和你的学习者档案、练习台账存放在同一个本地数据目录。提取和分析都在本机完成。如果你的 Agent 模型运行在云端，你输入给模型的文本遵循该服务商的常规数据条款——和任何其他对话内容一样。

**"我可以把策略库分享给别人吗？"**

你自己的考试策略和方法——可以。从受版权保护的书籍中提取的策略——不要公开发布。这和手写读书笔记的规则一样：笔记是你的，但不要出版他人的书的内容。详见下方许可证说明。

**"我能同时备考四级和六级吗？"**

可以。为每个考试类型创建独立的学习者档案，策略库是全局共享的。切换档案即可切换备考上下文。

**"为什么不支持雅思/托福？"**

当前优先覆盖国内高频英语考试（四级/六级/考研/专四/专八）。雅思/托福的评分体系完全不同（band score 1-9），需要独立设计，属于后续扩展。

---

## 维护者验证

```powershell
# 仓库完整性校验
python scripts\validate_repo.py --root . --json

# 单元测试
python -m unittest discover -s tests

# Git 格式检查
git diff --check
```

提交前安全检查：

```powershell
# 确认公开文件中无私有提示词正文
# 确认可移植 Skill 目录中无根级安装说明
Get-ChildItem -Name skills\examlex | Where-Object { $_ -in @('README.md','INSTALL.md') }
```

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [设计说明](docs/design.md) | 双轨分离、公开安全发布、确定性自动化的设计理念 |
| [架构说明](docs/architecture.md) | 项目分层与模块关系 |
| [使用流程](docs/usage.md) | 完整学习闭环操作指南 |
| [提示词策略](docs/prompt-policy.md) | public-safe 与 full-local 模式规则 |
| [快速开始](docs/getting-started.md) | 各平台安装与首次使用 |
| [配置](docs/configuration.md) | 可选本地配置与环境变量 |
| [开发](docs/development.md) | 开发环境搭建与贡献流程 |
| [排错](docs/troubleshooting.md) | 常见问题与解决方法 |
| [发布](docs/release.md) | 版本发布流程 |
| [项目质量](docs/project-quality.md) | 项目质量与发布检查 |
| [四级指南](docs/cet4.md) | CET-4 备考专项说明 |
| [六级指南](docs/cet6.md) | CET-6 备考专项说明 |
| [考研英语指南](docs/postgraduate.md) | 考研英语备考专项说明 |
| [CLI 参考](cli-reference.md) | 全部命令行签名、触发方式分类、封装脚本说明 |
| [优化计划](docs/optimization-plan.md) | 已完成优化与后续优先级 |
| [环境诊断](../scripts/check_env.ps1) | 检查 Python/Git/Skills/磁盘空间 |
| [数据诊断](../scripts/check_data.ps1) | 检查学习者数据完整性与大小 |
| [数据维护](../scripts/maintenance.ps1) | 清理旧备份、验证 JSON 完整性 |

中文版文档位于 `zh-CN/` 目录下。

---

## 关键词索引

**中文**：英语考试 · 四级 · 六级 · 考研英语 · CET-4 · CET-6 · 英语备考 · 英语学习 · AI 助教 · 英语辅导 · 学习规划 · 词汇 · 语法纠错 · 阅读训练 · 作文批改 · 能力画像 · 错误归因 · 每日计划 · 持续学习 · 多源蒸馏 · 知识摄入 · 策略库 · 方法沉淀 · 结构化提取 · RIA++蒸馏 · 认知提取 · Agent Skill · Skills 市场 · 公开安全

**English**：English exam · CET-4 · CET-6 · postgraduate English · AI tutor · English learning · exam preparation · learning planner · vocabulary builder · grammar corrector · reading navigator · writing polish · error taxonomy · ability profile · daily plan · continuous learning · multi-source distillation · knowledge ingestion · strategy library · structural extraction · RIA++ · cognitive extraction · Agent Skill · public-safe · Claude Code · Codex · Cursor

**适配工具**：Claude Code · Codex CLI · Codex App · Cursor · Anthropic Claude · AI Coding Agent · LLM Agent · Skills Marketplace

---

## 社区

- [贡献指南（英文）](../CONTRIBUTING.md)
- [安全策略（英文）](../SECURITY.md)
- [行为准则（英文）](../CODE_OF_CONDUCT.md)
- [支持（英文）](../SUPPORT.md)
- [更新日志（英文）](../CHANGELOG.md)

---

## 贡献

贡献应保持项目公开安全、确定性可验证。请从英文版 [CONTRIBUTING.md](../CONTRIBUTING.md) 开始。

---

## 许可证

MIT。详见 [LICENSE](../LICENSE)。
