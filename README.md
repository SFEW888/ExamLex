# English Exam AI Tutor

English Exam AI Tutor is a public-safe agent Skill plus automation toolkit for CET-4, CET-6, and postgraduate English preparation. It combines eight tutor roles with deterministic scripts for profile validation, constrained daily planning, practice logging, error attribution, ability updates, trend analysis, and writing rubric estimates.

The repository is designed for local use with Claude Code, Codex, Codex App, and Cursor. Public files contain role descriptions and prompt placeholders only; private local prompt bodies are not published here.

## Supported Learners

- Foundation levels: weak foundation, middle foundation, strong foundation.
- CET-4 and CET-6 target bands: `425~499`, `500~550`, `550+`, `600+`.
- Postgraduate English target bands: `50+`, `70~80`, `80+`, `90+`.

The scripts help keep daily work realistic for the learner's time budget. They do not guarantee official exam scores.

## Quick Start

Run commands from the repository root in PowerShell.

```powershell
python scripts\validate_repo.py --root . --json
python -m skills.english_exam_ai_tutor validate-profile --profile examples\sample-learner-profile.yaml
python -m skills.english_exam_ai_tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --output daily-plan.json
```

After practice has produced an error summary, include it in the next plan:

```powershell
python -m skills.english_exam_ai_tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --errors error-summary.json --output daily-plan.next.json
```

Record practice with PowerShell-friendly flags:

```powershell
python -m skills.english_exam_ai_tutor record-practice --ledger practice-ledger.json --date 2026-07-05 --exam-type CET4 --module writing --task-id writing-article-drill --duration-minutes 20 --total-items 10 --correct-items 7 --error-tags WRITING_ARTICLE_OMISSION --print-record
```

Summarize errors, update ability, and score writing:

```powershell
python -m skills.english_exam_ai_tutor summarize-errors --ledger practice-ledger.json --output error-summary.json
python -m skills.english_exam_ai_tutor update-ability --ability examples\sample-ability-profile.yaml --ledger practice-ledger.json --output ability-profile.next.json
python -m skills.english_exam_ai_tutor score-writing --text "I think English study is important because it helps me read more and express ideas clearly." --exam-type CET4 --output writing-score.json
```

Install the package in editable mode to use the shorter console command:

```powershell
python -m pip install -e .
english-exam-tutor validate-profile --profile examples\sample-learner-profile.yaml
english-exam-tutor daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --output daily-plan.json
```

## Install

Preview the copy target first:

```powershell
python scripts\install_claude.py --dry-run --json
python scripts\install_codex.py --dry-run --json
python scripts\install_cursor.py --dry-run --json
```

Install for each platform:

```powershell
python scripts\install_claude.py --force
python scripts\install_codex.py --force
python scripts\install_cursor.py --force
```

Platform-specific notes live in:

- [Claude Code](integrations/claude-code/README.md)
- [Codex CLI](integrations/codex-cli/README.md)
- [Codex App](integrations/codex-app/README.md)
- [Cursor](integrations/cursor/README.md)

## Prompt Modes

- Public-safe mode is the default for GitHub, examples, documentation, and shared artifacts. It includes assistant names, role boundaries, script interfaces, templates, schemas, and placeholders such as `[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]`.
- Full-local mode may route to private prompt assets on the user's machine, but those assets stay outside this public repository.
- The original eight tutor prompt bodies are not published here and must not be rewritten into public docs, examples, adapters, or generated release artifacts.

See [docs/prompt-policy.md](docs/prompt-policy.md).

## Repository Layout

```text
.
|-- docs/                         Project, architecture, usage, and exam guidance.
|-- examples/                     Sample learner, ability, ledger, and writing files.
|-- integrations/                 Platform adapter notes and minimal configs.
|-- scripts/                      Repo validation and installer scripts.
|-- skills/english-exam-ai-tutor/ Portable public-safe Skill package.
|-- skills/english_exam_ai_tutor/ Importable mirror used by tests and scripts.
|-- tests/                        Unit tests for installers, validators, and automation.
`-- pyproject.toml                Package metadata and public-safe prompt mode flag.
```

## Documentation

- [Design rationale](docs/design.md)
- [Architecture](docs/architecture.md)
- [Usage workflow](docs/usage.md)
- [Prompt policy](docs/prompt-policy.md)
- [Contributing](docs/contributing.md)
- [CET-4 guide](docs/cet4.md)
- [CET-6 guide](docs/cet6.md)
- [Postgraduate English guide](docs/postgraduate.md)

## Testing And Validation

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
git diff --check
```

For prompt-safety checks, search for any private prompt text before committing and confirm the portable Skill directory does not contain root-style install docs:

```powershell
Get-ChildItem -Name skills\english-exam-ai-tutor | Where-Object { $_ -in @('README.md','INSTALL.md') }
```
