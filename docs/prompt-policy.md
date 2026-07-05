# Prompt Policy

This repository is public-safe by default.

## Public-Safe Mode

Use public-safe mode for GitHub, examples, docs, demos, issue discussions, pull requests, generated release packages, and any artifact that may leave the local private environment.

Allowed content:

- eight assistant names, role boundaries, and high-level descriptions,
- placeholders such as `[PRIVATE_PROMPT_PLACEHOLDER: study-planner]`,
- script interfaces, templates, schemas, workflows, and error taxonomy,
- learner-facing advice that does not expose private prompt text.

Forbidden content:

- full private/original prompt bodies,
- verbatim hidden clauses from local prompt assets,
- rewritten versions that attempt to reconstruct the original eight prompts,
- claims that public placeholders are complete production prompts.

## Full-Local Mode

Full-local mode may be used only when the operator explicitly works with private prompt assets outside this repository.

In full-local mode, an agent may select the correct local assistant prompt and combine its output with script-generated evidence. It must not copy those private prompts into the portable Skill folder, docs, examples, integration configs, commits, issues, or pull requests.

## Original Eight Prompt Constraint

The original eight tutor prompt bodies are not published here and must not be rewritten. Keep the assistant roster and placeholders intact. If a workflow needs richer behavior in public-safe mode, add role-boundary documentation, templates, data fields, tests, or deterministic script behavior instead of adding private prompt text.
