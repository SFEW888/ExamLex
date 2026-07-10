---
name: examlex
description: Use when supporting CET-4, CET-6, TEM-4, TEM-8, or postgraduate English prep, including learner diagnosis, daily planning, error attribution, vocabulary estimation, spaced repetition review, timed practice, vocabulary/listening/reading/translation/writing/dictation/proofreading practice, writing scoring/versioning, multi-source continuous learning (extract exam strategies from books/videos/people/conversations via embedded distillation methodologies), progress visualization, and choosing public-safe or full-local prompt modes.
---

# ExamLex

Use this Skill to operate the portable English exam tutoring workspace for CET-4, CET-6, TEM-4, TEM-8, and postgraduate English learners. Keep the loop evidence-based: validate the learner profile, estimate vocabulary, generate a constrained plan with vocabulary pool assignments, record practice with error tags and timed metrics, summarize errors with spaced-repetition review urgency, update the ability profile, visualize progress, and revise the next plan from observed data.

## Mode Selection

- Public-safe mode: use only placeholders and public descriptions for the eight tutor assistants. Do not publish full private/original prompts.
- Full-local mode: use the user's local private prompt assets if they exist outside this public-safe release. Do not rewrite the original eight tutor prompts while operating in this mode.
- When unsure, default to public-safe mode and ask before using any private local prompt source.

Read [references/prompt-modes.md](references/prompt-modes.md) before publishing, packaging, or syncing the Skill outside the local machine. Read [references/assistant-roster.md](references/assistant-roster.md) when selecting tutor roles.

## User-Facing Invocation

The user invokes this Skill from an Agent interface:

- Codex: `/examlex`
- Claude Code: `/examlex`

Shortcut Skills may also be installed for direct scenario calls: `learning-planner`, `vocabulary-builder`, `reading-navigator`, `structure-planner`, `grammar-corrector`, `polish-wizard`, `scenario-dialog`, and `culture-guide`.

Do not ask the user to run Python commands unless they explicitly ask for developer or CLI debugging instructions. Python scripts are internal automation helpers that the Agent may run after interpreting the learner's request.

## Operating Workflow

After this Skill is invoked, parse the user's natural-language request, choose the relevant tutor role, and use scripts from the Skill directory only when deterministic state changes or validation are needed.

0. Estimate vocabulary (optional first step):
   `python skills/examlex/scripts/estimate_vocabulary.py --interactive --output vocab-estimate.json`
   Or batch mode: `python skills/examlex/scripts/estimate_vocabulary.py --wordlist answers.json --output result.json`

1. Validate intake:
   `python skills/examlex/scripts/validate_profile.py --profile learner-profile.json`
   Supports CET4, CET6, POSTGRADUATE_ENGLISH, TEM4, TEM8.

2. Generate the daily plan:
   `python skills/examlex/scripts/generate_daily_plan.py --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json`
   Optionally pass `--strategies strategy-library.json` to attach relevant user-ingested exam methods to planned modules.
   Optionally pass `--vocab-pool skills/examlex/assets/data/vocabulary/cet4-core-2000.json` for vocabulary assignments.
   The plan automatically includes spaced-repetition review tasks for error tags with high review urgency.

3. Record practice and tag errors (supports timed practice):
   `python skills/examlex/scripts/tag_error.py --module writing --text "..."`
   `python skills/examlex/scripts/record_practice.py --ledger practice-ledger.json --date 2026-07-05 --exam-type CET4 --module reading --task-id timed-reading-001 --duration-minutes 40 --total-items 20 --correct-items 14 --timed --time-limit-minutes 35 --overtime-items 3 --overtime-correct 1 --error-tags READING_SPEED_LOW`

4. Summarize errors (includes spaced-repetition review urgency and speed analysis):
   `python skills/examlex/scripts/summarize_errors.py --ledger practice-ledger.json --output error-summary.json --days 30`

5. Update ability and analyze trends:
   `python skills/examlex/scripts/update_ability_profile.py --ability ability-profile.json --ledger practice-ledger.json`
   `python skills/examlex/scripts/analyze_trends.py --ledger practice-ledger.json --history ability-history.json --output trend-analysis.json`

6. Manage writing drafts, score with rubric, and anchor against model essays:
   `python skills/examlex/scripts/manage_writing_versions.py --file writing-versions.json --writing-id essay-001 --text "..."`
   `python skills/examlex/scripts/score_writing_rubric.py --text-file essay.txt --exam-type CET4 --output writing-score.json`
   Optionally pass `--reference-samples skills/examlex/assets/data/sample-essays/` to anchor scoring against model essays.

7. Visualize progress (generates standalone HTML report with SVG charts):
   `python skills/examlex/scripts/visualize.py --ability-history ability-history.json --ledger practice-ledger.json --error-summary error-summary.json --output progress-report.html --days 30`

## Multi-Source Continuous Learning

Extract exam strategies from any source — text files, books, videos, people, conversations — and write them into `strategy-library.json`. All five distillation paths are built-in (`direct`, `book`, `video`, `person`, `manual`): no external skills needed. See [references/multi-source-distillation.md](references/multi-source-distillation.md) for the complete methodology reference.

### Pipeline Overview

Each distillation follows a 5-stage pipeline orchestrated by the Agent:

1. **Extract**: `examlex extract --input <url|file|name>` — downloads and extracts raw materials.
2. **Distill**: Agent follows the methodology guide (`prompts/ria.py` for video, `prompts/cognitive.py` for people) to produce structured strategies → `distilled.json`.
3. **Validate**: `examlex validate --artifacts-dir <path>` — runs format checks + Darwin 6-dimension structure scoring (59 pts).
4. **Evaluate**: Agent runs test prompts to score effectiveness (35 pts) → `evaluation.json`.
5. **Commit**: `examlex commit --artifacts-dir <path> --library strategy-library.json` — ratchet check + atomic write.

Total Darwin score < 70 triggers automatic hill-climb optimization (max 3 rounds).

### 7a. Direct text ingestion — `distillation-method direct`
For plain-text strategy notes:
```bash
examlex extract --input <note> --type text
# → Agent reads methodology guide → distill
examlex validate --artifacts-dir <path>
examlex commit --artifacts-dir <path> --library strategy-library.json
```

### 7b. Book / PDF — built-in `book`
For exam prep books (PDF/EPUB/DOCX/TXT/HTML):
```bash
examlex extract --input <book-file> --type book
# Extracts full text + chapter structure + glossary
# → Agent follows prompts/ria.py for RIA-TV++ distillation
examlex validate --artifacts-dir <path>
examlex commit --artifacts-dir <path> --library strategy-library.json
```
Methodology: scan for frameworks → triple-verify → RIA++: R(原文≤150字)/I(自述)/A1(案例)/A2(触发)/E(步骤)/B(边界).

### 7c. Video / Podcast — built-in `video`
For B站/YouTube URLs or subtitle files:
```bash
examlex extract --input <video-url> --type video
# yt-dlp download → ffmpeg audio → SenseVoiceSmall/whisper ASR
# → Agent follows prompts/ria.py for RIA-TV++ distillation
examlex validate --artifacts-dir <path>
examlex commit --artifacts-dir <path> --library strategy-library.json
```
Requires: yt-dlp + ffmpeg (run `examlex check-deps`).

### 7d. Person / Teacher — built-in `person`
For distilling a teacher's methodology:
```bash
examlex extract --input <person-name> --type person
# → Agent follows prompts/cognitive.py for 5-layer cognitive extraction
# → 6 parallel research agents → triple verification
examlex validate --artifacts-dir <path>
examlex commit --artifacts-dir <path> --library strategy-library.json
```

### 7e. Conversation / manual notes — `distillation-method manual`
```bash
examlex extract --input <notes-file> --type text
examlex validate --artifacts-dir <path>
examlex commit --artifacts-dir <path> --library strategy-library.json
```

### 7f. Darwin 评分与审批门禁
- Structure (59 pts): auto-scored by `examlex validate` via `validators/darwin_structure.py`
- Effectiveness (35 pts): Agent-evaluated via test prompts (see `references/darwin-rubric.md`)
- Meta-skill (6 pts): anti-pattern blacklist check
- Score < 70 → automatic hill-climb optimization (max 3 rounds)
- Check deps: `examlex check-deps`

## Constraints

- Do not rewrite the original eight tutor prompts in full-local mode.
- Public release must use public-safe prompt placeholders and must not include full private/original prompts.
- Writing score output is a deterministic rubric estimate, not official exam scoring.
- Practice records must use `total_items` and `correct_items`; do not use `total` or `correct`.
- Timed practice records must include `timed: true`; `time_limit_minutes` is auto-looked-up from `EXAM_TIME_LIMITS` if omitted.
- Keep data JSON-compatible even when a template is authored as YAML or Markdown.
- Keep generated learner-facing advice tied to the learner's exam type target bands (CET 425-600+, Postgraduate 50-90+, TEM 60-80+) and foundation level.
- Vocabulary estimation uses Yes/No sampling with false-alarm correction; results are estimates, not official measurements.
- Distillation methodologies (structural, RIA++, cognitive) are executed by the Agent internally — the user never needs to install external tools.

## References and Templates

- [references/assistant-roster.md](references/assistant-roster.md): eight assistants, role boundaries, public-safe placeholders.
- [references/error-taxonomy.md](references/error-taxonomy.md): module/dimension tree and valid error tags.
- [references/exam-profiles.md](references/exam-profiles.md): supported exam types, foundation levels, target bands.
- [references/prompt-modes.md](references/prompt-modes.md): public-safe versus full-local publishing rules.
- [references/workflow.md](references/workflow.md): diagnosis-to-next-plan loop.
- [references/data-model.md](references/data-model.md): learner profile, ability profile, practice ledger, writing versions, summaries, strategy library.
- [references/multi-source-distillation.md](references/multi-source-distillation.md): complete distillation methodology reference (structural / RIA++ / cognitive extraction).
- `assets/templates/learner-profile.json` and `assets/templates/learner-profile.yaml`: learner intake starter.
- `assets/templates/ability-profile.yaml`: ability profile starter.
- `assets/templates/exercise-record.json` and `assets/templates/exercise-record.yaml`: practice record starter.
- `assets/templates/error-log.yaml`: error capture starter.
- `assets/templates/daily-plan.md` and `assets/templates/daily-task-query.md`: plan/task presentation starters.
- `assets/templates/writing-version-record.yaml`: writing version metadata starter.
- `assets/templates/weekly-review.md` and `assets/templates/initial-diagnosis.md`: learner-facing review starters.
- `assets/data/vocabulary/`: built-in vocabulary pools (CET4/6/Postgraduate/TEM4/TEM8) with frequency-ranked entries.
- `assets/data/vocab-test-words.json`: Yes/No sampling word list with 6 frequency bands and non-word traps for vocabulary estimation.
- `assets/data/common-errors/`: common error patterns for Chinese learners (writing/translation/listening/reading/vocabulary).
- `assets/data/sample-essays/`: model essays with rubric scores and annotations for scoring anchor reference.
- `assets/schemas/`: JSON Schema files for vocab-entry, vocab-estimate-result, error-pattern, strategy-library, and sample-essay.
- [references/darwin-rubric.md](references/darwin-rubric.md): Darwin 6-dimension strategy quality scoring rubric (59 pts).
- `scripts/vocab_generator.py`: generate vocabulary pool JSON files from embedded word database.
- `scripts/estimate_vocabulary.py`: Yes/No sampling vocabulary size estimation engine.
- `scripts/visualize.py`: generate standalone HTML progress reports with inline SVG charts.
