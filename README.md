# ExamLex

[![CI](https://github.com/SFEW888/ExamLex/actions/workflows/ci.yml/badge.svg)](https://github.com/SFEW888/ExamLex/actions/workflows/ci.yml)
[![CodeQL](https://github.com/SFEW888/ExamLex/actions/workflows/codeql.yml/badge.svg)](https://github.com/SFEW888/ExamLex/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10--3.13-blue.svg)](https://www.python.org/)
[![Skills](https://img.shields.io/badge/Skills-9-brightgreen.svg)](#tutor-roles)
[![Platforms](https://img.shields.io/badge/Platforms-4-blue.svg)](#platform-integration)

**Language:** [简体中文](zh-CN/README.md)

> **Status:** ExamLex is open source at [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex) and licensed under MIT.

> CET-4 / CET-6 / TEM-4 / TEM-8 / Postgraduate English — Public-Safe Agent Skills + Deterministic Automation + Continuous Learning
>
> **In one sentence**: Turn the pain of "I don't know where to start with English prep" into a deterministic learning loop — ingest knowledge → diagnose → plan → practice → attribute errors → update → iterate. Every strategy and method you feed in gets absorbed and used in your next study session.

---

## Who This Is For

- University students preparing for CET-4 or CET-6 who need a systematic review plan, not scattered practice.
- Postgraduate English candidates who need evidence-based daily task allocation and weakness tracking.
- Self-learners who want AI-assisted planning for themselves or others.
- Agent Skill developers who want to study the public-safe Skill design pattern.
- Users with exam strategies, technique files, or essay templates who want AI to absorb and apply them automatically.
- Claude Code / Codex / Cursor users who want a one-click installable English prep Skill.

---

## Quick Start

> **Two usage modes — don't mix them up:**
> - **As Agent Skill** (invoke via `/examlex` in chat) → run a local installer from this checkout. Full assistant experience.
> - **Standalone CLI** (command-line only) → install the checkout, then use `examlex`. Scripts only, no Agent Skill registration.

### Requirements

- Python 3.10 / Python 3.11 / Python 3.12 / Python 3.13
- Git
- One of: Claude Code / Codex CLI / Codex App / Cursor

### Feature Dependencies

Core tutoring and direct-text ingestion need no third-party Python package. The following tools are required only when you use the corresponding book or video feature.

| Method | Tools | Install (Windows) | Install (macOS/Linux) |
|--------|-------|-------------------|----------------------|
| `text` | None | — | — |
| `person` | None | — | — |
| `book` (PDF) | [pdftotext (Poppler)](https://poppler.freedesktop.org/) | `winget install poppler` | `brew install poppler` / `apt install poppler-utils` |
| `book` (DOCX) | python-docx | `pip install python-docx` | `pip3 install python-docx` |
| `book` (EPUB DRM) | [Calibre / ebook-convert](https://calibre-ebook.com/download) | `winget install calibre` | `brew install calibre` |
| `video` (download/metadata) | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | `pip install yt-dlp` | `pip3 install yt-dlp` |
| `video` (merge/convert/audio) | [FFmpeg](https://ffmpeg.org/download.html) | `winget install ffmpeg` | `brew install ffmpeg` / `apt install ffmpeg` |
| `video` (ASR) | [Whisper](https://github.com/openai/whisper) or `SILICONFLOW_API_KEY` | `pip install openai-whisper` | `pip3 install openai-whisper` |

`ffmpeg` is the open-source media converter used in two places: `yt-dlp` may need it to merge separate video and audio streams, and ExamLex needs it to extract/convert audio before either local `whisper` or SiliconFlow ASR. A download-only path can sometimes work without `ffmpeg`, but the complete video-to-transcript pipeline cannot.

Run `bin/examlex check-deps` to see what's installed.

### As Agent Skill (recommended)

Clone the public repository, then run the installer for your Agent. It copies `skills\examlex` and the eight shortcut Skills into the selected platform's Skill directory:

```bash
git clone https://github.com/SFEW888/ExamLex.git
cd ExamLex
./install.sh claude    # or: codex, cursor
.\install.ps1 claude   # PowerShell
```

Restart your agent, then invoke:
```text
/examlex Create a 30-day CET4 plan for a weak-foundation learner targeting 550+.
/learning-planner Give me a 30-day plan for a CET4 550+ learner with weak foundation.
/grammar-corrector Check this essay and give me a correction report.
```

### Installation Verification

After restarting the Agent, verify the installed Skill and run a quick request:

```text
/examlex Show the available exam-preparation workflows.
/examlex Create a one-day CET4 study plan for a learner with a weak foundation.
```

Installation locations:

| Platform | Personal skills root | Project-local root |
|----------|----------------------|--------------------|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex CLI / Codex App | `~/.agents/skills/` | `.agents/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

### Standalone CLI (optional)

```bash
python -m pip install "git+https://github.com/SFEW888/ExamLex.git"
```

Then use:
```bash
examlex plan learner-profile.json --ability ability-profile.json
examlex errors practice-ledger.json --days 30
examlex daily-plan --profile learner-profile.json --ability ability-profile.json
```

> The Git installation installs only the CLI script engine. Agent conversation features require cloning the repository and running the Agent installer above. Contributors can use `python -m pip install -e .` in a checkout.

---

## Workflow

ExamLex turns preparation into a repeatable evidence loop:

```text
1. Create or validate learner-profile.json
2. Estimate vocabulary and initialize ability-profile.yaml
3. Generate a daily plan from the profile, evidence, and strategy library
4. Complete timed or untimed practice
5. Record results in exercise-record.json
6. Attribute errors and summarize recurring weaknesses
7. Update the ability profile and analyze trends
8. Review the HTML report and writing-version-record.yaml
9. Feed the new evidence into the next plan
```

At any stage, `examlex ingest` or the extract → validate → commit pipeline can add new methods to `strategy-library.json`. The next planning and tutoring session can then use those methods without replacing the learner's historical evidence.

---

## Features

### Tutor Roles

Eight built-in tutor assistants covering all English prep scenarios. Public repository publishes role boundaries and placeholders; private prompt bodies stay on the user's machine.

| Tutor | Shortcut Skill | Core Responsibility |
|------|:---------:|---------------------|
| Learning Planner | `learning-planner` | Evidence-based plans from profiles, ability scores, and error stats |
| Vocabulary Builder | `vocabulary-builder` | Word meaning, spelling, audio recognition, collocation, exam-context usage |
| Reading Navigator | `reading-navigator` | Reading speed, evidence location, long sentences, inference, paraphrase |
| Structure Planner | `structure-planner` | Essay, paragraph, translation, and answer structure planning |
| Grammar Corrector | `grammar-corrector` | Diagnose and fix articles, tense, agreement, clauses, sentence patterns |
| Polish Wizard | `polish-wizard` | Elevate clarity, expression richness, and exam appropriateness |
| Scenario Dialog | `scenario-dialog` | Create and guide exam-related situational dialogues |
| Culture Guide | `culture-guide` | Explain cultural context, idioms, allusions, and cross-cultural expression |

### Shortcut Skills

| Scenario | Skill | Invocation |
|----------|-------|-----------|
| Full workflow | `examlex` | `/examlex` |
| Study planning | `learning-planner` | `/learning-planner` |
| Vocabulary | `vocabulary-builder` | `/vocabulary-builder` |
| Reading | `reading-navigator` | `/reading-navigator` |
| Writing structure | `structure-planner` | `/structure-planner` |
| Grammar | `grammar-corrector` | `/grammar-corrector` |
| Polish | `polish-wizard` | `/polish-wizard` |
| Dialog | `scenario-dialog` | `/scenario-dialog` |
| Culture | `culture-guide` | `/culture-guide` |

### Automation Scripts

| Stage | Script | Description |
|:-----:|--------|-------------|
| Diagnose | `validate_profile.py` | Validate learner profile: CET4/6/TEM4/8/Postgraduate, foundation level, target band |
| Vocab | `estimate_vocabulary.py` | Yes/No sampling vocabulary size estimation with false-alarm correction |
| Plan | `generate_daily_plan.py` | Constraint-solve daily tasks + vocabulary pool + spaced repetition review |
| Record | `record_practice.py` | Structured practice logging with optional timed mode and overtime tracking |
| Attribute | `tag_error.py` + `summarize_errors.py` | Count errors by tag; adds review urgency (spaced repetition) and speed analysis |
| Update | `update_ability_profile.py` + `analyze_trends.py` | Update ability profile from evidence; analyze trends when enough data |
| Writing | `manage_writing_versions.py` + `score_writing_rubric.py` | Versioned drafts; deterministic rubric estimate with model essay anchoring |
| Review | `visualize.py` | Generate standalone HTML progress report with radar chart, trends, and error table |
| Iterate | Back to Plan | Feed updated ability profile and error summary into next plan |

### Continuous Learning — Multi-Source Distillation

Three knowledge management scripts enable continuous learning:

| Script | Description |
|:------:|-------------|
| `ingest_strategy.py` | Extract structured strategies from uploaded files into the strategy library |
| `list_strategies.py` | List/search strategy library entries by exam, module, or keyword |
| `validate_strategy.py` | Validate strategy library integrity |

New pipeline commands for advanced distillation:
```bash
examlex extract --input <url|file|name> [--type auto|video|book|text|person]
examlex validate --artifacts-dir <path>
examlex commit --artifacts-dir <path> --library strategy-library.json
examlex ops-check    # 13-point operational readiness check
```

Five distillation methods: `direct` (text), `book` (PDF/EPUB/DOCX), `video` (B站/YouTube + ASR), `person` (cognitive extraction), `manual` (conversation notes). Each strategy is automatically scored on a 9-dimension Darwin rubric (100 points). Strategies below 70 enter hill-climb optimization (max 3 rounds).

See [skills/examlex/references/multi-source-distillation.md](skills/examlex/references/multi-source-distillation.md) for full documentation.

---

## Use Cases

| Need | Recommended route | Result |
|------|-------------------|--------|
| Build an exam plan | `learning-planner` + `generate_daily_plan.py` | Constraint-solved daily tasks from foundation, target, and time budget |
| Fix weak vocabulary retention | `vocabulary-builder` + `tag_error.py` | Diagnose meaning, spelling, audio recognition, and context use separately |
| Improve reading | `reading-navigator` + `summarize_errors.py` | Separate evidence for long sentences, location, inference, and paraphrase |
| Develop an essay | `structure-planner` → `grammar-corrector` → `polish-wizard` | Versioned structure, correction, and expression improvement |
| Stop recurring grammar errors | `grammar-corrector` + `update_ability_profile.py` | Tagged evidence feeds the next priority plan |
| Measure progress | `analyze_trends.py` + `examlex report` | Trend evidence plus a local HTML report |
| Practice dialogue and context | `scenario-dialog` + `culture-guide` | Guided situational practice with cultural explanation |
| Run the full loop | `/examlex` | Diagnosis → plan → practice → attribution → update → iteration |
| Preserve personal methods | strategy file → `ingest_strategy.py` | Reuse the method in later plans and tutor guidance |
| Distill a whole book | book extraction → RIA++ → validate → commit | Approved, source-traceable strategies in the library |
| Distill a preparation video | yt-dlp + FFmpeg + ASR → RIA++ | Transcript-backed strategies with validation evidence |
| Distill an expert's methodology | cognitive extraction → validate → commit | Mental models and heuristics with explicit source boundaries |

### Use Case Examples

**From essay structure to a versioned revision**

```text
User: /structure-planner I need to write a CET-4 argumentative essay about environmental protection.

Agent: Plan a three-paragraph structure:
       1. Context, position, and preview of the argument.
       2. Personal actions plus policy-level measures.
       3. Synthesis and a concrete call to action.
       Write V1 from this structure, then preserve it before correction.

User: /polish-wizard Polish my V1 without changing my position.

Agent: Return the revised text, a change list, and the reason for each grammar,
       cohesion, or expression change; append V2 instead of overwriting V1.
```

**Turn a recurring grammar error into tomorrow's plan**

```text
User: /grammar-corrector Check this essay.

Agent: Detect repeated article omissions and agreement errors, then record
       WRITING_ARTICLE_OMISSION and WRITING_LANGUAGE_ACCURACY_FAIL evidence.
       The 30-day summary shows article omission as the highest-frequency tag.

User: Make tomorrow's plan focus on articles.

Agent: Generate a targeted grammar drill, a short writing task with an article
       self-check, and reading annotation practice. Preserve review_urgency and
       the evidence count that caused this priority.
```

---

## Usage

### Quick Examples

```bash
# Diagnose (supports CET4, CET6, TEM4, TEM8, POSTGRADUATE_ENGLISH)
examlex check examples/sample-learner-profile.yaml

# Plan with vocab pool and spaced repetition
examlex plan examples/sample-learner-profile.yaml \
  --ability examples/sample-ability-profile.yaml \
  --vocab-pool skills/examlex/assets/data/vocabulary/cet4-core-2000.json \
  --output daily-plan.json

# Record timed practice
examlex log practice-ledger.json \
  --date 2026-07-06 --exam-type CET4 --module reading \
  --task-id timed-001 --duration-minutes 42 --total-items 20 --correct-items 14 \
  --timed --overtime-items 3 --overtime-correct 1

# Estimate vocabulary
examlex vocab --interactive --output vocab-estimate.json

# Visualize progress
examlex report --ability-history ability-history.json \
  --ledger practice-ledger.json --days 30 --output report.html

# Ingest strategy
examlex ingest reading-strategy.md --library strategy-library.json --exam-types CET4,CET6 --modules reading

# Full pipeline
examlex extract --input ./cet4-guide.pdf --type book
examlex validate --artifacts-dir <path>
examlex commit --artifacts-dir <path> --library strategy-library.json

# Back up local learning data
examlex backup ./local/data
```

### CLI Wrappers

The project provides `bin/examlex` (bash) and `bin/examlex.ps1` (PowerShell) wrappers:

| Command | Equivalent |
|---------|-----------|
| `examlex check <file>` | Validate learner profile |
| `examlex plan <file> --ability ...` | Generate daily plan |
| `examlex errors <file>` | Summarize error tags |
| `examlex trends <file>` | Analyze practice trends |
| `examlex score <essay>` | Estimate writing score |
| `examlex ingest <file>` | Ingest strategy file |
| `examlex extract --input <url>` | Extract from video/book/text |
| `examlex backup <dir>` | Back up local learner and strategy data |
| `examlex report --ability-history ...` | Generate a local HTML progress report |
| `examlex check-deps` | Check tool dependencies |
| `examlex ops-check` | 13-point operational check |

---

## Configuration

### Skill Installation Paths

| Platform | Personal skills root | Project-local root |
|----------|---------------------|-------------------|
| Claude Code | `$HOME\.claude\skills` | `.claude\skills` |
| Codex CLI / Codex App | `$HOME\.agents\skills` | `.agents\skills` |
| Cursor | `$HOME\.cursor\skills` | `.cursor\skills` |

### Environment Variables

ExamLex does not automatically load `.env`. Export these values in your shell, or load `.env.example` with your own environment tool:

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `SILICONFLOW_API_KEY` | No | — | Cloud ASR key (SenseVoiceSmall, alternative to local whisper) |
| `EXAMLEX_PYTHON` | No | `python` | Python interpreter for the local ExamLex wrappers |

---

## Architecture

### Architecture Overview

```
Agent Layer (Claude Code / Codex / Cursor)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Skill Layer (skills/examlex/)            │
│  Tutor roles · Reference docs · Templates · Schemas     │
│  8 shortcut Skills (skills/*/)                           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Script Layer (examlex/)            │
│  extractors/  validators/  optimizers/  prompts/         │
│  validate · daily-plan · record · tag-error · summarize  │
│  update-ability · analyze-trends · writing-version       │
│  score-writing · ops-check · CLI entry point              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Data Layer                                              │
│  Learner profile · Ability profile · Practice ledger     │
│  Error summary · Writing versions · Strategy library     │
│  JSON/YAML compatible · Field-compatible with scripts    │
└─────────────────────────────────────────────────────────┘
```

### Does Continuous Learning Increase Project Size?

No. All five distillation paths are implemented by local project code. Heavy extraction tools are optional and loaded only when their matching workflow needs them; `text` and `person` distillation use only the Python standard library.

### Repository Layout

```
.
├── SKILL.md                         # Root-level Skill entry
├── install.sh / install.ps1         # Cross-platform installer scripts
│
├── skills/examlex/    # Portable public-safe Skill package
│   ├── SKILL.md                     #   Main Skill definition
│   ├── assets/schemas/              #   JSON Schemas
│   ├── assets/templates/            #   YAML/JSON/Markdown templates
│   ├── references/                  #   Reference docs
│   └── scripts/
│       ├── extractors/              #   video.py, book.py, text.py
│       ├── validators/              #   format_checker.py, darwin_structure.py
│       ├── optimizers/              #   ratchet.py
│       ├── prompts/                 #   ria.py, cognitive.py, effect.py, climb.py
│       ├── ops.py                   #   13-point operational check
│       └── ...                      #   11 exam-prep scripts
│
├── examlex/    # Importable Python mirror (tests + CLI)
├── skills/*/                        # 8 shortcut Skills
├── integrations/                    # Platform adapters
├── docs/                            # English docs
├── zh-CN/                           # Chinese docs
├── examples/                        # Sample profiles, ledgers, etc.
├── tests/                           # 333+ tests
├── scripts/                         # Repo validators and installers
├── .github/                         # CI/CD, issue/PR templates
└── pyproject.toml                   # Package metadata
```

### Design Principles

- **Two-track separation:** `skills/examlex/` is the portable Agent-readable Skill package, while `examlex/` is the importable Python mirror used by tests and the CLI. Their script fields and behavior stay synchronized.
- **Determinism first:** planning, validation, attribution, and scoring scripts favor auditable and reproducible rules over probabilistic hidden state.
- **Public safety:** the repository publishes role boundaries, templates, schemas, script interfaces, and placeholders only. The original eight tutor prompt bodies never enter public history.

---

## Data Model

ExamLex stores learner state in JSON-compatible structures. YAML and Markdown templates remain available for convenient editing, but field names must stay compatible with the scripts.

| Data file | Purpose | Template or producer |
|-----------|---------|----------------------|
| **Learner profile** | Exam type, foundation level, target band, and daily time budget | `learner-profile.json` / `.yaml` |
| **Ability profile** | Module ability nodes, status, level, and accuracy evidence | `ability-profile.yaml` |
| **Practice ledger** | Date, module, task, duration, item totals, correct items, and error tags | `exercise-record.json` / `.yaml` |
| **Error summary** | Counts by tag, module, dimension, urgency, and speed evidence | Produced by `summarize_errors.py` |
| **Writing versions** | Versioned V1/V2/V3 drafts, revision notes, and parent links | `writing-version-record.yaml` |
| **Writing score** | Deterministic, explicitly non-official rubric estimate with dimension scores | Produced by `score_writing_rubric.py` |
| **Strategy library** | Structured exam strategies, methods, templates, provenance, and audit evidence | `strategy-library.json`, written by `ingest_strategy.py` or `examlex commit` |

---

## Continuous Learning (Knowledge Ingestion)

Continuous learning accepts more than plain text. A preparation book, long video, podcast transcript, teacher methodology, or conversation note can be distilled into a strategy artifact and later used by planning and tutoring.

### Multi-Source Distillation Architecture

```text
text ─────── direct ──────┐
book ─────── structural ──┤
video ────── RIA++ ───────┼─> extract -> validate -> commit
person ───── cognitive ───┤          │
conversation ─ manual ────┘          v
                                strategy-library.json
                                         │
                         ┌───────────────┼───────────────┐
                         v               v               v
                     daily plan      tutor guidance   search/list
```

### Strategy Library Structure

Each strategy retains enough provenance to be audited:

| Field | Meaning | Example |
|-------|---------|---------|
| `strategy_id` | Stable identifier | `cet4-reading-speed-001` |
| `title` | Human-readable strategy name | Fast CET-4 reading location method |
| `source_type` | Source category | `text`, `book`, `video`, `person`, `conversation` |
| `distillation_method` | Extraction method | `direct`, `structural`, `ria`, `cognitive`, `manual` |
| `source_file` | Local source name | `cet4-reading-notes.md` |
| `source_url` | Original URL, ISBN, or source reference | Video URL or book ISBN |
| `exam_types` | Supported exams | `["CET4", "CET6"]` |
| `modules` | Related modules | `["reading"]` |
| `ability_nodes` | Related ability nodes | `["reading_speed", "evidence_location"]` |
| `content` | Core method | Read the question stem before locating evidence |
| `steps` | Executable steps | `["Scan stems", "Locate in order"]` |

### Examples

**Book:** extract candidate methods from a PDF or EPUB, reject generic or single-source claims, validate the remaining structured artifacts, and commit only approved strategies.

**Video:** use `yt-dlp` for acquisition, FFmpeg for merging/conversion and audio extraction, then local Whisper or SiliconFlow ASR for transcription before RIA++ distillation. A complete video-to-transcript pipeline requires FFmpeg even when a downloader can fetch a single stream without it.

**Person:** collect evidence from multiple independent books, interviews, lessons, and learner reports; distinguish stable mental models from one-off tips; retain source references and confidence evidence.

**Conversation:** turn user-provided notes into explicitly manual strategies without presenting them as independently verified facts.

### Workflow Integration

- With source material: choose the matching extraction method, validate the artifact, commit it, and make it available to later plans and tutor sessions.
- Without source material: all ordinary tutoring and automation continue with an empty or unchanged strategy library.
- At any stage: new knowledge can be added without discarding learner history.
- Across profiles: one strategy library can serve multiple learner profiles.
- For every strategy: retain `source_type`, `distillation_method`, and source provenance.

See [the multi-source distillation reference](skills/examlex/references/multi-source-distillation.md) for gates, audit fields, and failure handling.

---

## Supported Learners

| Exam | ID | Target Bands |
|------|----|-------------|
| CET-4 | `CET4` | `425~499`, `500~550`, `550+`, `600+` |
| CET-6 | `CET6` | `425~499`, `500~550`, `550+`, `600+` |
| Postgraduate English | `POSTGRADUATE_ENGLISH` | `50+`, `70~80`, `80+`, `90+` |
| TEM-4 | `TEM4` | `60~69`, `70~79`, `80+` |
| TEM-8 | `TEM8` | `60~69`, `70~79`, `80+` |

| Foundation level | Identifier | Planning emphasis |
|------------------|------------|-------------------|
| Weak | `基础偏弱` | High-frequency vocabulary, grammar repair, supported slow reading, and short guided output |
| Moderate | `中等基础` | Balanced module practice with evidence-driven weak-point repair |
| Strong | `基础较好` | Timed practice, advanced expression, speed, and high-impact error elimination |

---

## Error Taxonomy

| Module | Example Tags | Dimensions |
|--------|-------------|------------|
| Vocabulary | `VOCAB_MEANING_RECOGNITION_FAIL`, `VOCAB_SPELLING_FAIL` | Meaning, spelling, audio recognition, context use |
| Listening | `LISTENING_KEYWORD_MISS`, `LISTENING_NUMBER_DATE_FAIL` | Keywords, linking/weak forms, numbers/dates, main idea |
| Reading | `READING_LONG_SENTENCE_FAIL`, `READING_PARAPHRASE_FAIL` | Speed, locating, long sentences, inference |
| Translation | `TRANSLATION_GRAMMAR_FAIL`, `TRANSLATION_CHINESE_ENGLISH` | Grammar, word choice, Chinese-English transfer, variety |
| Writing | `WRITING_ARTICLE_OMISSION`, `WRITING_LANGUAGE_ACCURACY_FAIL` | Task response, structure, accuracy, expression richness |

See [skills/examlex/references/error-taxonomy.md](skills/examlex/references/error-taxonomy.md).

---

## Platform Integration

| Platform | Invocation | Shortcut Prefix | Adapter |
|----------|-----------|:--------------:|--------|
| Claude Code | `/examlex` | `/` | [Guide](integrations/claude-code/README.md) |
| Codex CLI | `/examlex` | `/` | [Guide](integrations/codex-cli/README.md) |
| Codex App | `/examlex` | `/` | [Guide](integrations/codex-app/README.md) |
| Cursor | Via Skill directory config | — | [Guide](integrations/cursor/README.md) |

---

## Prompt Modes

| Mode | Use Case | Description |
|------|----------|-------------|
| `public-safe` (default) | GitHub, examples, docs, demos, releases | Role boundaries, placeholders, templates, schemas, script interfaces only |
| `full-local` | User's private machine | May route to private prompt assets outside the repository |

> **Important**: Original eight tutor prompt bodies are not published, rewritten, or reconstructed into any public file. Placeholders like `[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]` are interface markers only.

---

## FAQ

**"Are script outputs official exam scores?"**
No. All script outputs are deterministic calculations or rubric estimates based on your data. `score_writing_rubric.py` is a rubric estimate, not official scoring.

**"Do I have to run CLI commands manually?"**
No. In most cases you speak natural language in your Agent chat. The Agent reads the workflow from SKILL.md and calls scripts as needed. CLI and `examlex` wrappers are mainly for debugging, scripting, and standalone use.

**"Will strategy library data be uploaded to the cloud?"**
No. The strategy library is a local JSON file. Extraction and analysis happen on your machine. If your Agent model runs in the cloud, the text you send follows that provider's standard data terms.

**"Can I share my strategy library?"**
Your own exam strategies — yes. Strategies extracted from copyrighted books — do not publish them publicly. Same rules as handwritten study notes: your notes are yours, but don't republish someone else's book content.

**"Does continuous learning increase the project size?"**
No. All five distillation paths use built-in project code. Heavy extraction tools are optional and loaded only for the workflows that require them.

---

## Testing And Validation

```bash
python -m unittest discover -s tests      # complete test suite
python scripts/validate_repo.py --root .   # Repository integrity check
examlex check-deps                         # Tool dependency check
examlex ops-check                          # 13-point operational readiness check
```

## Documentation

| Document | Purpose |
|----------|---------|
| [Getting Started](docs/getting-started.md) | Local installation and first use. |
| [Configuration](docs/configuration.md) | Authoritative configuration and environment variables. |
| [Usage](docs/usage.md) | Complete learning workflow. |
| [Architecture](docs/architecture.md) | Repository layers and boundaries. |
| [Design](docs/design.md) | Public-safe, deterministic, two-track design principles. |
| [Prompt Policy](docs/prompt-policy.md) | Rules for public-safe and full-local prompt modes. |
| [Development](docs/development.md) | Source layout and local checks. |
| [Troubleshooting](docs/troubleshooting.md) | Common failures and remedies. |
| [Release](docs/release.md) | Versioning and release checklist. |
| [Project Quality](docs/project-quality.md) | Repository quality and release checks. |
| [CET-4](docs/cet4.md) / [CET-6](docs/cet6.md) / [Postgraduate](docs/postgraduate.md) | Exam-specific guidance. |
| [TEM-4](docs/tem4.md) / [TEM-8](docs/tem8.md) | English-major exam guidance. |
| [CLI Reference](cli-reference.md) | Short and full command names. |

---

## Keyword Index

English exam · CET-4 · CET-6 · TEM-4 · TEM-8 · postgraduate English · AI tutor · learning planner · vocabulary builder · grammar correction · reading training · writing revision · error taxonomy · ability profile · daily plan · continuous learning · multi-source distillation · knowledge ingestion · strategy library · RIA++ · cognitive extraction · Agent Skill · public-safe · Claude Code · Codex · Cursor

---

## Community

- [Contribution Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Support](SUPPORT.md)
- [Changelog](CHANGELOG.md)

---

## Contributing

Contributions should keep the project public-safe and deterministically verifiable. Start from [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT. See [LICENSE](LICENSE).
