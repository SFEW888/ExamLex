# Getting Started

Use this guide to install ExamLex from the public [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex) repository.

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- PowerShell or a POSIX shell for the local installer

Core tutoring and direct-text ingestion require no third-party Python package. Multi-source ingestion has feature-specific dependencies:

| Feature | Required tools |
| --- | --- |
| Video download and metadata | `yt-dlp` |
| Video stream merge, media conversion, and audio extraction | `ffmpeg` |
| Video speech-to-text | local `whisper` or `SILICONFLOW_API_KEY`; both paths still use `ffmpeg` for audio preparation |
| PDF extraction | `pdftotext` (Poppler) |
| DRM-free e-book conversion fallback | `ebook-convert` (Calibre) |

Run `bin/examlex check-deps` after installation. The complete video-to-transcript path requires both `yt-dlp` and `ffmpeg`, plus one ASR backend.

## Agent Install With Shortcut Skills

Use this path when you want the main Skill plus all eight shortcut Skills.

Clone the repository first:

```powershell
git clone https://github.com/SFEW888/ExamLex.git
Set-Location ExamLex
```

From the project root on macOS/Linux:

```bash
./install.sh codex
./install.sh claude
```

From the project root in Windows PowerShell:

```powershell
.\install.ps1 codex
.\install.ps1 claude
```

Use project-local installs when you only want the Skills in the current project:

```powershell
.\install.ps1 codex -Project
.\install.ps1 claude -Project
```

Preview targets first:

```bash
./install.sh codex --dry-run
./install.sh claude --dry-run
```

Verify in the Agent:

```text
/skills
/examlex 帮我为 CET4 550+ 制定一周计划
/learning-planner 帮我生成本周任务
/grammar-corrector 批改这段作文
```

## Shortcut Skill Names

Use these in Agent chat instead of long Python commands:

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

## Supported Exams

This tutor supports five exam types:

| Exam | Target Bands | Unique Modules |
|------|-------------|----------------|
| CET-4 | 425~499, 500~550, 550+, 600+ | — |
| CET-6 | 425~499, 500~550, 550+, 600+ | — |
| Postgraduate | 50+, 70~80, 80+, 90+ | — |
| TEM-4 | 60~69, 70~79, 80+ | dictation, language-knowledge |
| TEM-8 | 60~69, 70~79, 80+ | proofreading |

## New Features

- **Vocabulary Estimation**: `examlex vocab --interactive` — Yes/No sampling with false-alarm correction
- **Timed Practice**: `examlex log --timed` — auto time-limit lookup + overtime tracking
- **Spaced Repetition**: automatic review urgency scoring in error summaries
- **Progress Visualization**: `examlex report` — standalone HTML with SVG radar/trend/error charts
- **Vocabulary Pool**: built-in 650 words across 5 exam levels
- **Common Error Library**: 21 curated error patterns with examples
- **Model Essay Library**: scored sample essays for rubric anchoring
- **Backup & Restore**: `examlex backup` / `examlex restore` with tar.gz support

## Install And Run The CLI

Install the CLI directly from GitHub:

```powershell
python -m pip install "git+https://github.com/SFEW888/ExamLex.git"
examlex --help
```

Use these wrappers when you want to run the deterministic tools directly from a terminal:

```bash
bin/examlex check examples/sample-learner-profile.yaml
bin/examlex plan examples/sample-learner-profile.yaml --ability examples/sample-ability-profile.yaml --output daily-plan.json
bin/examlex strategies --library strategy-library.json  # 需要你创建/积累的策略库文件 (create/accumulate your own strategy library file)
```

PowerShell:

```powershell
.\bin\examlex.ps1 check examples/sample-learner-profile.yaml
.\bin\examlex.ps1 plan examples/sample-learner-profile.yaml --ability examples/sample-ability-profile.yaml --output daily-plan.json
```

The underlying Python module is for maintainers and debugging:

```powershell
python -m examlex --help
```

See [../cli-reference.md](../cli-reference.md) for all short commands.

## Validate The Repository

Maintainers can still run the deterministic checks directly:

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
```

## Optional Editable Install

```powershell
python -m pip install -e .
examlex --help
```

Generated local files such as `daily-plan.json`, `.env`, and learner records should stay untracked.
