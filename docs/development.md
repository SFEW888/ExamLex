# Development

This project favors deterministic standard-library scripts over hidden local setup.

## Source Layout

- `skills/examlex/`: canonical portable public-safe Skill, implementation, and resource package.
- `examlex/`: thin compatibility package for the historical CLI and import path.
- `scripts/`: repository installers and validation.
- `tests/`: unit tests for scripts, CLI behavior, installers, and project invariants.

The project does not use a separate `src/` directory because the canonical importable package is the Agent Skill under `skills/`.

## Local Checks

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
python -m pip install ".[quality,security]"
python -m ruff check .
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
python -m bandit -q -r skills/examlex/scripts scripts -ll
python -m pip_audit .
python -m coverage run -m unittest discover -s tests -q
python -m coverage report
git diff --check
```

For CLI changes, also run a smoke command:

```powershell
python -m examlex --help
```

## Change Rules

- Edit automation scripts under `skills/examlex/scripts/`, then run `python skills\examlex\scripts\sync_mirror.py` to repair the compatibility bridge and verify it with `--check`.
- Add or update tests for behavior changes.
- Keep the portable Skill directory free of root-style project docs.
- Keep generated files in `local/`, `test-artifacts/`, or another ignored path.
