# Usage

Use this project through an Agent Skill first. `SKILL.md` is not a terminal program, and `python -m skills.english_exam_ai_tutor ...` is only the internal automation CLI for development or debugging.

## Agent Skill Calls

Use slash calls in Agent chat:

```text
/english-exam-ai-tutor Create today's CET4 550+ plan from my learner profile, ability profile, and latest error summary.
/learning-planner Build a 30-day plan for a weak-foundation learner targeting CET4 550+.
/grammar-corrector Check this paragraph and return a correction report.
/reading-navigator Break down this long sentence and identify the evidence for the answer.
```

## Shortcut Skills

| Scenario | Slash call |
| --- | --- |
| Full tutor workflow | `/english-exam-ai-tutor` |
| Learning plan | `/learning-planner` |
| Vocabulary | `/vocabulary-builder` |
| Reading | `/reading-navigator` |
| Writing structure | `/structure-planner` |
| Grammar correction | `/grammar-corrector` |
| Polishing | `/polish-wizard` |
| Scenario dialogue | `/scenario-dialog` |
| Cultural context | `/culture-guide` |

## Learning Loop

1. Use `/english-exam-ai-tutor` for intake and diagnosis. Supports CET4, CET6, TEM4, TEM8, and postgraduate English.
2. Optionally estimate vocabulary: `tutor vocab --interactive` (Yes/No sampling with false-alarm correction).
3. Use `/learning-planner` to generate the stage plan and daily tasks with vocabulary pool assignments and spaced repetition review.
4. Use shortcut Skills for practice: vocabulary, reading, grammar, polishing, dialogue, or culture.
5. Let the Agent record practice (with optional timed mode and overtime tracking), tag errors, summarize repeated issues with review urgency, update ability, and revise the next plan with the automation scripts.
6. Keep writing drafts versioned and anchor scoring against model essay references.
7. Visualize progress: `tutor report --ability-history <path> --ledger <path>` generates a standalone HTML report with SVG charts.

## Internal CLI

The Agent may run the internal CLI after the Skill has interpreted the task. Humans can run it for debugging:

```powershell
# Core workflow
python -m skills.english_exam_ai_tutor validate-profile --profile learner-profile.json
python -m skills.english_exam_ai_tutor daily-plan --profile learner-profile.json --ability ability-profile.json --vocab-pool vocab.json --output daily-plan.json
python -m skills.english_exam_ai_tutor record-practice --ledger practice-ledger.json --date 2026-07-06 --exam-type CET4 --module reading --task-id t1 --duration-minutes 30 --total-items 20 --correct-items 14 --timed --time-limit-minutes 35
python -m skills.english_exam_ai_tutor summarize-errors --ledger practice-ledger.json --output error-summary.json --days 30
python -m skills.english_exam_ai_tutor update-ability --ability ability-profile.json --ledger practice-ledger.json
python -m skills.english_exam_ai_tutor analyze-trends --ledger practice-ledger.json --history ability-history.json

# Vocabulary estimation
python -m skills.english_exam_ai_tutor vocab-estimate --interactive --output vocab-estimate.json
python -m skills.english_exam_ai_tutor vocab-estimate --wordlist answers.json --output result.json

# Progress visualization
python -m skills.english_exam_ai_tutor visualize --ability-history ability-history.json --ledger practice-ledger.json --output report.html --days 30

# Data management
python -m skills.english_exam_ai_tutor backup --data-dir ./data --output backup.tar.gz
python -m skills.english_exam_ai_tutor backup --list backup.tar.gz
python -m skills.english_exam_ai_tutor restore --data-dir ./data --input backup.tar.gz
```

Generated local files such as plans, ledgers, `.env`, and private prompt assets should stay untracked.
