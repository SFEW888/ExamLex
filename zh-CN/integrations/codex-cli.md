# Codex CLI 集成

为 Codex CLI 安装 Skill：

```powershell
python scripts\install_codex.py --dry-run --json
python scripts\install_codex.py --force
```

之后在四级、六级或考研英语任务中使用已安装的 `english-exam-ai-tutor` Skill。如果是在当前仓库内开发或调试，也可以直接运行本地脚本。

常用命令：

```powershell
python scripts\validate_repo.py --root . --json
python -m skills.english_exam_ai_tutor summarize-errors --ledger practice-ledger.json --output error-summary.json
python -m skills.english_exam_ai_tutor update-ability --ability ability-profile.json --ledger practice-ledger.json --output ability-profile.next.json
```

提交和 Pull Request 中应保持 public-safe 输出。
