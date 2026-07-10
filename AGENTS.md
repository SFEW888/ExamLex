# Agent Instructions

This repository contains a public-safe English exam tutor Skill and deterministic automation scripts. Work from the repository root unless a command says otherwise.

- Keep public-safe mode intact. Do not add private prompt bodies or rewrite the original eight tutor prompts.
- Preserve the eight assistant roles and placeholder identifiers under `skills/examlex/references/assistant-roster.md`.
- Do not add `README.md` or `INSTALL.md` inside `skills/examlex/`.
- Use PowerShell-friendly commands in docs and examples.
- Keep generated `test-artifacts/` untracked and unstaged.
- Run `python scripts\validate_repo.py --root . --json` and prompt-safety checks before claiming documentation or adapter work is complete.
