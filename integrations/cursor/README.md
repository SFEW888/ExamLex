# Cursor Integration

Install Cursor-compatible local rules:

```powershell
python scripts\install_cursor.py --dry-run --json
python scripts\install_cursor.py --force
```

Cursor should use the public-safe Skill instructions and repository docs for learner workflows. Keep generated plans anchored in profile, ability, ledger, and error-summary files.

For daily operation:

```powershell
python skills\english-exam-ai-tutor\scripts\record_practice.py --ledger practice-ledger.json --date 2026-07-05 --exam-type CET4 --module vocabulary --task-id vocab-context-01 --duration-minutes 15 --total-items 20 --correct-items 16 --error-tags VOCAB_CONTEXT_MISUSE --print-record
python skills\english-exam-ai-tutor\scripts\summarize_errors.py --ledger practice-ledger.json --output error-summary.json
```

Do not paste private prompt bodies into Cursor rules or committed files.
