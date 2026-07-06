# Cursor Integration

Install Cursor-compatible local rules:

```powershell
.\install.ps1 cursor
```

Cursor should use the public-safe Skill instructions and repository docs for learner workflows. Keep generated plans anchored in profile, ability, ledger, and error-summary files.

Use short scenario prompts in Cursor chat or rules:

```text
english-exam-ai-tutor: Build today's plan from my learner profile and ability profile.
learning-planner: Make a CET4 550+ weekly plan.
grammar-corrector: Check this paragraph and return a correction report.
reading-navigator: Break down this reading passage.
```

Python scripts are internal automation helpers. Cursor can run them after the Skill instructions have interpreted the task.

Do not paste private prompt bodies into Cursor rules or committed files.
