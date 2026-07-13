# Workflow

Use this loop for CET-4, CET-6, TEM-4, TEM-8, and postgraduate English tutoring sessions.

## 0. Knowledge Ingestion (optional, multi-source)

Before diagnosis or at any later stage, add methods through the gated strategy pipeline:

1. Run `python run.py extract --input <url|file|name> --type <video|book|text|person>` to capture source material.
2. Let the Agent apply RIA++, cognitive extraction, or direct ingestion according to source type and write session artifacts.
3. Run `python run.py validate --artifacts-dir <path>` for format and Darwin structure checks.
4. Produce effectiveness evaluation evidence for every candidate strategy.
5. Run `python run.py commit --artifacts-dir <path> --library strategy-library.json` for atomic approval and commit.

Only `approved` strategies may enter a daily plan. If ingestion fails or no strategy library exists, the ordinary learning loop continues normally. See [multi-source-distillation.md](multi-source-distillation.md) for the complete contract.

## 1. Diagnosis

Collect or load a learner profile with:

- `learner_id`
- `exam_type`
- `foundation_level`
- `target_band`
- `daily_time_budget_minutes`
- optional `exam_date`

Validate it with `scripts/validate_profile.py`. If validation fails, fix the profile before planning.

## 2. Plan

Generate a daily plan from the learner profile, ability profile, and optional error summary. Pass `--strategies strategy-library.json` to attach relevant user-ingested exam methods to planned modules:

```bash
python run.py daily-plan --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --strategies strategy-library.json --output daily-plan.json
```

Use the generated tasks as the baseline. Adapt wording for the learner, but keep module, focus, minutes, and reasons consistent unless the user changes constraints.

## 3. Practice

Run or assign tasks across vocabulary, listening, reading, translation, and writing. Record results in the practice ledger with `total_items` and `correct_items`.

Use `tag_error.py` for deterministic first-pass tags when the learner provides error text. Add manual tags from `references/error-taxonomy.md` when the observed issue is clear.

## 4. Error Attribution

Append practice records with `record_practice.py`, then summarize repeated errors:

```bash
python run.py summarize-errors --ledger practice-ledger.json --output error-summary.json
```

Treat the summary as evidence for the next plan, not as a final judgment of the learner.

## 5. Ability Update

Update the ability profile from the ledger:

```bash
python run.py update-ability --ability ability-profile.json --ledger practice-ledger.json
```

Analyze trends when a ledger or ability history has enough points:

```bash
python run.py analyze-trends --ledger practice-ledger.json --history ability-history.json --output trend-analysis.json
```

## 6. Writing Loop

For writing tasks, create versioned drafts with `manage_writing_versions.py`. Score drafts with `score_writing_rubric.py` when the user needs a deterministic rubric estimate.

Always state that this score is a rubric estimate, not official scoring. Use version metadata to compare revisions rather than overwriting previous drafts.

## 7. Next Plan

Feed the updated ability profile and error summary back into `generate_daily_plan.py`. Prioritize repeated high-impact errors and low-status ability nodes while respecting the learner's daily time budget.
