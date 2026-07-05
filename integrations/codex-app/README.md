# Codex App Integration

Install the Skill for Codex:

```powershell
python scripts\install_codex.py --dry-run --json
python scripts\install_codex.py --force
```

The optional adapter config in `agents\openai.yaml` documents a minimal public-safe agent entry. It contains no secrets and should be treated as an example for local Codex App routing.

Use the same evidence loop in Codex App:

```powershell
python scripts\validate_repo.py --root . --json
python skills\english-exam-ai-tutor\scripts\validate_profile.py --profile learner-profile.json
python skills\english-exam-ai-tutor\scripts\generate_daily_plan.py --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json
```

Do not copy private prompt text into adapter configs or shared transcripts.
