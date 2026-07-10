# Development

This project favors deterministic standard-library scripts over hidden local setup.

## Source Layout

- `skills/examlex/`: portable public-safe Skill package.
- `examlex/`: importable Python mirror used by the CLI and tests.
- `scripts/`: repository installers and validation.
- `tests/`: unit tests for scripts, CLI behavior, installers, and project invariants.

The project does not use a separate `src/` directory because the distributable artifact is an agent Skill plus an importable mirror under `skills/`.

## Local Checks

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
git diff --check
```

For CLI changes, also run a smoke command:

```powershell
python -m examlex --help
```

## Change Rules

- Edit automation scripts under `skills/examlex/scripts/`, then run `python skills\examlex\scripts\sync_mirror.py --sync` and verify with `--check`.
- Add or update tests for behavior changes.
- Keep the portable Skill directory free of root-style project docs.
- Keep generated files in `local/`, `test-artifacts/`, or another ignored path.
