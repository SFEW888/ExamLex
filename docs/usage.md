# Usage

Use this project through an Agent Skill first. `SKILL.md` is not a terminal program, and `python -m examlex ...` is only the internal automation CLI for development or debugging.

## Agent Skill Calls

Use slash calls in Agent chat:

```text
/examlex Create today's CET4 550+ plan from my learner profile, ability profile, and latest error summary.
/learning-planner Build a 30-day plan for a weak-foundation learner targeting CET4 550+.
/grammar-corrector Check this paragraph and return a correction report.
/reading-navigator Break down this long sentence and identify the evidence for the answer.
```

## Shortcut Skills

| Scenario | Slash call |
| --- | --- |
| Full tutor workflow | `/examlex` |
| Learning plan | `/learning-planner` |
| Vocabulary | `/vocabulary-builder` |
| Reading | `/reading-navigator` |
| Writing structure | `/structure-planner` |
| Grammar correction | `/grammar-corrector` |
| Polishing | `/polish-wizard` |
| Scenario dialogue | `/scenario-dialog` |
| Cultural context | `/culture-guide` |

## Learning Loop

1. Use `/examlex` for intake and diagnosis. Supports CET4, CET6, TEM4, TEM8, and postgraduate English.
2. Optionally estimate vocabulary: `examlex vocab --interactive` (Yes/No sampling with false-alarm correction).
3. Use `/learning-planner` to generate the stage plan and daily tasks with vocabulary pool assignments and spaced repetition review.
4. Use shortcut Skills for practice: vocabulary, reading, grammar, polishing, dialogue, or culture.
5. Let the Agent record practice (with optional timed mode and overtime tracking), tag errors, summarize repeated issues with review urgency, update ability, and revise the next plan with the automation scripts.
6. Keep writing drafts versioned and anchor scoring against model essay references.
7. Visualize progress: `examlex report --ability-history <path> --ledger <path>` generates a standalone HTML report with SVG charts.

## Step-by-Step Learning Loop

The following PowerShell examples make the evidence handoff between stages explicit.

### 1. Validate the Repository and Learner Profile

```powershell
python scripts\validate_repo.py --root . --json
python -m examlex validate-profile --profile examples\sample-learner-profile.yaml
```

Fix profile errors before generating a plan.

### 2. Generate the First and Next Daily Plans

```powershell
python -m examlex daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --strategies strategy-library.json --output daily-plan.json
python -m examlex daily-plan --profile examples\sample-learner-profile.yaml --ability ability-profile.next.json --strategies strategy-library.json --errors error-summary.json --output daily-plan.next.json
```

The first plan can omit `--errors`. Later plans should consume the latest error summary and ability evidence.

### 3. Record Practice and Preserve Strategy Revision Evidence

```powershell
python -m examlex record-practice --ledger practice-ledger.json --date 2026-07-05 --exam-type CET6 --module reading --task-id reading-long-sentence-01 --duration-minutes 25 --total-items 12 --correct-items 8 --error-tags READING_LONG_SENTENCE_FAIL READING_PARAPHRASE_FAIL --print-record
python -m examlex record-practice --ledger practice-ledger.json --plan daily-plan.next.json --plan-task-index 0 --date 2026-07-05 --exam-type CET6 --module reading --task-id reading-long-sentence-01 --duration-minutes 25 --total-items 12 --correct-items 8
```

Providing `--plan` and `--plan-task-index` links the practice evidence to the exact approved strategy revision used by that task.

### 4. Attribute Errors and Update Ability

```powershell
python -m examlex summarize-errors --ledger practice-ledger.json --output error-summary.json
python -m examlex update-ability --ability examples\sample-ability-profile.yaml --ledger practice-ledger.json --output ability-profile.next.json
```

### 5. Keep the Writing Loop Versioned

```powershell
python -m examlex writing-version --file writing-versions.json --writing-id essay-001 --text "First draft text"
python -m examlex score-writing --text "I will compare two views and explain why consistent practice matters for postgraduate English preparation." --exam-type POSTGRADUATE_ENGLISH --output writing-score.json
```

The score is revision guidance, not an official exam score. Append new versions instead of overwriting earlier drafts.

### 6. Run the Weekly Review

```powershell
python -m examlex summarize-errors --ledger practice-ledger.json --output weekly-error-summary.json
python -m examlex analyze-trends --ledger practice-ledger.json --history ability-history.json --output weekly-trends.json
```

Use `skills\examlex\assets\templates\weekly-review.md` to write a learner-facing review grounded in completed tasks, recurring error tags, and measured ability changes.

## Internal CLI

The Agent may run the internal CLI after the Skill has interpreted the task. Humans can run it for debugging:

```powershell
# Core workflow
python -m examlex validate-profile --profile learner-profile.json
python -m examlex daily-plan --profile learner-profile.json --ability ability-profile.json --strategies strategy-library.json --vocab-pool vocab.json --output daily-plan.json
python -m examlex record-practice --ledger practice-ledger.json --plan daily-plan.json --plan-task-index 0 --date 2026-07-06 --exam-type CET4 --module reading --task-id t1 --duration-minutes 30 --total-items 20 --correct-items 14
python -m examlex record-practice --ledger practice-ledger.json --date 2026-07-06 --exam-type CET4 --module reading --task-id t1 --duration-minutes 30 --total-items 20 --correct-items 14 --timed --time-limit-minutes 35
python -m examlex summarize-errors --ledger practice-ledger.json --output error-summary.json --days 30
python -m examlex update-ability --ability ability-profile.json --ledger practice-ledger.json
python -m examlex analyze-trends --ledger practice-ledger.json --history ability-history.json

# Vocabulary estimation
python -m examlex vocab-estimate --interactive --output vocab-estimate.json
python -m examlex vocab-estimate --wordlist answers.json --output result.json

# Progress visualization
python -m examlex visualize --ability-history ability-history.json --ledger practice-ledger.json --output report.html --days 30

# Data management
python -m examlex backup --data-dir ./data --output backup.tar.gz
python -m examlex backup --list backup.tar.gz
python -m examlex restore --data-dir ./data --input backup.tar.gz --expected-checksum <checksum_sha256_returned_by_backup>
```

`backup` writes a companion `backup.tar.gz.sha256` file for routine integrity checks. Keep the returned checksum outside the backup directory and supply it to `restore`; this binds restoration to the archive you created rather than a rewritten archive and manifest.

Generated local files such as plans, ledgers, `.env`, and private prompt assets should stay untracked.
