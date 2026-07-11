# ExamLex

> **Status:** ExamLex is currently unpublished. Install it from a local checkout. This documentation is intentionally self-contained and does not depend on remote links or badges.

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
> - **As Agent Skill** (invoke via `/examlex` in chat) → run a local installer from this checkout. Full assistant experience.
> - **Standalone CLI** (command-line only) → install the checkout, then use `examlex`. Scripts only, no Agent Skill registration.

### Requirements

- Python 3.10+
- Git
- One of: Claude Code / Codex CLI / Codex App / Cursor

### Feature Dependencies

Core tutoring and direct-text ingestion need no third-party Python package. The following tools are required only when you use the corresponding book or video feature.

| Method | Tools | Install (Windows) | Install (macOS/Linux) |
|--------|-------|-------------------|----------------------|
| `text` | None | — | — |
| `person` | None | — | — |
| `book` (PDF) | pdftotext | `winget install poppler` | `brew install poppler` / `apt install poppler-utils` |
| `book` (DOCX) | python-docx | `pip install python-docx` | `pip3 install python-docx` |
| `book` (EPUB DRM) | calibre | `winget install calibre` | `brew install calibre` |
| `video` (download/metadata) | yt-dlp | `pip install yt-dlp` | `pip3 install yt-dlp` |
| `video` (merge/convert/audio) | ffmpeg | `winget install ffmpeg` | `brew install ffmpeg` / `apt install ffmpeg` |
| `video` (ASR) | whisper or `SILICONFLOW_API_KEY` | `pip install openai-whisper` | `pip3 install openai-whisper` |

`ffmpeg` is the open-source media converter used in two places: `yt-dlp` may need it to merge separate video and audio streams, and ExamLex needs it to extract/convert audio before either local `whisper` or SiliconFlow ASR. A download-only path can sometimes work without `ffmpeg`, but the complete video-to-transcript pipeline cannot.

Run `bin/examlex check-deps` to see what's installed.

### As Agent Skill (recommended)

From the project root, use the local installer scripts. They copy `skills\examlex` and the eight shortcut Skills into the selected platform's Skill directory:

```bash
./install.sh claude    # or: codex, cursor
.\install.ps1 claude   # PowerShell
```

Restart your agent, then invoke:
```text
/examlex Create a 30-day CET4 plan for a weak-foundation learner targeting 550+.
/learning-planner Give me a 30-day plan for a CET4 550+ learner with weak foundation.
/grammar-corrector Check this essay and give me a correction report.
```

### Standalone CLI (optional)

```bash
python -m pip install -e .
```

Then use:
```bash
examlex plan learner-profile.json --ability ability-profile.json
examlex errors practice-ledger.json --days 30
examlex daily-plan --profile learner-profile.json --ability ability-profile.json
```

> `python -m pip install -e .` installs only the script engine. Agent conversation features require the local Skill installer above.

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
| [Development](docs/development.md) | Source layout and local checks. |
| [Troubleshooting](docs/troubleshooting.md) | Common failures and remedies. |
| [Release](docs/release.md) | Versioning and release checklist. |
| [Roadmap](docs/roadmap.md) | Implemented and planned work. |
| [CLI Reference](cli-reference.md) | Short and full command names. |

---

## Roadmap

- [x] CET-4 / CET-6 / Postgraduate English exam profiles
- [x] TEM-4 / TEM-8 support
- [x] Multi-source continuous learning (text/book/video/person/manual)
- [x] Darwin 9-dimension quality scoring with auto-optimization
- [x] 13-point operational readiness check (`examlex ops-check`)
- [ ] IELTS / TOEFL support
- [ ] Web UI for strategy library browsing

---

## Contributing

Contributions should keep the project public-safe and deterministically verifiable. Start from [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT. See [LICENSE](LICENSE).
