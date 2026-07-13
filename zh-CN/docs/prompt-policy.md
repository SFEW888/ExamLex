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
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --save
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --json
```

命令只报告文件大小和 SHA-256 哈希，绝不返回提示词正文或已配置路径。`--save` 将外部路径写入用户本机 `~/.examlex/prompt-config.json`，也可使用 `EXAMLEX_PRIVATE_PROMPT_DIR`。

公开的 `tutor-prepare` 命令只执行路由与有限澄清：复用已知需求，并在同一轮最多询问两个关键问题；它不加载私有提示词，也不调用模型。真正的私有执行只能通过进程内 `run_tutor_turn()` API 和注入的受信提供器完成。原始学习者请求仍是提供器的 user message，结构化上下文则放入明确的不可信数据边界。提供器异常会转换为固定错误，疑似提示词泄漏的输出会被阻断。

不得通过 stdout、Shell 参数、临时文件、学习者可见消息或普通日志传递组合提示词。本地提供器默认允许；远程提供器会接触私有提示词，必须由调用方明确授权，且 ExamLex 无法保证其留存或日志策略。没有受信提供器时保持 public-safe，不得声称已应用私有提示词。

绝不能把私有目录放入仓库，也不能复制到可移植 Skill 目录、文档、示例、集成配置、备份、日志、构建产物、提交、Issue 或 Pull Request 中。

## 原始八个提示词约束

原始八个助教提示词正文不发布，也不能重写。请保持助教角色表和占位符不变。如果 public-safe 模式需要更丰富行为，应增加角色边界说明、模板、数据字段、测试或确定性脚本逻辑，而不是加入私有提示词正文。
