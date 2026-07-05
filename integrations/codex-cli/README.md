# Codex CLI Integration

Install the Skill for Codex CLI:

```powershell
python scripts\install_codex.py --dry-run --json
python scripts\install_codex.py --force
```

Then use the installed `english-exam-ai-tutor` Skill for CET-4, CET-6, or postgraduate English tasks. For repository-local work, run scripts directly from this checkout.

Useful commands:

```powershell
python scripts\validate_repo.py --root . --json
python skills\english-exam-ai-tutor\scripts\summarize_errors.py --ledger practice-ledger.json --output error-summary.json
python skills\english-exam-ai-tutor\scripts\update_ability_profile.py --ability ability-profile.json --ledger practice-ledger.json --output ability-profile.next.json
```

Keep public-safe output in commits and pull requests.
