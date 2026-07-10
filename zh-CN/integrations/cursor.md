# Cursor 集成

安装 Cursor 兼容的本地规则：

```powershell
python scripts\install_cursor.py --dry-run --json
python scripts\install_cursor.py --force
```

Cursor 应使用 public-safe Skill 说明和仓库文档来处理学习者流程。生成计划时，必须基于学习者档案、能力画像、练习记录和错误统计，而不是凭空生成。

日常操作示例：

```powershell
python -m examlex record-practice --ledger practice-ledger.json --date 2026-07-05 --exam-type CET4 --module vocabulary --task-id vocab-context-01 --duration-minutes 15 --total-items 20 --correct-items 16 --error-tags VOCAB_CONTEXT_MISUSE --print-record
python -m examlex summarize-errors --ledger practice-ledger.json --output error-summary.json
```

不要把私有提示词正文粘贴进 Cursor 规则或提交文件。
