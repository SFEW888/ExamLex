# Codex App Integration

Clone [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex), then install the main Skill plus shortcut Skills for Codex App:

```powershell
git clone https://github.com/SFEW888/ExamLex.git
Set-Location ExamLex
.\install.ps1 codex
```

The optional adapter config in `agents\openai.yaml` documents a minimal public-safe agent entry. It contains no secrets and should be treated as an example for local Codex App routing.

Use Skill calls inside Codex App:

```text
/examlex Build today's plan from my learner profile and ability profile.
/learning-planner Make a CET4 550+ weekly plan.
/grammar-corrector Check this paragraph and return a correction report.
/reading-navigator Break down this reading passage.
```

Python scripts are internal automation helpers. Codex App can run them after the Skill has interpreted the task.

Do not copy private prompt text into adapter configs or shared transcripts.
