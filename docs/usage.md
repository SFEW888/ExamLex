# Usage

This workflow assumes PowerShell from the repository root.

## 1. Validate The Repository

```powershell
python scripts\validate_repo.py --root . --json
```

## 2. Validate A Learner Profile

Start from `examples\sample-learner-profile.yaml` or `skills\english-exam-ai-tutor\assets\templates\learner-profile.json`.

```powershell
python skills\english-exam-ai-tutor\scripts\validate_profile.py --profile examples\sample-learner-profile.yaml
```

Fix validation errors before planning.

## 3. Generate A Daily Plan

```powershell
python skills\english-exam-ai-tutor\scripts\generate_daily_plan.py --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --output daily-plan.json
```

If no error summary exists yet, omit `--errors` for the first plan.

After `summarize_errors.py` creates `error-summary.json`, feed it into the next plan:

```powershell
python skills\english-exam-ai-tutor\scripts\generate_daily_plan.py --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --errors error-summary.json --output daily-plan.next.json
```

## 4. Daily Loop

Record each practice result with explicit counts and tags:

```powershell
python skills\english-exam-ai-tutor\scripts\record_practice.py --ledger practice-ledger.json --date 2026-07-05 --exam-type CET6 --module reading --task-id reading-long-sentence-01 --duration-minutes 25 --total-items 12 --correct-items 8 --error-tags READING_LONG_SENTENCE_FAIL READING_PARAPHRASE_FAIL --print-record
```

Summarize the ledger:

```powershell
python skills\english-exam-ai-tutor\scripts\summarize_errors.py --ledger practice-ledger.json --output error-summary.json
```

Update ability state:

```powershell
python skills\english-exam-ai-tutor\scripts\update_ability_profile.py --ability ability-profile.json --ledger practice-ledger.json --output ability-profile.next.json
```

Generate tomorrow's plan from updated evidence:

```powershell
python skills\english-exam-ai-tutor\scripts\generate_daily_plan.py --profile learner-profile.json --ability ability-profile.next.json --errors error-summary.json --output daily-plan.next.json
```

## 5. Writing Loop

Append writing versions instead of overwriting drafts:

```powershell
python skills\english-exam-ai-tutor\scripts\manage_writing_versions.py --file writing-versions.json --writing-id essay-001 --text "First draft text"
```

Score a draft with a deterministic rubric estimate:

```powershell
python skills\english-exam-ai-tutor\scripts\score_writing_rubric.py --text-file essay.txt --exam-type POSTGRADUATE_ENGLISH --output writing-score.json
```

Use the score to guide revision. Do not present it as official exam scoring.

## 6. Weekly Review

At the end of a week, summarize errors and trends:

```powershell
python skills\english-exam-ai-tutor\scripts\summarize_errors.py --ledger practice-ledger.json --output weekly-error-summary.json
python skills\english-exam-ai-tutor\scripts\analyze_trends.py --ledger practice-ledger.json --history ability-history.json --output weekly-trends.json
```

Use `skills\english-exam-ai-tutor\assets\templates\weekly-review.md` to write the learner-facing review. Anchor comments in completed tasks, repeated error tags, and ability changes.
