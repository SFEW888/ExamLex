# CLI 命令参考

> 所有命令均可通过 `examlex`（bash）或 `examlex.ps1`（PowerShell）封装脚本调用，也可直通底层 `python -m examlex`；复制安装主 Skill 后，还可在其目录中使用 `python run.py`。

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
| `examlex check <file>` | `validate-profile` | 👤 | 校验学习者档案合法性 |
| `examlex plan <file> [opts]` | `daily-plan` | 👤 | 约束求解生成每日计划 |
| `examlex log <file> [opts]` | `record-practice` | 🤖 | 追加练习记录到台账 |
| `examlex tag <text> [opts]` | `tag-error` | 🤖 | 从错误描述推断确定性标签 |
| `examlex errors <file> [opts]` | `summarize-errors` | 👤 | 汇总台账中的错误统计 |
| `examlex update <a> <l>` | `update-ability` | 🤖 | 从练习证据更新能力画像 |
| `examlex trends <file> [opts]` | `analyze-trends` | 👤 | 练习与能力趋势分析 |
| `examlex write <id> [opts]` | `writing-version` | 🤖 | 追加作文版本草稿 |
| `examlex score <essay> [opts]` | `score-writing` | 👤 | 确定性评分估算（非官方） |

### 📥 知识管理

| 快捷命令 | 底层命令 | 触发 | 说明 |
|----------|----------|:--:|------|
| `examlex extract --input <url\|file\|name> [opts]` | `extract` | 🤖 | 从 URL/文件/人名提取原始素材（多源学习的第 1 阶段） |
| `examlex ingest <file> [opts]` | `ingest-strategy` | 👤 | 从文件提取策略写入策略库 |
| `examlex strategies [opts]` | `list-strategies` | 👤 | 列出/搜索已摄入的策略 |
| `examlex validate --artifacts-dir <path>` | `validate-strategies` | 🤖 | 验证蒸馏策略格式并计算 Darwin 6 维结构评分（第 3 阶段） |
| `examlex commit --artifacts-dir <path> --library <path>` | `commit-strategies` | 🤖 | 通过 ratchet 检查将策略原子写入策略库（第 5 阶段） |

### 💾 数据管理

| 快捷命令 | 底层命令 | 触发 | 说明 |
|----------|----------|:--:|------|
| `examlex backup <dir> [opts]` | `backup` | 👤 | 打包备份全部学习数据 |
| `examlex restore <file> <dir>` | `restore` | 👤 | 从备份恢复学习数据 |
| `examlex report [opts]` | `visualize` | 👤 | 生成进度可视化 HTML 报告 |

兼容拼写 `backup-data` 和 `restore-data` 分别路由到同一个 `backup`、`restore` 实现。

### 📊 词汇

| 快捷命令 | 底层命令 | 触发 | 说明 |
|----------|----------|:--:|------|
| `examlex vocab [opts]` | `vocab-estimate` | 👤 | 抽样估算词汇量 |

### 🔧 维护者

| 底层命令 | 触发 | 说明 |
|----------|:--:|------|
| `check-deps` | 🔧 | 检查外部工具依赖（ffmpeg、yt-dlp 等） |
| `ops-check` | 🔧 | 运行 13 项运维就绪检查 |
| `resume` | 👤 | 读取已有蒸馏会话并返回续跑指引 |
| `sessions-cleanup` | 🔧 | 预览或归档陈旧的非终态会话 |
| `validate-strategy` | 🔧 | 校验策略库文件 |
| `validate_repo.py` | 🔧 | 仓库完整性校验（非 CLI 命令） |

---

## 各命令详细签名

### `examlex check` — 校验档案

```bash
examlex check <profile>

# 示例
examlex check learner-profile.json
```

### `examlex plan` — 生成每日计划

```bash
examlex plan <profile>
  --ability <path>            # 能力画像（必填）
  --output <path>             # 输出路径（必填）
  [--errors <path>]           # 错误汇总（可选，有则用于优化计划）
  [--strategies <path>]       # 策略库（可选，有则附加方法论建议）

# 示例
examlex plan learner-profile.json \
  --ability ability-profile.json \
  --errors error-summary.json \
  --output daily-plan.json
```

### `examlex log` — 记录练习

```bash
examlex log <ledger>
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
examlex log practice-ledger.json \
  --date 2026-07-05 \
  --exam-type CET4 \
  --module reading \
  --task-id timed-reading-001 \
  --duration-minutes 40 --total-items 20 --correct-items 14 \
  --timed --time-limit-minutes 35 \
  --error-tags READING_SPEED_LOW,READING_INFERENCE_FAIL
```

### `examlex tag` — 错误归因

```bash
examlex tag <text> [--module <module>] [--output <path>]

# 示例
examlex tag "I went to store." --module writing
# → ["WRITING_ARTICLE_OMISSION"]
```

### `examlex errors` — 错误汇总

```bash
examlex errors <ledger> [--output <path>]

# 示例
examlex errors practice-ledger.json --days 30 --output errors.json
```

### `examlex update` — 更新能力画像

```bash
examlex update <ability-profile> <ledger>

# 示例
examlex update ability-profile.json practice-ledger.json
```

### `examlex trends` — 趋势分析

```bash
examlex trends <ledger>
  [--history <ability-history>]
  [--output <path>]

# 示例
examlex trends practice-ledger.json --history ability-history.json --days 90
```

### `examlex write` — 作文版本

```bash
examlex write <writing-id>
  --file <writing-versions.json>
  --version <V1|V2|V3|...>
  --text <essay-text>
  [--source-version <parent-version>]
  [--changes <note1,note2>]

# 示例
examlex write essay-001 \
  --file writing-versions.json \
  --version V2 \
  --text "Improved version..." \
  --source-version V1 \
  --changes "修正了语法错误,增加了过渡句"
```

### `examlex score` — 作文评分

```bash
examlex score
  --text-file <path> | --text <string>
  --exam-type <CET4|CET6|POSTGRADUATE_ENGLISH|TEM4|TEM8>
  [--output <path>]

# 示例
examlex score --text-file my-essay.txt --exam-type CET4
```

### `examlex ingest` — 摄入策略

```bash
examlex ingest <file>
  --library <strategy-library.json>
  [--exam-types <CET4,CET6,...>]
  [--modules <module1,module2,...>]
  [--json]

# 示例
examlex ingest "四级阅读技巧.md" --library strategy-library.json
```

### `examlex strategies` — 策略库

```bash
examlex strategies --library <path> [--search <keyword>] [--json]

# 示例
examlex strategies --search 阅读
examlex strategies --library strategy-library.json
```

### `examlex backup` — 数据备份

```bash
examlex backup <data-dir> [--output <path>] [--exclude <pattern>] [--json]

# 示例
examlex backup ./local/data --output backup-2026-07-05.tar.gz
examlex backup ./local/data --list backup-2026-07-05.tar.gz
```

### `examlex restore` — 数据恢复

```bash
examlex restore <backup-file> --data-dir <dir> [--force] [--dry-run] [--json]

# 示例
examlex restore backup-2026-07-05.tar.gz --data-dir ./local/data
examlex restore backup-2026-07-05.tar.gz --data-dir ./local/data --dry-run
```

### `examlex report` — 进度报告

```bash
examlex report
  --ability-history <path>
  --ledger <path>
  [--error-summary <path>]
  [--output <path>]
  [--days <n>]
  [--title <text>]

# 示例
examlex report \
  --ability-history ability-history.json \
  --ledger practice-ledger.json \
  --days 30 \
  --output progress-report.html
```

### `examlex vocab` — 词汇量估算

```bash
examlex vocab --interactive [--output <path>]
examlex vocab --wordlist <answers.json> [--output <path>]

# 示例
examlex vocab --interactive --output vocab-result.json
```

### `examlex extract` — 提取原始素材

```bash
examlex extract --input <url|file|name>
  [--type auto|video|book|text|person]   # 强制指定输入类型（默认自动检测）
  [--output-dir <dir>]                   # 覆盖会话输出目录
  [--json]                               # JSON 格式输出

# 示例
examlex extract --input 四级阅读技巧.md --type text
examlex extract --input VIDEO_URL --type video
```

### `examlex validate` — 验证蒸馏策略

```bash
examlex validate --artifacts-dir <path>
  [--json]                               # JSON 格式输出

# 示例
examlex validate --artifacts-dir ./sessions/session-001
```

底层命令：`validate-strategies`。执行格式校验和 Darwin 6 维结构评分（满分 59 分），结果写入 `validation_report.json`。

### `examlex commit` — 提交策略到库

```bash
examlex commit --artifacts-dir <path>
  --library <strategy-library.json>
  [--json]                               # JSON 格式输出

# 示例
examlex commit --artifacts-dir ./sessions/session-001 --library strategy-library.json
```

底层命令：`commit-strategies`。执行 ratchet 检查（新策略 Darwin 分需超过已有记录），原子写入策略库。

### `examlex resume` — 续跑蒸馏会话

```bash
examlex resume <session-id> [--sessions-root <dir>] [--json]
examlex resume 12345678-1234-1234-1234-123456789abc --json
```

该命令读取已有的管线状态，返回当前阶段、产物目录和下一步操作，不会创建新会话。

### `examlex sessions-cleanup` — 陈旧会话归档

```bash
examlex sessions-cleanup [--sessions-root <dir>] [--archive-root <dir>] [--older-than-hours 24]
examlex sessions-cleanup --sessions-root sessions --older-than-hours 24 --apply
```

默认只预览，不修改文件。`--apply` 仅移动符合条件的非终态会话，并拒绝覆盖已经存在的归档目标。

### `examlex check-deps` — 检查依赖

```bash
examlex check-deps

# 示例
examlex check-deps
```

底层命令：`check-deps`。检查 ffmpeg、yt-dlp 等外部工具是否可用，用于视频/音频提取前的环境验证。

### `examlex ops-check` — 运维检查

```bash
examlex ops-check
  [--library <strategy-library.json>]    # 可选，用于业务结果检查
  [--json]                               # JSON 格式输出

# 示例
examlex ops-check
examlex ops-check --library strategy-library.json --json
```

底层命令：`ops-check`。运行 13 项运维就绪检查（环境、配置、数据完整性等），返回通过/警告/失败报告。

---

## 与传统 CLI 命令对照

如果你习惯直接用底层命令，两种方式等价：

```bash
# 快捷方式
examlex plan profile.json --ability ability.json

# 等价底层命令
python -m examlex daily-plan --profile profile.json --ability ability.json

# 等价 pip 安装后命令
examlex daily-plan --profile profile.json --ability ability.json
```
