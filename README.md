# English Exam AI Tutor

[![CI](https://github.com/your-org/english-exam-ai-tutor/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/english-exam-ai-tutor/actions/workflows/ci.yml)
[![CodeQL](https://github.com/your-org/english-exam-ai-tutor/actions/workflows/codeql.yml/badge.svg)](https://github.com/your-org/english-exam-ai-tutor/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Skills](https://img.shields.io/badge/Skills-9-brightgreen.svg)](#tutor-roles)
[![Platforms](https://img.shields.io/badge/Platforms-4-blue.svg)](#platform-integration)

> CET-4 / CET-6 / Postgraduate English — Public-Safe Agent Skills + Deterministic Automation + Continuous Learning
>
> **In one sentence**: Turn the pain of "I don't know where to start with English prep" into a deterministic learning loop — ingest knowledge → diagnose → plan → practice → attribute errors → update → iterate. Every strategy and method you feed in gets absorbed and used in your next study session.

See [zh-CN/README.md](zh-CN/README.md) for the Chinese version.

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
> - **As Agent Skill** (invoke via `/english-exam-ai-tutor` in chat) → `git clone` to your skills directory. Full assistant experience.
> - **Standalone CLI** (command-line only) → `pip install` then use `tutor` or `english-exam-tutor`. Scripts only, no Agent Skill registration.

### Requirements

- Python 3.10+
- Git
- One of: Claude Code / Codex CLI / Codex App / Cursor

### Optional Tools by Distillation Method

| Method | Tools | Install (Windows) | Install (macOS/Linux) |
|--------|-------|-------------------|----------------------|
| `text` | None | — | — |
| `person` | None | — | — |
| `book` (PDF) | pdftotext | `winget install poppler` | `brew install poppler` / `apt install poppler-utils` |
| `book` (DOCX) | python-docx | `pip install python-docx` | `pip3 install python-docx` |
| `book` (EPUB DRM) | calibre | `winget install calibre` | `brew install calibre` |
| `video` (download) | yt-dlp | `pip install yt-dlp` | `pip3 install yt-dlp` |
| `video` (audio) | ffmpeg | `winget install ffmpeg` | `brew install ffmpeg` / `apt install ffmpeg` |
| `video` (ASR) | whisper or SILICONFLOW_API_KEY | `pip install openai-whisper` | `pip3 install openai-whisper` |

Run `bin/tutor check-deps` to see what's installed.

### As Agent Skill (recommended)

One-line install:
```bash
npx skills add your-org/english-exam-ai-tutor
```

Or clone manually to `skills\english-exam-ai-tutor` under your platform's skills directory:

```bash
# Claude Code
git clone https://github.com/your-org/english-exam-ai-tutor.git ~/.claude/skills/english-exam-ai-tutor

# Codex CLI / Codex App
git clone https://github.com/your-org/english-exam-ai-tutor.git ~/.agents/skills/english-exam-ai-tutor

# Cursor
git clone https://github.com/your-org/english-exam-ai-tutor.git ~/.cursor/skills/english-exam-ai-tutor
```

Or use the installer scripts:
```bash
./install.sh claude    # or: codex, cursor
.\install.ps1 claude   # PowerShell
```

Restart your agent, then invoke:
```text
/english-exam-ai-tutor Create a 30-day CET4 plan for a weak-foundation learner targeting 550+.
/learning-planner Give me a 30-day plan for a CET4 550+ learner with weak foundation.
/grammar-corrector Check this essay and give me a correction report.
```

### Standalone CLI (optional)

```bash
git clone https://github.com/your-org/english-exam-ai-tutor.git
cd english-exam-ai-tutor
pip install -e .
```

Then use:
```bash
tutor plan learner-profile.json --ability ability-profile.json
tutor errors practice-ledger.json --days 30
english-exam-tutor daily-plan --profile learner-profile.json --ability ability-profile.json
```

> `pip install -e .` installs only the script engine. Agent conversation features still require `git clone` to a skills directory.

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
| Full workflow | `english-exam-ai-tutor` | `/english-exam-ai-tutor` |
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
tutor extract --input <url|file|name> [--type auto|video|book|text|person]
tutor validate --artifacts-dir <path>
tutor commit --artifacts-dir <path> --library strategy-library.json
tutor ops-check    # 13-point operational readiness check
```

Five distillation methods: `direct` (text), `book` (PDF/EPUB/DOCX), `video` (B站/YouTube + ASR), `person` (cognitive extraction), `manual` (conversation notes). Each strategy is automatically scored on a 9-dimension Darwin rubric (100 points). Strategies below 70 enter hill-climb optimization (max 3 rounds).

See [skills/english-exam-ai-tutor/references/multi-source-distillation.md](skills/english-exam-ai-tutor/references/multi-source-distillation.md) for full documentation.

---

## Usage

### Quick Examples

```bash
# Diagnose (supports CET4, CET6, TEM4, TEM8, POSTGRADUATE_ENGLISH)
tutor check examples/sample-learner-profile.yaml

# Plan with vocab pool and spaced repetition
tutor plan examples/sample-learner-profile.yaml \
  --ability examples/sample-ability-profile.yaml \
  --vocab-pool skills/english-exam-ai-tutor/assets/data/vocabulary/cet4-core-2000.json \
  --output daily-plan.json

# Record timed practice
tutor log practice-ledger.json \
  --date 2026-07-06 --exam-type CET4 --module reading \
  --task-id timed-001 --duration-minutes 42 --total-items 20 --correct-items 14 \
  --timed --overtime-items 3 --overtime-correct 1

# Estimate vocabulary
tutor vocab --interactive --output vocab-estimate.json

# Visualize progress
tutor report --ability-history ability-history.json \
  --ledger practice-ledger.json --days 30 --output report.html

# Ingest strategy
tutor ingest reading-strategy.md --library strategy-library.json --exam-types CET4,CET6 --modules reading

# Full pipeline
tutor extract --input ./cet4-guide.pdf --type book
tutor validate --artifacts-dir <path>
tutor commit --artifacts-dir <path> --library strategy-library.json
```

### CLI Wrappers

The project provides `bin/tutor` (bash) and `bin/tutor.ps1` (PowerShell) wrappers:

| Command | Equivalent |
|---------|-----------|
| `tutor check <file>` | Validate learner profile |
| `tutor plan <file> --ability ...` | Generate daily plan |
| `tutor errors <file>` | Summarize error tags |
| `tutor trends <file>` | Analyze practice trends |
| `tutor score <essay>` | Estimate writing score |
| `tutor ingest <file>` | Ingest strategy file |
| `tutor extract --input <url>` | Extract from video/book/text |
| `tutor check-deps` | Check tool dependencies |
| `tutor ops-check` | 13-point operational check |

---

## Configuration

### Skill Installation Paths

| Platform | Personal skills root | Project-local root |
|----------|---------------------|-------------------|
| Claude Code | `$HOME\.claude\skills` | `.claude\skills` |
| Codex CLI / Codex App | `$HOME\.agents\skills` | `.agents\skills` |
| Cursor | `$HOME\.cursor\skills` | `.cursor\skills` |

### Environment Variables

Copy `.env.example` to `.env`:

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `SILICONFLOW_API_KEY` | No | — | Cloud ASR key (SenseVoiceSmall, alternative to local whisper) |
| `TUTOR_PYTHON` | No | `python` | Python interpreter for the `tutor` wrapper |

---

## Architecture

### Architecture Overview

```
Agent Layer (Claude Code / Codex / Cursor)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Skill Layer (skills/english-exam-ai-tutor/)            │
│  Tutor roles · Reference docs · Templates · Schemas     │
│  8 shortcut Skills (skills/*/)                           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Script Layer (skills/english_exam_ai_tutor/)            │
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

No. All five distillation paths are implemented in ~25 Python files within the project. The five reference projects (cangjie-skill, nuwa-skill, book-to-skill, video-downloader, darwin-skill) were studied for methodology only — their code is NOT bundled. Heavy tools (yt-dlp, ffmpeg, whisper, Docling, calibre) are optional and lazy-loaded. `text` and `person` distillation import nothing beyond the Python standard library. The entire project is ~1.9 MB.

### Repository Layout

```
.
├── SKILL.md                         # Root-level Skill entry (npx skills add compatible)
├── install.sh / install.ps1         # Cross-platform installer scripts
│
├── skills/english-exam-ai-tutor/    # Portable public-safe Skill package
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
├── skills/english_exam_ai_tutor/    # Importable Python mirror (tests + CLI)
├── skills/*/                        # 8 shortcut Skills
├── integrations/                    # Platform adapters
├── docs/                            # English docs
├── zh-CN/                           # Chinese docs
├── examples/                        # Sample profiles, ledgers, etc.
├── tests/                           # 210+ tests
├── scripts/                         # Repo validators and installers
├── .github/                         # CI/CD, issue/PR templates
└── pyproject.toml                   # Package metadata
```

---

## Supported Learners

| Exam | ID | Target Bands |
|------|----|-------------|
| CET-4 | `CET4` | `425~499`, `500~550`, `550+`, `600+` |
| CET-6 | `CET6` | `425~499`, `500~550`, `550+`, `600+` |
| Postgraduate English | `POSTGRADUATE_ENGLISH` | `50+`, `70~80`, `80+`, `90+` |
| TEM-4 | `TEM4` | `60~69`, `70~79`, `80+` |
| TEM-8 | `TEM8` | `60~69`, `70~79`, `80+` |

Foundation levels: `基础偏弱` (weak) / `中等基础` (moderate) / `基础较好` (strong).

---

## Error Taxonomy

| Module | Example Tags | Dimensions |
|--------|-------------|------------|
| Vocabulary | `VOCAB_MEANING_RECOGNITION_FAIL`, `VOCAB_SPELLING_FAIL` | Meaning, spelling, audio recognition, context use |
| Listening | `LISTENING_KEYWORD_MISS`, `LISTENING_NUMBER_DATE_FAIL` | Keywords, linking/weak forms, numbers/dates, main idea |
| Reading | `READING_LONG_SENTENCE_FAIL`, `READING_PARAPHRASE_FAIL` | Speed, locating, long sentences, inference |
| Translation | `TRANSLATION_GRAMMAR_FAIL`, `TRANSLATION_CHINESE_ENGLISH` | Grammar, word choice, Chinese-English transfer, variety |
| Writing | `WRITING_ARTICLE_OMISSION`, `WRITING_LANGUAGE_ACCURACY_FAIL` | Task response, structure, accuracy, expression richness |

See [skills/english-exam-ai-tutor/references/error-taxonomy.md](skills/english-exam-ai-tutor/references/error-taxonomy.md).

---

## Platform Integration

| Platform | Invocation | Shortcut Prefix | Adapter |
|----------|-----------|:--------------:|--------|
| Claude Code | `/english-exam-ai-tutor` | `/` | [Guide](integrations/claude-code/README.md) |
| Codex CLI | `/english-exam-ai-tutor` | `/` | [Guide](integrations/codex-cli/README.md) |
| Codex App | `/english-exam-ai-tutor` | `/` | [Guide](integrations/codex-app/README.md) |
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
No. In most cases you speak natural language in your Agent chat. The Agent reads the workflow from SKILL.md and calls scripts as needed. CLI and `tutor` wrappers are mainly for debugging, scripting, and standalone use.

**"Will strategy library data be uploaded to the cloud?"**
No. The strategy library is a local JSON file. Extraction and analysis happen on your machine. If your Agent model runs in the cloud, the text you send follows that provider's standard data terms.

**"Can I share my strategy library?"**
Your own exam strategies — yes. Strategies extracted from copyrighted books — do not publish them publicly. Same rules as handwritten study notes: your notes are yours, but don't republish someone else's book content.

**"Does continuous learning increase the project size?"**
No. All five distillation paths are ~25 built-in Python files. The five reference projects were studied for methodology, not bundled. Heavy tools are optional and lazy-loaded. The project is ~1.9 MB.

---

## Testing And Validation

```bash
python -m pytest tests/                    # 210+ tests
python scripts/validate_repo.py --root .   # Repository integrity check
tutor check-deps                           # Tool dependency check
tutor ops-check                            # 13-point operational readiness check
```

---

## Roadmap

- [x] CET-4 / CET-6 / Postgraduate English exam profiles
- [x] TEM-4 / TEM-8 support
- [x] Multi-source continuous learning (text/book/video/person/manual)
- [x] Darwin 9-dimension quality scoring with auto-optimization
- [x] 13-point operational readiness check (`tutor ops-check`)
- [ ] IELTS / TOEFL support
- [ ] Web UI for strategy library browsing

---

## Contributing

Contributions should keep the project public-safe and deterministically verifiable. Start from [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT. See [LICENSE](LICENSE).
