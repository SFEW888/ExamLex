# Design Rationale

ExamLex is intentionally split into a portable Skill and small deterministic scripts.

The Skill gives agents the tutoring frame: supported exams, learner levels, target bands, the eight assistant roles, prompt modes, references, and templates. The scripts keep the measurable parts stable: profile validation, daily planning, practice recording, error summaries, ability updates, trend analysis, writing versioning, and writing rubric estimates.

## Public-Safe Release

This repository is suitable for public GitHub release because it publishes role boundaries and placeholders, not private prompt bodies. Public-safe docs can explain what each assistant does and how to route tasks, but they must not reproduce or reconstruct the original eight tutor prompts.

Full-local mode is a local operating mode only. It can select private prompt assets that live outside this repository, but those assets must stay out of shared files.

## Deterministic Automation

The scripts deliberately avoid probabilistic planning or scoring logic. This makes learner state auditable:

- `validate_profile.py` rejects unsupported exam tracks, bands, and required-field gaps.
- `generate_daily_plan.py` solves a constrained daily plan from time budget, target exam, ability state, and error evidence.
- `record_practice.py` stores repeatable ledger entries with explicit `total_items` and `correct_items`.
- `summarize_errors.py` groups error tags by tag, module, and dimension.
- `update_ability_profile.py` converts practice evidence into ability changes.
- `score_writing_rubric.py` gives a deterministic rubric estimate for revision guidance, not official scoring.

## Planning Model

Daily planning is constraint solving rather than generic advice. The planner respects:

- learner exam type and target band,
- foundation level,
- daily time budget,
- low-status ability nodes,
- repeated or high-impact error tags,
- module coverage across vocabulary, listening, reading, translation, and writing.

The agent may adapt learner-facing wording, but the planned modules, minutes, focus, and reasons should remain consistent with script output unless the learner changes constraints.
