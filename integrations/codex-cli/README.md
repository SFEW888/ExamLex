# Codex CLI Integration

Clone [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex), then install the main Skill plus shortcut Skills for Codex CLI:

```powershell
git clone https://github.com/SFEW888/ExamLex.git
Set-Location ExamLex
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
