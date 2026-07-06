---
name: english-exam-ai-tutor
description: Use when supporting CET-4, CET-6, or postgraduate English prep, including learner diagnosis, daily planning, error attribution, vocabulary/listening/reading/translation/writing practice, writing scoring/versioning, multi-source continuous learning (extract exam strategies from books/videos/people/conversations via embedded distillation methodologies), and choosing public-safe or full-local prompt modes.
---

# English Exam AI Tutor

Use this Skill to operate the portable English exam tutoring workspace for CET-4, CET-6, and postgraduate English learners. Keep the loop evidence-based: validate the learner profile, generate a constrained plan, record practice with error tags, update the ability profile, and revise the next plan from observed data.

## Mode Selection

- Public-safe mode: use only placeholders and public descriptions for the eight tutor assistants. Do not publish full private/original prompts.
- Full-local mode: use the user's local private prompt assets if they exist outside this public-safe release. Do not rewrite the original eight tutor prompts while operating in this mode.
- When unsure, default to public-safe mode and ask before using any private local prompt source.

Read [references/prompt-modes.md](references/prompt-modes.md) before publishing, packaging, or syncing the Skill outside the local machine. Read [references/assistant-roster.md](references/assistant-roster.md) when selecting tutor roles.

## User-Facing Invocation

The user invokes this Skill from an Agent interface:

- Codex: `/english-exam-ai-tutor`
- Claude Code: `/english-exam-ai-tutor`

Shortcut Skills may also be installed for direct scenario calls: `learning-planner`, `vocabulary-builder`, `reading-navigator`, `structure-planner`, `grammar-corrector`, `polish-wizard`, `scenario-dialog`, and `culture-guide`.

Do not ask the user to run Python commands unless they explicitly ask for developer or CLI debugging instructions. Python scripts are internal automation helpers that the Agent may run after interpreting the learner's request.

## Operating Workflow

After this Skill is invoked, parse the user's natural-language request, choose the relevant tutor role, and use scripts from the Skill directory only when deterministic state changes or validation are needed.

1. Validate intake:
   `python skills/english-exam-ai-tutor/scripts/validate_profile.py --profile learner-profile.json`
2. Generate the daily plan:
   `python skills/english-exam-ai-tutor/scripts/generate_daily_plan.py --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json`
   Optionally pass `--strategies strategy-library.json` to attach relevant user-ingested exam methods to planned modules.
3. Record practice and tag errors:
   `python skills/english-exam-ai-tutor/scripts/tag_error.py --module writing --text "..."`
   `python skills/english-exam-ai-tutor/scripts/record_practice.py --ledger practice-ledger.json --date 2026-07-05 --exam-type CET4 --module writing --task-id writing-article-drill --duration-minutes 20 --total-items 10 --correct-items 7 --error-tags WRITING_ARTICLE_OMISSION`
4. Summarize errors:
   `python skills/english-exam-ai-tutor/scripts/summarize_errors.py --ledger practice-ledger.json --output error-summary.json`
5. Update ability and analyze trends:
   `python skills/english-exam-ai-tutor/scripts/update_ability_profile.py --ability ability-profile.json --ledger practice-ledger.json`
   `python skills/english-exam-ai-tutor/scripts/analyze_trends.py --ledger practice-ledger.json --history ability-history.json --output trend-analysis.json`
6. Manage writing drafts and estimate writing quality:
   `python skills/english-exam-ai-tutor/scripts/manage_writing_versions.py --file writing-versions.json --writing-id essay-001 --text "..."`
   `python skills/english-exam-ai-tutor/scripts/score_writing_rubric.py --text-file essay.txt --exam-type CET4 --output writing-score.json`

## Multi-Source Continuous Learning

Extract exam strategies from any source — text files, books, videos, people, conversations — and write them into `strategy-library.json`. All five distillation paths are built-in (`direct`, `book`, `video`, `person`, `manual`): no external skills needed. See [references/multi-source-distillation.md](references/multi-source-distillation.md) for the complete methodology reference.

### Pipeline Overview

Each distillation follows a 5-stage pipeline orchestrated by the Agent:

1. **Extract**: `tutor extract --input <url|file|name>` — downloads and extracts raw materials.
2. **Distill**: Agent follows the methodology guide (`prompts/ria.py` for video, `prompts/cognitive.py` for people) to produce structured strategies → `distilled.json`.
3. **Validate**: `tutor validate --artifacts-dir <path>` — runs format checks + Darwin 6-dimension structure scoring (59 pts).
4. **Evaluate**: Agent runs test prompts to score effectiveness (35 pts) → `evaluation.json`.
5. **Commit**: `tutor commit --artifacts-dir <path> --library strategy-library.json` — ratchet check + atomic write.

Total Darwin score < 70 triggers automatic hill-climb optimization (max 3 rounds).

### 7a. Direct text ingestion — `distillation-method direct`
For plain-text strategy notes:
```bash
tutor extract --input <note> --type text
# → Agent reads methodology guide → distill
tutor validate --artifacts-dir <path>
tutor commit --artifacts-dir <path> --library strategy-library.json
```

### 7b. Book / PDF — built-in `book`
For exam prep books (PDF/EPUB/DOCX/TXT/HTML):
```bash
tutor extract --input <book-file> --type book
# Extracts full text + chapter structure + glossary
# → Agent follows prompts/ria.py for RIA-TV++ distillation
tutor validate --artifacts-dir <path>
tutor commit --artifacts-dir <path> --library strategy-library.json
```
Methodology: scan for frameworks → triple-verify → RIA++: R(原文≤150字)/I(自述)/A1(案例)/A2(触发)/E(步骤)/B(边界).

### 7c. Video / Podcast — built-in `video`
For B站/YouTube URLs or subtitle files:
```bash
tutor extract --input <video-url> --type video
# yt-dlp download → ffmpeg audio → SenseVoiceSmall/whisper ASR
# → Agent follows prompts/ria.py for RIA-TV++ distillation
tutor validate --artifacts-dir <path>
tutor commit --artifacts-dir <path> --library strategy-library.json
```
Requires: yt-dlp + ffmpeg (run `tutor check-deps`).

### 7d. Person / Teacher — built-in `person`
For distilling a teacher's methodology:
```bash
tutor extract --input <person-name> --type person
# → Agent follows prompts/cognitive.py for 5-layer cognitive extraction
# → 6 parallel research agents → triple verification
tutor validate --artifacts-dir <path>
tutor commit --artifacts-dir <path> --library strategy-library.json
```

### 7e. Conversation / manual notes — `distillation-method manual`
```bash
tutor extract --input <notes-file> --type text
tutor validate --artifacts-dir <path>
tutor commit --artifacts-dir <path> --library strategy-library.json
```

### 7f. Darwin scoring & optimization (automatic)
- Structure (59 pts): auto-scored by `tutor validate` via `validators/darwin_structure.py`
- Effectiveness (35 pts): Agent-evaluated via test prompts (see `references/darwin-rubric.md`)
- Meta-skill (6 pts): anti-pattern blacklist check
- Score < 70 → automatic hill-climb optimization (max 3 rounds)
- Check deps: `tutor check-deps`

## Constraints

- Do not rewrite the original eight tutor prompts in full-local mode.
- Public release must use public-safe prompt placeholders and must not include full private/original prompts.
- Writing score output is a deterministic rubric estimate, not official exam scoring.
- Practice records must use `total_items` and `correct_items`; do not use `total` or `correct`.
- Keep data JSON-compatible even when a template is authored as YAML or Markdown.
- Keep generated learner-facing advice tied to CET-4, CET-6, or postgraduate English target bands and the learner's diagnosed foundation level.
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
