# Troubleshooting

## Python Cannot Import The CLI

Run commands from the repository root:

```powershell
cd english-exam-ai-tutor
python -m skills.english_exam_ai_tutor --help
```

If using the short command, reinstall in editable mode:

```powershell
python -m pip install -e .
```

## Tests Fail In A Sandboxed Temp Directory

Some restricted Windows sandboxes deny writes to the default user temp directory. Re-run the same test command in a normal shell, or set a writable temp directory before running tests.

## Validation Reports A Script Mirror Mismatch

Copy the intended change between:

- `skills/english-exam-ai-tutor/scripts/`
- `skills/english_exam_ai_tutor/scripts/`

Then rerun:

```powershell
python scripts\validate_repo.py --root . --json
```

## Prompt Safety Check Fails

Remove private prompt bodies from public files. Public examples should use placeholders such as `[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]`.
