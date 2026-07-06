# CLI 命令参考

> 所有命令均可通过 `tutor`（bash）或 `tutor.ps1`（PowerShell）封装脚本调用，也可直通底层 `python -m skills.english_exam_ai_tutor`。

---

## 触发方式说明

| 图标 | 含义 |
|:----:|------|
| 🤖 | **Agent 主导** — 通常由 Agent 在对话中自动调用，用户无需手动输入 |
| 👤 | **用户可用** — 适合用户直接在终端运行，调试或独立使用 |
| 🔧 | **维护者** — 开发/测试/仓库维护专用 |

---

## 命令总览

### 📋 备考闭环（按工作流顺序）

| 快捷命令 | 底层命令 | 触发 | 说明 |
|----------|----------|:--:|------|
| `tutor check <file>` | `validate-profile` | 👤 | 校验学习者档案合法性 |
| `tutor plan <file> [opts]` | `daily-plan` | 👤 | 约束求解生成每日计划 |
| `tutor log <file> [opts]` | `record-practice` | 🤖 | 追加练习记录到台账 |
| `tutor tag <text> [opts]` | `tag-error` | 🤖 | 从错误描述推断确定性标签 |
| `tutor errors <file> [opts]` | `summarize-errors` | 👤 | 汇总台账中的错误统计 |
| `tutor update <a> <l>` | `update-ability` | 🤖 | 从练习证据更新能力画像 |
| `tutor trends <file> [opts]` | `analyze-trends` | 👤 | 练习与能力趋势分析 |
| `tutor write <id> [opts]` | `writing-version` | 🤖 | 追加作文版本草稿 |
| `tutor score <essay> [opts]` | `score-writing` | 👤 | 确定性评分估算（非官方） |

### 📥 知识管理

| 快捷命令 | 底层命令 | 触发 | 说明 |
|----------|----------|:--:|------|
| `tutor extract --input <url\|file\|name> [opts]` | `extract` | 🤖 | 从 URL/文件/人名提取原始素材（多源学习的第 1 阶段） |
| `tutor ingest <file> [opts]` | `ingest-strategy` | 👤 | 从文件提取策略写入策略库 |
| `tutor strategies [opts]` | `list-strategies` | 👤 | 列出/搜索已摄入的策略 |
| `tutor validate --artifacts-dir <path>` | `validate-strategies` | 🤖 | 验证蒸馏策略格式并计算 Darwin 6 维结构评分（第 3 阶段） |
| `tutor commit --artifacts-dir <path> --library <path>` | `commit-strategies` | 🤖 | 通过 ratchet 检查将策略原子写入策略库（第 5 阶段） |

### 💾 数据管理

| 快捷命令 | 底层命令 | 触发 | 说明 |
|----------|----------|:--:|------|
| `tutor backup <dir> [opts]` | `backup` | 👤 | 打包备份全部学习数据 |
| `tutor restore <file> <dir>` | `restore` | 👤 | 从备份恢复学习数据 |
| `tutor report [opts]` | `visualize` | 👤 | 生成进度可视化 HTML 报告 |

### 📊 词汇

| 快捷命令 | 底层命令 | 触发 | 说明 |
|----------|----------|:--:|------|
| `tutor vocab [opts]` | `vocab-estimate` | 👤 | 抽样估算词汇量 |

### 🔧 维护者

| 底层命令 | 触发 | 说明 |
|----------|:--:|------|
| `check-deps` | 🔧 | 检查外部工具依赖（ffmpeg、yt-dlp 等） |
| `ops-check` | 🔧 | 运行 13 项运维就绪检查 |
| `validate-strategy` | 🔧 | 校验策略库文件 |
| `validate_repo.py` | 🔧 | 仓库完整性校验（非 CLI 命令） |

---

## 各命令详细签名

### `tutor check` — 校验档案

```bash
tutor check <profile>

# 示例
tutor check learner-profile.json
```

### `tutor plan` — 生成每日计划

```bash
tutor plan <profile>
  --ability <path>            # 能力画像（必填）
  --output <path>             # 输出路径（必填）
  [--errors <path>]           # 错误汇总（可选，有则用于优化计划）
  [--strategies <path>]       # 策略库（可选，有则附加方法论建议）

# 示例
tutor plan learner-profile.json \
  --ability ability-profile.json \
  --errors error-summary.json \
  --output daily-plan.json
```

### `tutor log` — 记录练习

```bash
tutor log <ledger>
  --date <YYYY-MM-DD>
  --exam-type <CET4|CET6|POSTGRADUATE_ENGLISH>
  --module <vocabulary|listening|reading|translation|writing>
  --task-id <id>
  --duration-minutes <minutes>
  --total-items <n>
  --correct-items <n>
  [--timed]                        # 计时训练模式
  [--time-limit-minutes <minutes>] # 考试规定时间
  [--overtime-items <n>]
  [--overtime-correct <n>]
  [--error-tags <tag1,tag2>]

# 示例
tutor log practice-ledger.json \
  --date 2026-07-05 \
  --exam-type CET4 \
  --module reading \
  --task-id timed-reading-001 \
  --duration-minutes 40 --total-items 20 --correct-items 14 \
  --timed --time-limit-minutes 35 \
  --error-tags READING_SPEED_LOW,READING_INFERENCE_FAIL
```

### `tutor tag` — 错误归因

```bash
tutor tag <text> [--module <module>] [--output <path>]

# 示例
tutor tag "I went to store." --module writing
# → ["WRITING_ARTICLE_OMISSION"]
```

### `tutor errors` — 错误汇总

```bash
tutor errors <ledger> [--output <path>]

# 示例
tutor errors practice-ledger.json --days 30 --output errors.json
```

### `tutor update` — 更新能力画像

```bash
tutor update <ability-profile> <ledger>

# 示例
tutor update ability-profile.json practice-ledger.json
```

### `tutor trends` — 趋势分析

```bash
tutor trends <ledger>
  [--history <ability-history>]
  [--output <path>]

# 示例
tutor trends practice-ledger.json --history ability-history.json --days 90
```

### `tutor write` — 作文版本

```bash
tutor write <writing-id>
  --file <writing-versions.json>
  --version <V1|V2|V3|...>
  --text <essay-text>
  [--source-version <parent-version>]
  [--changes <note1,note2>]

# 示例
tutor write essay-001 \
  --file writing-versions.json \
  --version V2 \
  --text "Improved version..." \
  --source-version V1 \
  --changes "修正了语法错误,增加了过渡句"
```

### `tutor score` — 作文评分

```bash
tutor score
  --text-file <path> | --text <string>
  --exam-type <CET4|CET6|POSTGRADUATE_ENGLISH|TEM4|TEM8>
  [--output <path>]

# 示例
tutor score --text-file my-essay.txt --exam-type CET4
```

### `tutor ingest` — 摄入策略

```bash
tutor ingest <file>
  --library <strategy-library.json>
  [--exam-types <CET4,CET6,...>]
  [--modules <module1,module2,...>]
  [--json]

# 示例
tutor ingest "四级阅读技巧.md" --library strategy-library.json
```

### `tutor strategies` — 策略库

```bash
tutor strategies --library <path> [--search <keyword>] [--json]

# 示例
tutor strategies --search 阅读
tutor strategies --library strategy-library.json
```

### `tutor backup` — 数据备份

```bash
tutor backup <data-dir> [--output <path>] [--exclude <pattern>] [--json]

# 示例
tutor backup ./local/data --output backup-2026-07-05.tar.gz
tutor backup ./local/data --list backup-2026-07-05.tar.gz
```

### `tutor restore` — 数据恢复

```bash
tutor restore <backup-file> --data-dir <dir> [--force] [--dry-run] [--json]

# 示例
tutor restore backup-2026-07-05.tar.gz --data-dir ./local/data
tutor restore backup-2026-07-05.tar.gz --data-dir ./local/data --dry-run
```

### `tutor report` — 进度报告

```bash
tutor report
  --ability-history <path>
  --ledger <path>
  [--error-summary <path>]
  [--output <path>]
  [--days <n>]
  [--title <text>]

# 示例
tutor report \
  --ability-history ability-history.json \
  --ledger practice-ledger.json \
  --days 30 \
  --output progress-report.html
```

### `tutor vocab` — 词汇量估算

```bash
tutor vocab --interactive [--output <path>]
tutor vocab --wordlist <answers.json> [--output <path>]

# 示例
tutor vocab --interactive --output vocab-result.json
```

### `tutor extract` — 提取原始素材

```bash
tutor extract --input <url|file|name>
  [--type auto|video|book|text|person]   # 强制指定输入类型（默认自动检测）
  [--output-dir <dir>]                   # 覆盖会话输出目录
  [--json]                               # JSON 格式输出

# 示例
tutor extract --input 四级阅读技巧.md --type text
tutor extract --input https://www.bilibili.com/video/BVxxx --type video
```

### `tutor validate` — 验证蒸馏策略

```bash
tutor validate --artifacts-dir <path>
  [--json]                               # JSON 格式输出

# 示例
tutor validate --artifacts-dir ./sessions/session-001
```

底层命令：`validate-strategies`。执行格式校验和 Darwin 6 维结构评分（满分 59 分），结果写入 `validation_report.json`。

### `tutor commit` — 提交策略到库

```bash
tutor commit --artifacts-dir <path>
  --library <strategy-library.json>
  [--json]                               # JSON 格式输出

# 示例
tutor commit --artifacts-dir ./sessions/session-001 --library strategy-library.json
```

底层命令：`commit-strategies`。执行 ratchet 检查（新策略 Darwin 分需超过已有记录），原子写入策略库。

### `tutor check-deps` — 检查依赖

```bash
tutor check-deps

# 示例
tutor check-deps
```

底层命令：`check-deps`。检查 ffmpeg、yt-dlp 等外部工具是否可用，用于视频/音频提取前的环境验证。

### `tutor ops-check` — 运维检查

```bash
tutor ops-check
  [--library <strategy-library.json>]    # 可选，用于业务结果检查
  [--json]                               # JSON 格式输出

# 示例
tutor ops-check
tutor ops-check --library strategy-library.json --json
```

底层命令：`ops-check`。运行 13 项运维就绪检查（环境、配置、数据完整性等），返回通过/警告/失败报告。

---

## 与传统 CLI 命令对照

如果你习惯直接用底层命令，两种方式等价：

```bash
# 快捷方式
tutor plan profile.json --ability ability.json

# 等价底层命令
python -m skills.english_exam_ai_tutor daily-plan --profile profile.json --ability ability.json

# 等价 pip 安装后命令
english-exam-tutor daily-plan --profile profile.json --ability ability.json
```
