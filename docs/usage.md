# Usage

This workflow assumes PowerShell from the repository root.

## 1. Validate The Repository

```powershell
python scripts\validate_repo.py --root . --json
```

## 2. Validate A Learner Profile

Start from `examples\sample-learner-profile.yaml` or `skills\english-exam-ai-tutor\assets\templates\learner-profile.json`.

```powershell
python -m skills.english_exam_ai_tutor validate-profile --profile examples\sample-learner-profile.yaml
```

Fix validation errors before planning.

## 3. Generate A Daily Plan

```powershell
python -m skills.english_exam_ai_tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --output daily-plan.json
```

If no error summary exists yet, omit `--errors` for the first plan.

After `summarize_errors.py` creates `error-summary.json`, feed it into the next plan:

```powershell
python -m skills.english_exam_ai_tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --errors error-summary.json --output daily-plan.next.json
```

## 4. Daily Loop

Record each practice result with explicit counts and tags:

```powershell
python -m skills.english_exam_ai_tutor record-practice --ledger practice-ledger.json --date 2026-07-05 --exam-type CET6 --module reading --task-id reading-long-sentence-01 --duration-minutes 25 --total-items 12 --correct-items 8 --error-tags READING_LONG_SENTENCE_FAIL READING_PARAPHRASE_FAIL --print-record
```

Summarize the ledger:

```powershell
python -m skills.english_exam_ai_tutor summarize-errors --ledger practice-ledger.json --output error-summary.json
```

Update ability state:

```powershell
python -m skills.english_exam_ai_tutor update-ability --ability examples\sample-ability-profile.yaml --ledger practice-ledger.json --output ability-profile.next.json
```

Generate tomorrow's plan from updated evidence:

```powershell
python -m skills.english_exam_ai_tutor daily-plan --profile examples\sample-learner-profile.yaml --ability ability-profile.next.json --errors error-summary.json --output daily-plan.next.json
```

## 5. Writing Loop

Append writing versions instead of overwriting drafts:

```powershell
python -m skills.english_exam_ai_tutor writing-version --file writing-versions.json --writing-id essay-001 --text "First draft text"
```

Score a draft with a deterministic rubric estimate:

```powershell
python -m skills.english_exam_ai_tutor score-writing --text "I will compare two views and explain why consistent practice matters for postgraduate English preparation." --exam-type POSTGRADUATE_ENGLISH --output writing-score.json
```

Use the score to guide revision. Do not present it as official exam scoring.

## 6. Weekly Review

At the end of a week, summarize errors and trends:

```powershell
python -m skills.english_exam_ai_tutor summarize-errors --ledger practice-ledger.json --output weekly-error-summary.json
python -m skills.english_exam_ai_tutor analyze-trends --ledger practice-ledger.json --history ability-history.json --output weekly-trends.json
```

## Optional Installed Command

For the shortest command names, install the package in editable mode:

```powershell
python -m pip install -e .
english-exam-tutor validate-profile --profile examples\sample-learner-profile.yaml
english-exam-tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --output daily-plan.json
```

Use `skills\english-exam-ai-tutor\assets\templates\weekly-review.md` to write the learner-facing review. Anchor comments in completed tasks, repeated error tags, and ability changes.
