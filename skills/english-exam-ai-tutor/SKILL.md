---
name: english-exam-ai-tutor
description: Use when supporting CET-4, CET-6, or postgraduate English prep, including learner diagnosis, daily planning, error attribution, vocabulary/listening/reading/translation/writing practice, writing scoring/versioning, and choosing public-safe or full-local prompt modes.
---

# English Exam AI Tutor

Use this Skill to operate the portable English exam tutoring workspace for CET-4, CET-6, and postgraduate English learners. Keep the loop evidence-based: validate the learner profile, generate a constrained plan, record practice with error tags, update the ability profile, and revise the next plan from observed data.

## Mode Selection

- Public-safe mode: use only placeholders and public descriptions for the eight tutor assistants. Do not publish full private/original prompts.
- Full-local mode: use the user's local private prompt assets if they exist outside this public-safe release. Do not rewrite the original eight tutor prompts while operating in this mode.
- When unsure, default to public-safe mode and ask before using any private local prompt source.

Read [references/prompt-modes.md](references/prompt-modes.md) before publishing, packaging, or syncing the Skill outside the local machine. Read [references/assistant-roster.md](references/assistant-roster.md) when selecting tutor roles.

## Operating Workflow

Run scripts from the Skill directory or reference them by path from a project root.

1. Validate intake:
   `python skills/english-exam-ai-tutor/scripts/validate_profile.py --profile learner-profile.json`
2. Generate the daily plan:
   `python skills/english-exam-ai-tutor/scripts/generate_daily_plan.py --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json`
3. Record practice and tag errors:
   `python skills/english-exam-ai-tutor/scripts/tag_error.py --module writing --text "..."`
   `python skills/english-exam-ai-tutor/scripts/record_practice.py --ledger practice-ledger.json --record-json "{\"total_items\":10,\"correct_items\":7,\"error_tags\":[\"WRITING_ARTICLE_OMISSION\"]}"`
4. Summarize errors:
   `python skills/english-exam-ai-tutor/scripts/summarize_errors.py --ledger practice-ledger.json --output error-summary.json`
5. Update ability and analyze trends:
   `python skills/english-exam-ai-tutor/scripts/update_ability_profile.py --ability ability-profile.json --ledger practice-ledger.json`
   `python skills/english-exam-ai-tutor/scripts/analyze_trends.py --ledger practice-ledger.json --history ability-history.json --output trend-analysis.json`
6. Manage writing drafts and estimate writing quality:
   `python skills/english-exam-ai-tutor/scripts/manage_writing_versions.py --file writing-versions.json --writing-id essay-001 --text "..."`
   `python skills/english-exam-ai-tutor/scripts/score_writing_rubric.py --text-file essay.txt --exam-type CET4 --output writing-score.json`

Read [references/workflow.md](references/workflow.md) for the learning loop and [references/data-model.md](references/data-model.md) for file shapes.

## Constraints

- Do not rewrite the original eight tutor prompts in full-local mode.
- Public release must use public-safe prompt placeholders and must not include full private/original prompts.
- Writing score output is a deterministic rubric estimate, not official exam scoring.
- Practice records must use `total_items` and `correct_items`; do not use `total` or `correct`.
- Keep data JSON-compatible even when a template is authored as YAML or Markdown.
- Keep generated learner-facing advice tied to CET-4, CET-6, or postgraduate English target bands and the learner's diagnosed foundation level.

## References and Templates

- [references/assistant-roster.md](references/assistant-roster.md): eight assistants, role boundaries, public-safe placeholders.
- [references/error-taxonomy.md](references/error-taxonomy.md): module/dimension tree and valid error tags.
- [references/exam-profiles.md](references/exam-profiles.md): supported exam types, foundation levels, target bands.
- [references/prompt-modes.md](references/prompt-modes.md): public-safe versus full-local publishing rules.
- [references/workflow.md](references/workflow.md): diagnosis-to-next-plan loop.
- [references/data-model.md](references/data-model.md): learner profile, ability profile, practice ledger, writing versions, summaries.
- `assets/templates/learner-profile.json` and `assets/templates/learner-profile.yaml`: learner intake starter.
- `assets/templates/ability-profile.yaml`: ability profile starter.
- `assets/templates/exercise-record.json` and `assets/templates/exercise-record.yaml`: practice record starter.
- `assets/templates/error-log.yaml`: error capture starter.
- `assets/templates/daily-plan.md` and `assets/templates/daily-task-query.md`: plan/task presentation starters.
- `assets/templates/writing-version-record.yaml`: writing version metadata starter.
- `assets/templates/weekly-review.md` and `assets/templates/initial-diagnosis.md`: learner-facing review starters.
