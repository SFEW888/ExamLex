# Claude Code 集成

把可移植 Skill 安装到 Claude Code 的本地 skills 目录：

```powershell
python scripts\install_claude.py --dry-run --json
python scripts\install_claude.py --force
```

安装后，当学习者提出四级、六级或考研英语相关任务时，优先使用 `english-exam-ai-tutor` Skill。共享工作保持 public-safe 模式。只有在私有提示词资产仍然位于仓库之外时，才使用 full-local 模式。

推荐闭环：

```powershell
python -m skills.english_exam_ai_tutor validate-profile --profile learner-profile.json
python -m skills.english_exam_ai_tutor daily-plan --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json
```
