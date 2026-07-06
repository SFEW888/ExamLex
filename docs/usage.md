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

1. Use `/english-exam-ai-tutor` for intake and diagnosis.
2. Use `/learning-planner` to generate the stage plan and daily tasks.
3. Use shortcut Skills for practice: vocabulary, reading, grammar, polishing, dialogue, or culture.
4. Let the Agent record practice, tag errors, summarize repeated issues, update ability, and revise the next plan with the automation scripts.
5. Keep writing drafts versioned and treat writing scores as deterministic rubric estimates, not official exam scores.

## Internal CLI

The Agent may run the internal CLI after the Skill has interpreted the task. Humans can run it for debugging:

```powershell
python -m skills.english_exam_ai_tutor --help
python -m skills.english_exam_ai_tutor validate-profile --profile examples\sample-learner-profile.yaml
python -m skills.english_exam_ai_tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --output daily-plan.json
```

Generated local files such as plans, ledgers, `.env`, and private prompt assets should stay untracked.
