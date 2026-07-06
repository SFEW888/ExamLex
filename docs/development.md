# Development

This project favors deterministic standard-library scripts over hidden local setup.

## Source Layout

- `skills/english-exam-ai-tutor/`: portable public-safe Skill package.
- `skills/english_exam_ai_tutor/`: importable Python mirror used by the CLI and tests.
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
python -m skills.english_exam_ai_tutor --help
```

## Change Rules

- Update both script mirrors when editing automation scripts.
- Add or update tests for behavior changes.
- Keep the portable Skill directory free of root-style project docs.
- Keep generated files in `local/`, `test-artifacts/`, or another ignored path.
