# Claude Code Integration

Install the portable Skill into Claude Code's local skills directory:

```bash
npx skills add your-org/english-exam-ai-tutor  # 替换为你的组织名/用户名 (replace with your org/username)
```

For the main Skill plus shortcut Skills:

```powershell
.\install.ps1 claude
```

After installation, start with the `english-exam-ai-tutor` Skill when a learner asks about CET-4, CET-6, or postgraduate English. Keep public-safe mode for shared work. Use full-local mode only with private prompt assets that remain outside this repository.

Use Skill calls inside Claude Code:

```text
/english-exam-ai-tutor Build today's plan from my learner profile and ability profile.
/learning-planner Make a CET6 600+ weekly plan.
/grammar-corrector Check this paragraph and return a correction report.
/reading-navigator Break down this reading passage.
```

Python scripts are internal automation helpers. Claude Code can run them after the Skill has interpreted the task; users should not need to call them as the primary workflow.
