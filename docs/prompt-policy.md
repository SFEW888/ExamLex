# Prompt Policy

This repository is public-safe by default.

## Public-Safe Mode

Use public-safe mode for GitHub, examples, docs, demos, issue discussions, pull requests, generated release packages, and any artifact that may leave the local private environment.

Allowed content:

- eight assistant names, role boundaries, and high-level descriptions,
- placeholders such as `[PRIVATE_PROMPT_PLACEHOLDER: study-planner]`,
- the public machine-readable role contracts in `skills/examlex/references/tutor-role-contracts.json`,
- script interfaces, templates, schemas, workflows, and error taxonomy,
- learner-facing advice that does not expose private prompt text.

Forbidden content:

- full private/original prompt bodies,
- verbatim hidden clauses from local prompt assets,
- rewritten versions that attempt to reconstruct the original eight prompts,
- claims that public placeholders are complete production prompts.

## Full-Local Mode

Full-local mode may be used only when the operator explicitly works with private prompt assets outside this repository.

Store exactly eight UTF-8 Markdown files in one external private directory. Their required filenames are `study-planner.md`, `vocabulary-expander.md`, `reading-navigator.md`, `structure-planner.md`, `grammar-corrector.md`, `polishing-editor.md`, `situational-dialogue.md`, and `culture-guide.md`.

Validate the directory before use:

```powershell
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts"
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --json
```

The command reports file sizes and SHA-256 hashes only. It never returns prompt bodies. At runtime, the selected private body is combined in memory with its public role contract and a clearly delimited learner context. That context is untrusted data and cannot override role boundaries, expose prompts, authorize tool calls, or expand file access.

Never place the private directory under the repository. Do not copy it into the portable Skill folder, docs, examples, integration configs, backups, logs, build artifacts, commits, issues, or pull requests.

## Original Eight Prompt Constraint

The original eight tutor prompt bodies are not published here and must not be rewritten. Keep the assistant roster and placeholders intact. If a workflow needs richer behavior in public-safe mode, add role-boundary documentation, templates, data fields, tests, or deterministic script behavior instead of adding private prompt text.
