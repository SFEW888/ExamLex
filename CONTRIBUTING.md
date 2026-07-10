# Contributing

Thank you for helping improve ExamLex.

This project is public-safe by default. Contributions must keep private prompt bodies out of the repository, preserve deterministic script behavior, and include focused validation for behavior changes.

## Local Setup

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
```

Optional editable install:

```powershell
python -m pip install -e .
examlex --help
```

## Contribution Rules

- Keep `skills/examlex/` portable: `SKILL.md`, `scripts/`, `references/`, and `assets/` only.
- Keep private prompt bodies out of public files. Use placeholders such as `[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]`.
- Mirror automation script changes between `skills/examlex/scripts/` and `examlex/scripts/`.
- Use `total_items` and `correct_items` for practice records.
- Add or update tests when changing scripts, validators, schemas, templates, or scoring behavior.
- Do not add dependencies unless there is a clear project-level need.

## Pull Request Checklist

- `python scripts\validate_repo.py --root . --json` passes.
- `python -m unittest discover -s tests` passes.
- `git diff --check` passes.
- Public-safe prompt policy is preserved.
- Documentation is updated when commands, files, or workflows change.

See [docs/contributing.md](docs/contributing.md) for project-specific details.
