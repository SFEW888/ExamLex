# Contributing

Contributions should keep the project public-safe, deterministic, and easy to validate on Windows.

## Validation

Run:

```powershell
python scripts\validate_repo.py --root . --json
python -m pip install ".[quality,security]"
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
python -m bandit -q -r skills/examlex/scripts scripts -ll
python -m pip_audit .
git diff --check
```

For code changes, run focused tests or the full suite:

```powershell
python -m unittest discover -s tests
```

## Prompt Safety

Do not add full private prompt bodies. Keep public docs limited to role descriptions, placeholders, policies, workflows, templates, schemas, and script behavior.

Before finishing prompt-adjacent work, search for any known private prompt text. No private prompt body should remain in tracked project files.

## Error Taxonomy Changes

When adding or changing tags:

- update `skills/examlex/references/error-taxonomy.md`,
- update script mappings in both portable and importable script mirrors,
- add or adjust focused tests,
- keep `total_items` and `correct_items` as the practice count fields.

## Installer Safety

Installers should default to clear destinations, support `--dry-run`, and avoid secrets. Destructive overwrites should require explicit flags such as `--force`.

Do not add external dependencies unless the project explicitly adopts them. The current toolkit is standard-library only.
