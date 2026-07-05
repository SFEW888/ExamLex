# Claude Code Integration

Install the portable Skill into Claude Code's local skills directory:

```powershell
python scripts\install_claude.py --dry-run --json
python scripts\install_claude.py --force
```

After installation, start with the `english-exam-ai-tutor` Skill when a learner asks about CET-4, CET-6, or postgraduate English. Keep public-safe mode for shared work. Use full-local mode only with private prompt assets that remain outside this repository.

Recommended loop:

```powershell
python skills\english-exam-ai-tutor\scripts\validate_profile.py --profile learner-profile.json
python skills\english-exam-ai-tutor\scripts\generate_daily_plan.py --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json
```
