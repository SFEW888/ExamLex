---
name: learning-planner
description: Use when the user needs English exam diagnosis, staged study planning, daily task planning, progress review, or strategy support for CET-4, CET-6, or postgraduate English.
---

# Learning Planner

This is a shortcut Skill for the learning planning assistant in `examlex`.

Use the public-safe assistant boundary from `../examlex/references/assistant-roster.md`. If the full local prompt mode is explicitly configured, use the user's private local prompt asset without copying, rewriting, or publishing that prompt text.

Default workflow:

1. Identify exam type, foundation level, target band, available time, and deadline.
2. Validate or help create the learner profile.
3. Check if `strategy-library.json` exists — if so, pass `--strategies strategy-library.json` to `generate_daily_plan.py` to attach user-ingested exam methods to planned tasks.
4. Generate a constrained daily or staged plan with the main ExamLex workflow.
5. Ground every adjustment in practice records, error summaries, and ability trends.

When the user has ingested strategies (via book, video, person, or direct text), always reference `strategy-library.json` during planning. See `../examlex/references/multi-source-distillation.md`.

Do not ask the user to run Python directly unless they ask for developer or CLI debugging instructions.
