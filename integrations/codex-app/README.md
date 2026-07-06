# Codex App Integration

Install the Skill for Codex:

```bash
npx skills add your-org/english-exam-ai-tutor  # 替换为你的组织名/用户名 (replace with your org/username)
```

For the main Skill plus shortcut Skills:

```powershell
.\install.ps1 codex
```

The optional adapter config in `agents\openai.yaml` documents a minimal public-safe agent entry. It contains no secrets and should be treated as an example for local Codex App routing.

Use Skill calls inside Codex App:

```text
/english-exam-ai-tutor Build today's plan from my learner profile and ability profile.
/learning-planner Make a CET4 550+ weekly plan.
/grammar-corrector Check this paragraph and return a correction report.
/reading-navigator Break down this reading passage.
```

Python scripts are internal automation helpers. Codex App can run them after the Skill has interpreted the task.

Do not copy private prompt text into adapter configs or shared transcripts.
