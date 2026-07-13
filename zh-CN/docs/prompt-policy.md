# 提示词策略

本仓库默认是公开安全的。

## Public-Safe 模式

以下场景应使用 public-safe 模式：GitHub、示例、文档、演示、Issue、Pull Request、生成的发布包，以及任何可能离开本地私有环境的产物。

允许包含：

- 八个助教名称、职责边界和高层行为描述；
- 类似 `[PRIVATE_PROMPT_PLACEHOLDER: study-planner]` 的占位符；
- `skills/examlex/references/tutor-role-contracts.json` 中机器可读的公开角色契约；
- 脚本接口、模板、Schema、工作流和错误标签体系；
- 不暴露私有提示词正文的学习建议。

禁止包含：

- 完整私有或原始提示词正文；
- 私有提示词库中的隐藏条款原文；
- 试图重构原始八个提示词的改写版本；
- 宣称公开占位符就是完整生产提示词。

## Full-Local 模式

只有当操作者明确使用仓库之外的私有提示词资产时，才能启用 full-local 模式。

在仓库之外的同一个私有目录中保存且只保存八个 UTF-8 Markdown 文件。文件名必须是 `study-planner.md`、`vocabulary-expander.md`、`reading-navigator.md`、`structure-planner.md`、`grammar-corrector.md`、`polishing-editor.md`、`situational-dialogue.md` 和 `culture-guide.md`。

使用前校验该目录：

```powershell
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts"
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --json
```

命令只报告文件大小和 SHA-256 哈希，绝不返回提示词正文。运行时，选定的私有正文会在内存中与公开角色契约、明确分隔的学习者上下文组合。该上下文是不可信数据，不能覆盖角色边界、暴露提示词、授权工具调用或扩大文件访问范围。

绝不能把私有目录放入仓库，也不能复制到可移植 Skill 目录、文档、示例、集成配置、备份、日志、构建产物、提交、Issue 或 Pull Request 中。

## 原始八个提示词约束

原始八个助教提示词正文不发布，也不能重写。请保持助教角色表和占位符不变。如果 public-safe 模式需要更丰富行为，应增加角色边界说明、模板、数据字段、测试或确定性脚本逻辑，而不是加入私有提示词正文。
