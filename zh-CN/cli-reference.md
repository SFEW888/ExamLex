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
| `examlex source-list [opts]` | `source-list` | 👤 | 列出合并后的四六级/考研题源及证据等级 |
| `examlex source-collect --source <id> [opts]` | `source-collect` | 🤖 | 从已验证 RSS/Atom 入口建立本地元数据索引 |
| `examlex source-fetch --source <id> --item <id> --kind <text\|media>` | `source-fetch` | 🤖 | 显式获取一条已索引的公开正文或媒体 |
| `examlex ingest <file> [opts]` | `ingest-strategy` | 👤 | 从文件提取策略写入策略库 |
| `examlex strategies [opts]` | `list-strategies` | 👤 | 列出/搜索已摄入的策略 |
| `examlex strategy-db import-json\|export-json [opts]` | `strategy-db` | 🔧 | 在 JSON 与事务型 SQLite 策略库之间迁移 |
| `examlex validate --artifacts-dir <path>` | `validate-strategies` | 🤖 | 验证蒸馏策略格式并计算 Darwin 6 维结构评分（第 3 阶段） |
| `examlex commit --artifacts-dir <path> --library <path>` | `commit-strategies` | 🤖 | 通过 ratchet 检查将策略原子写入策略库（第 5 阶段） |
| `examlex validate-exam-artifact --kind <paper\|answerbook> --file <json>` | `validate-exam-artifact` | 🔧 | 校验五类考试整卷与详细答案册契约 |

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
| `examlex word --input <json> [--output <md>]` | `vocab-card` | 👤 | 生成精细背词词条版块 |
| `examlex prompt-check --private-dir <dir> [opts]` | `prompt-check` | 👤 | 校验仓库外的八助教私有提示词集，不输出正文 |
| `examlex tutor-prepare --request <text> [opts]` | `tutor-prepare` | 🤖 | 路由请求并返回最多两个安全澄清问题 |

### 🔧 维护者

| 底层命令 | 触发 | 说明 |
|----------|:--:|------|
| `check-deps` | 🔧 | 检查外部工具依赖（ffmpeg、yt-dlp 等） |
| `ops-check` | 🔧 | 运行 13 项运维就绪检查 |
| `resume` | 👤 | 读取已有蒸馏会话并返回续跑指引 |
| `sessions-cleanup` | 🔧 | 检查或手动清理会话产物；成功提交还会自动执行保留策略 |
| `capacity-monitor` | 🔧 | 后台执行保留策略并对策略库阈值发出复核提醒 |
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
examlex ingest "reading-method.md" --library strategy-library.json
```

相同源文件在考试类型、模块、来源类型、蒸馏方式、来源 URL 和显式结构化参数均相同
时，重复摄入会直接复用已有策略，不再追加重复条目。同一文件用于不同考试或模块时，
仍可生成独立策略。

### `examlex strategies` — 策略库

```bash
examlex strategies --library <path> [--search <keyword>] [--duplicates] [--duplicate-limit 20] [--json]

# 示例
examlex strategies --library strategy-library.json --search 阅读
examlex strategies --library strategy-library.json --duplicates
```

`--duplicates` 只列出供复核的候选组，依据包括相同摄入指纹、规范化正文、相同标题与
适用范围，以及历史版本间的重复正文。该命令不删除数据；删除历史版本前必须先核对
学习记录中的版本引用。

以 `.db`、`.sqlite` 或 `.sqlite3` 结尾的策略库会自动使用事务型 SQLite 后端；JSON
仍作为便携交换格式继续支持。

### `examlex strategy-db` — 迁移策略库存储

```bash
examlex strategy-db import-json --input strategy-library.json --database strategy-library.db --json
examlex strategy-db export-json --database strategy-library.db --output strategy-library.json --json
```

SQLite 将当前策略与不可变历史版本存入分离且带索引的表，并保证导出后的 JSON 结构
可回读。近似重复只作为用户复核候选；导入、导出、列出和写入都不会自动删除策略。

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

### `examlex word` — 生成背词词条版块

```bash
examlex word --input vocabulary-block.json --output vocabulary-block.md
examlex vocab-card --input vocabulary-block.json --validate-only --json
```

输入必须包含序号、单词、音标、按词性区分的释义、构词或记忆说明、双语语境例句，
以及至少一个派生词或同族词；输出还会附主动回忆任务。学习者表达“背单词”意图时，
默认使用这一精细结构，只有明确要求简版时才可改为紧凑清单。

### `examlex validate-exam-artifact` — 校验整卷或答案册

```bash
examlex validate-exam-artifact --kind paper --file paper.json --json
examlex validate-exam-artifact --kind answerbook --file answers.json --paper paper.json --json
```

整卷校验覆盖四级、六级、考研英语、专四和专八的题型配置、编号、题量、证据角色和
“非官方模拟”声明；答案册校验会强制检查详细解析、题干与全部选项翻译、证据范围、
推理步骤、逐项排除，以及写作、阅读、听力、完形和翻译的专用解析包。

### `examlex prompt-check` — 校验外部私有提示词

```powershell
examlex prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" [--json]
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --save --json
```

目录中必须且只能包含八份 UTF-8 `<role-id>.md` 文件，分别对应八个公开角色契约。命令会校验文件名与文件安全性，只报告字节大小和 SHA-256 哈希，绝不打印提示词正文或目录路径。`--save` 会把外部目录写入本机用户配置。私有目录必须放在仓库之外，且不得提交。

### `examlex tutor-prepare` — 路由并澄清助教请求

```powershell
examlex tutor-prepare --request "纠正：I has finished it yesterday." [--role auto] [--asked-field <name>] [--json]
python run.py tutor-prepare --request "制定六级学习计划" --json
```

该公开安全预检不加载私有提示词，也不调用模型。它会选择一至三个角色，并返回最多两个关键澄清问题。后续轮次可重复传入 `--asked-field` 标记已经问过的字段，从而避免重复追问。真正的私有执行是通过 `run_tutor_turn()` 与注入的受信提供器完成的进程内库调用。

### `examlex source-list` — 查看带证据等级的题源目录

```bash
examlex source-list
  [--exam cet|postgraduate]
  [--section <题型>]
  [--evidence S|A|B|C|R]
  [--media article|audio|video|report]
  [--collectable]
  [--references]
  [--json]
```

媒体来源在完成文章级真题比对前保持 `B` 或 `C`。升级到 `A` 必须补齐考试、
题型、原文标题或 URL 和比对证据。目录不保存互相冲突的媒体百分比。

### `examlex source-collect` — 索引已验证 RSS/Atom

```bash
examlex source-collect --source <来源ID或别名>
  [--limit 1..100]
  [--content-mode metadata|text]
  [--delay 0..60]
  [--output-dir <目录>]
  [--json]
```

默认使用 `metadata`。选择 `text` 后，也只会提取公开且 `robots.txt` 允许的
网页正文，不发送 Cookie、登录信息，也不绕过付费墙。

### `examlex source-fetch` — 获取一条已索引素材

```bash
examlex source-fetch --source <来源ID或别名> --item <item-id> --kind text
  [--output-dir <目录>] [--json]

examlex source-fetch --source <来源ID或别名> --item <item-id> --kind media
  [--max-media-mb 1..1024] [--output-dir <目录>] [--json]
```

媒体下载必须来自维护订阅入口中的音频/视频 enclosure，并且必须显式选择条目；
默认硬限制为 100 MiB。证据、安全和模拟题溯源规范见
`skills/examlex/references/source-collection.md`。

### `examlex extract` — 提取原始素材

```bash
examlex extract --input <url|file|name>
  [--type auto|video|book|text|person]   # 强制指定输入类型（默认自动检测）
  [--output-dir <dir>]                   # 覆盖会话输出目录
  [--json]                               # JSON 格式输出

# 示例
examlex extract --input reading-method.md --type text
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

### `examlex sessions-cleanup` — 陈旧会话归档或瘦身

```bash
examlex sessions-cleanup [--sessions-root <dir>] [--archive-root <dir>] [--older-than-hours 24]
examlex sessions-cleanup --sessions-root sessions --older-than-hours 24 --apply
examlex sessions-cleanup --older-than-hours 168 --prune-terminal-artifacts
examlex sessions-cleanup --older-than-hours 168 --prune-terminal-artifacts --apply
```

默认只预览，不修改文件。未指定瘦身选项时，`--apply` 仅移动符合条件的非终态会话，
并拒绝覆盖已经存在的归档目标。`--prune-terminal-artifacts` 改为选择陈旧且已经
提交成功的会话；只有再加 `--apply`，才会删除可重新生成的全文、音频、转录稿和章节
提取物。管线状态、蒸馏策略、验证/评估报告及其他审计文件仍会保留。

该命令继续用于检查和手动维护。除此之外，成功执行 `examlex commit` 会自动把标准受管
会话标记为 `committed`，清理超过 168 小时的可再生成产物，并按从旧到新的顺序执行
4 GiB 硬上限。活动会话文件不计入该上限。策略库达到 100 MiB 时只发出提醒并列出有限
数量的重复候选，不会自动修改或删除策略及其不可变历史版本。

### `examlex capacity-monitor` — 后台容量策略

```powershell
examlex capacity-monitor --json
examlex capacity-monitor --strategy-library strategy-library.db --notify-windows
powershell -ExecutionPolicy Bypass -File scripts/install_capacity_monitor.ps1
```

每次运行只对可重新生成的音频、字幕、转录稿、全文和章节提取物执行时限与硬容量
上限，并写入持久状态报告。策略库达到阈值时会另写警告报告，列出可能重复的版本供
用户选择，并可显示 Windows 通知；策略和不可变历史版本始终不会被自动删除。安装
脚本默认注册一个每 30 分钟运行一次的当前用户计划任务。

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
  [--offline]                            # 跳过哔哩哔哩、YouTube 和 SiliconFlow 联网检查

# 示例
examlex ops-check
examlex ops-check --library strategy-library.json --json
examlex ops-check --offline --json
```

底层命令：`ops-check`。运行 13 项运维就绪检查（环境、配置、数据完整性等），返回通过/警告/失败报告。需要离线或确定性 CI 诊断时使用 `--offline`。

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
