# Codex CLI Integration

ExamLex is currently unpublished. From the local project root, install the main Skill plus shortcut Skills for Codex CLI:

```powershell
.\install.ps1 codex
```

Then use the installed `examlex` Skill for CET-4, CET-6, or postgraduate English tasks.

Use Skill calls inside Codex:

```text
/examlex Build today's plan from my learner profile and ability profile.
/learning-planner Make a CET4 550+ weekly plan.
/grammar-corrector Check this paragraph and return a correction report.
/reading-navigator Break down this reading passage.
```

For repository maintenance, validate the checkout with `python scripts\validate_repo.py --root . --json`.

Keep public-safe output in commits and pull requests.
