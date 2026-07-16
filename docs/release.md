# Release

This repository is pre-1.0. Use semantic versioning once the public CLI and Skill contract are stable.

Canonical repository: [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex).

## Versioning

Use `X.Y.Z`:

- `X`: incompatible public contract changes,
- `Y`: backward-compatible features,
- `Z`: backward-compatible fixes.

## Release Checklist

```powershell
$repoRoot = (Resolve-Path .).Path
$releasePaths = @('build', 'dist', 'examlex.egg-info') | ForEach-Object { Join-Path $repoRoot $_ }
if ($releasePaths | Where-Object { -not $_.StartsWith($repoRoot + '\') }) { throw 'Unsafe release cleanup target.' }
Remove-Item -LiteralPath $releasePaths -Recurse -Force -ErrorAction SilentlyContinue

python -m pip install ".[quality,security,release]"
python scripts\validate_repo.py --root . --json
python skills\examlex\scripts\sync_mirror.py --check
python -m ruff check .
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
python -m bandit -q -r skills/examlex/scripts scripts -ll
python -m pip_audit .
python -m coverage run -m unittest discover -s tests -q
python -m coverage report
python -m build
python scripts\smoke_test_wheel.py dist
git diff --check
```

Run the cleanup block only from the repository root. It confirms every target
is under that root before deleting stale build outputs. The isolated wheel smoke
test catches stale build caches, missing canonical resources, duplicated package
resources, and missing public CLI commands before a release is tagged.

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
