---
name: examlex
description: Use when an agent needs an English exam AI tutor for CET-4, CET-6, TEM-4, TEM-8, or postgraduate English preparation, including study planning, vocabulary estimation, spaced repetition review, reading, writing structure, grammar correction, polishing, scenario dialogue, timed practice, progress visualization, and cultural context.
---

# ExamLex

ExamLex is published at [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex). Clone the repository and use `install.ps1` or `install.sh` to install the main Skill and shortcut Skills.

For the complete public-safe workflow, use the canonical Skill instructions at `skills/examlex/SKILL.md`. Treat the eight shortcut Skill folders under `skills/` as optional routers for shorter user-facing calls:

- `learning-planner`
- `vocabulary-builder`
- `reading-navigator`
- `structure-planner`
- `grammar-corrector`
- `polish-wizard`
- `scenario-dialog`
- `culture-guide`

When this root Skill is installed alone, route all exam-prep requests through the canonical `examlex` workflow and read only the relevant reference files under `skills/examlex/references/`.

Keep public-safe mode by default. Do not publish, infer, rewrite, or reconstruct private tutor prompt bodies.
