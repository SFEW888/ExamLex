# GitHub Project Quality

The public [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex) repository is organized to meet open-source project quality expectations, not only as a local Skill folder.

## Quality Bar

- Clear first screen: `README.md` explains the purpose, supported exams, quick start, installation, prompt modes, layout, documentation, and validation.
- Community health: root-level `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `LICENSE`, and `CHANGELOG.md`.
- Contribution workflow: `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, and `.github/workflows/ci.yml`.
- Deterministic checks: `scripts/validate_repo.py`, detect-secrets, Bandit, pip-audit, a 55% branch-coverage floor, Ruff, unit tests, exact generated-mirror validation, and `git diff --check`.
- Efficient CI: all supported Python and operating-system combinations run tests, while repository validation, distribution builds, and isolated wheel smoke tests run only once.
- Skill portability: `skills/examlex/` keeps only the required Skill package files and resources.
- Prompt safety: public files use placeholders and keep private prompt bodies out of the repository.

## Release Readiness Checklist

Before publishing or tagging a release:

```powershell
python scripts\validate_repo.py --root . --json
python skills\examlex\scripts\sync_mirror.py --check
python -m pip install ".[quality,security]"
python -m ruff check .
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
python -m bandit -q -r skills/examlex/scripts scripts -ll
python -m pip_audit .
python -m coverage run -m unittest discover -s tests -q
python -m coverage report
git diff --check
```

Also confirm:

- issue templates still match current support categories,
- README command examples run on Windows PowerShell,
- platform adapters mention Claude Code, Codex CLI, Codex App, and Cursor,
- no generated test artifacts or local prompt files are tracked,
- public-safe mode remains set in `pyproject.toml`.
