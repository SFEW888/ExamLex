# Release

This repository is pre-1.0. Use semantic versioning once the public CLI and Skill contract are stable.

## Versioning

Use `X.Y.Z`:

- `X`: incompatible public contract changes,
- `Y`: backward-compatible features,
- `Z`: backward-compatible fixes.

## Release Checklist

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
git diff --check
```

Before tagging:

- update `CHANGELOG.md`,
- verify README quick-start commands,
- verify platform adapter notes,
- confirm `.env`, learner records, and private prompts are untracked,
- confirm `pyproject.toml` remains in `public-safe` mode.

## GitHub Release Notes

Include:

- added features,
- fixed issues,
- changed behavior,
- breaking changes,
- upgrade notes,
- known limitations,
- contributors.
