# Workflow

Use this loop for CET-4, CET-6, and postgraduate English tutoring sessions.

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

Generate a daily plan from the learner profile, ability profile, and optional error summary:

```bash
python skills/english-exam-ai-tutor/scripts/generate_daily_plan.py --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json
```

Use the generated tasks as the baseline. Adapt wording for the learner, but keep module, focus, minutes, and reasons consistent unless the user changes constraints.

## 3. Practice

Run or assign tasks across vocabulary, listening, reading, translation, and writing. Record results in the practice ledger with `total_items` and `correct_items`.

Use `tag_error.py` for deterministic first-pass tags when the learner provides error text. Add manual tags from `references/error-taxonomy.md` when the observed issue is clear.

## 4. Error Attribution

Append practice records with `record_practice.py`, then summarize repeated errors:

```bash
python skills/english-exam-ai-tutor/scripts/summarize_errors.py --ledger practice-ledger.json --output error-summary.json
```

Treat the summary as evidence for the next plan, not as a final judgment of the learner.

## 5. Ability Update

Update the ability profile from the ledger:

```bash
python skills/english-exam-ai-tutor/scripts/update_ability_profile.py --ability ability-profile.json --ledger practice-ledger.json
```

Analyze trends when a ledger or ability history has enough points:

```bash
python skills/english-exam-ai-tutor/scripts/analyze_trends.py --ledger practice-ledger.json --history ability-history.json --output trend-analysis.json
```

## 6. Writing Loop

For writing tasks, create versioned drafts with `manage_writing_versions.py`. Score drafts with `score_writing_rubric.py` when the user needs a deterministic rubric estimate.

Always state that this score is a rubric estimate, not official scoring. Use version metadata to compare revisions rather than overwriting previous drafts.

## 7. Next Plan

Feed the updated ability profile and error summary back into `generate_daily_plan.py`. Prioritize repeated high-impact errors and low-status ability nodes while respecting the learner's daily time budget.
