# 快速开始

本指南帮助你在全新克隆后安装 Skills。最简路径与其他 Agent 原生 Skill 仓库一致，一行命令即可完成。

## 环境要求

- Python 3.10 或更新版本
- Git
- 使用 `npx skills add` 需要 Node.js/npm；使用克隆安装器需要 Git 加 PowerShell 或 POSIX shell
- 克隆安装器内部需要 Python 3.10 或更新版本

当前工具包不依赖任何第三方 Python 包。

## 一行命令安装

```bash
npx skills add your-org/english-exam-ai-tutor
```

在仓库发布到 GitHub 并填入真实组织名后，以上命令会安装主 Skill `english-exam-ai-tutor`。重启 Agent，运行 `/skills`，即可在对话中调用该 Skill。

## 克隆安装（含快捷 Skill）

如果你希望同时安装主 Skill 和全部 8 个快捷 Skill，请使用此方式。

macOS/Linux：

```bash
git clone https://github.com/your-org/english-exam-ai-tutor.git ~/.english-exam-ai-tutor
cd ~/.english-exam-ai-tutor
./install.sh codex
./install.sh claude
```

Windows PowerShell：

```powershell
git clone https://github.com/your-org/english-exam-ai-tutor.git
cd english-exam-ai-tutor
.\install.ps1 codex
.\install.ps1 claude
```

如果只想在当前项目中安装 Skill，使用项目本地安装：

```powershell
.\install.ps1 codex -Project
.\install.ps1 claude -Project
```

预览安装目标：

```bash
./install.sh codex --dry-run
./install.sh claude --dry-run
```

在 Agent 中验证：

```text
/skills
/english-exam-ai-tutor 帮我为 CET4 550+ 制定一周计划
/learning-planner 帮我生成本周任务
/grammar-corrector 批改这段作文
```

## 快捷 Skill 名称

在 Agent 对话中使用以下斜杠命令替代长 Python 命令：

| 场景 | 斜杠调用 |
| --- | --- |
| 完整备考流程 | `/english-exam-ai-tutor` |
| 学习计划 | `/learning-planner` |
| 词汇 | `/vocabulary-builder` |
| 阅读 | `/reading-navigator` |
| 写作结构 | `/structure-planner` |
| 语法批改 | `/grammar-corrector` |
| 润色 | `/polish-wizard` |
| 情景对话 | `/scenario-dialog` |
| 文化背景 | `/culture-guide` |

## 支持的考试

本助教支持五种考试类型：

| 考试 | 目标分段 | 特有模块 |
|------|---------|----------|
| CET-4 | 425~499、500~550、550+、600+ | — |
| CET-6 | 425~499、500~550、550+、600+ | — |
| 考研英语 | 50+、70~80、80+、90+ | — |
| TEM-4 | 60~69、70~79、80+ | 听写、语言知识 |
| TEM-8 | 60~69、70~79、80+ | 校对改错 |

## 新特性

- **词汇量估算**：`tutor vocab --interactive` — 使用 Yes/No 抽样加虚报修正
- **计时练习**：`tutor log --timed` — 自动查表限时 + 超时追踪
- **间隔重复**：错误汇总中自动计算复习紧迫度评分
- **进度可视化**：`tutor report` — 生成独立 HTML，含雷达图/趋势图/错误图（SVG）
- **词汇池**：内置 650 词，覆盖 5 个考试等级
- **常见错误库**：21 条精选错误模式，附示例
- **范文库**：带评分数据的范文样本，用于评分锚定
- **备份与恢复**：`tutor backup` / `tutor restore`，支持 tar.gz

## 运行可选 CLI

当你需要直接从终端运行确定性工具时，使用以下封装命令：

```bash
bin/tutor check examples/sample-learner-profile.yaml
bin/tutor plan examples/sample-learner-profile.yaml --ability examples/sample-ability-profile.yaml --output daily-plan.json
bin/tutor strategies --library strategy-library.json
```

PowerShell：

```powershell
.\bin\tutor.ps1 check examples/sample-learner-profile.yaml
.\bin\tutor.ps1 plan examples/sample-learner-profile.yaml --ability examples/sample-ability-profile.yaml --output daily-plan.json
```

底层 Python 模块供维护者和调试使用：

```powershell
python -m skills.english_exam_ai_tutor --help
```

详见 [../cli-reference.md](../cli-reference.md) 获取所有简短命令。

## 验证仓库

维护者仍可直接运行确定性检查：

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
```

## 可选的可编辑安装

```powershell
python -m pip install -e .
english-exam-tutor --help
```

生成的本地文件（如 `daily-plan.json`、`.env`、学习记录等）应保持不被版本跟踪。
