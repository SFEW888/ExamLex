# Codex Notes

Use this repository as a public-safe Skill plus automation toolkit for CET-4, CET-6, and postgraduate English tutoring.

Install for Codex with:

```powershell
python scripts\install_codex.py --dry-run --json
python scripts\install_codex.py --force
```

Before making changes, inspect the existing Skill references and scripts. Do not revert unrelated edits, do not stage `test-artifacts/`, and do not add full private prompt text. Validate with `python scripts\validate_repo.py --root . --json` before finishing.
