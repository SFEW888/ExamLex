# 英语考试 AI 助教

English Exam AI Tutor 是一个面向英语四六级和考研英语备考的公开安全版 Agent Skill 与自动化脚本工具包。它把八个助教角色和一组确定性脚本结合起来，用于学习者档案校验、每日计划生成、练习记录、错误归因、能力画像更新、趋势分析和作文评分参考。

本项目设计为本地优先，可配合 Claude Code、Codex、Codex App 和 Cursor 使用。公开文件只包含角色边界、使用说明和私有提示词占位符；用户本地的完整私有提示词不会发布在这个仓库中。

## 支持对象

- 基础水平：基础偏弱、中等基础、基础较好。
- 四级、六级目标区间：`425~499`、`500~550`、`550+`、`600+`。
- 考研英语目标区间：`50+`、`70~80`、`80+`、`90+`。

脚本会根据学习者的时间预算生成现实可执行的任务，但不会承诺官方考试分数。

## 快速开始

在 PowerShell 中进入项目根目录：

```powershell
cd D:\Codex_project\英语\english-exam-ai-tutor
```

检查仓库结构并校验示例学习者档案：

```powershell
python scripts\validate_repo.py --root . --json
python -m skills.english_exam_ai_tutor validate-profile --profile examples\sample-learner-profile.yaml
```

生成每日学习计划：

```powershell
python -m skills.english_exam_ai_tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --output daily-plan.json
```

当练习后已经有错误统计时，把它输入下一次计划：

```powershell
python -m skills.english_exam_ai_tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --errors error-summary.json --output daily-plan.next.json
```

记录一次练习：

```powershell
python -m skills.english_exam_ai_tutor record-practice --ledger practice-ledger.json --date 2026-07-05 --exam-type CET4 --module writing --task-id writing-article-drill --duration-minutes 20 --total-items 10 --correct-items 7 --error-tags WRITING_ARTICLE_OMISSION --print-record
```

统计错误、更新能力画像、进行作文评分参考：

```powershell
python -m skills.english_exam_ai_tutor summarize-errors --ledger practice-ledger.json --output error-summary.json
python -m skills.english_exam_ai_tutor update-ability --ability examples\sample-ability-profile.yaml --ledger practice-ledger.json --output ability-profile.next.json
python -m skills.english_exam_ai_tutor score-writing --text "I think English study is important because it helps me read more and express ideas clearly." --exam-type CET4 --output writing-score.json
```

如果希望使用更短的命令，可以安装为可编辑包：

```powershell
python -m pip install -e .
english-exam-tutor validate-profile --profile examples\sample-learner-profile.yaml
english-exam-tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --output daily-plan.json
```

## 安装到不同平台

先预览安装目标：

```powershell
python scripts\install_claude.py --dry-run --json
python scripts\install_codex.py --dry-run --json
python scripts\install_cursor.py --dry-run --json
```

确认无误后安装：

```powershell
python scripts\install_claude.py --force
python scripts\install_codex.py --force
python scripts\install_cursor.py --force
```

平台适配说明：

- [Claude Code](integrations/claude-code.md)
- [Codex CLI](integrations/codex-cli.md)
- [Codex App](integrations/codex-app.md)
- [Cursor](integrations/cursor.md)

## 提示词模式

- `public-safe` 是默认模式，适用于 GitHub、示例、文档、演示和公开发布物。它只包含助教名称、职责边界、脚本接口、模板、结构和类似 `[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]` 的占位符。
- `full-local` 只用于本机私有环境，可以调用用户本地私有提示词资产，但这些资产不得进入公开仓库。
- 原始八个助教提示词正文不发布、不改写、不重构到公开文档、示例、适配器或 release 产物中。

详见 [提示词策略](docs/prompt-policy.md)。

## 仓库结构

```text
.
|-- docs/                         英文项目说明、架构、使用和考试指南。
|-- zh-CN/                        中文版文档目录。
|-- examples/                     示例学习者档案、能力画像、练习记录和作文版本。
|-- integrations/                 平台适配说明和最小配置。
|-- scripts/                      仓库校验和安装脚本。
|-- skills/english-exam-ai-tutor/ 可移植 public-safe Skill。
|-- skills/english_exam_ai_tutor/ 测试和命令行使用的可导入镜像。
|-- tests/                        单元测试。
`-- pyproject.toml                包元数据和 public-safe 模式配置。
```

## 中文文档

- [设计说明](docs/design.md)
- [架构说明](docs/architecture.md)
- [使用流程](docs/usage.md)
- [提示词策略](docs/prompt-policy.md)
- [贡献规范](docs/contributing.md)
- [四级指南](docs/cet4.md)
- [六级指南](docs/cet6.md)
- [考研英语指南](docs/postgraduate.md)
- [Skill 中文说明](skill/SKILL.md)

## 测试和校验

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
git diff --check
```

提交前还应确认公开文件中没有私有提示词正文，并确认可移植 Skill 目录中没有根级安装说明：

```powershell
Get-ChildItem -Name skills\english-exam-ai-tutor | Where-Object { $_ -in @('README.md','INSTALL.md') }
```
