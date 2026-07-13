# CLI Command Reference

> Run commands through the installed `examlex` console entry, `bin/examlex` on bash, `bin/examlex.ps1` on PowerShell, `python -m examlex`, or `python run.py` inside a copied ExamLex Skill directory.

## Invocation Classes

| Mark | Meaning |
|:----:|---------|
| A | Agent-led: normally invoked by an Agent during a workflow. |
| U | User-facing: suitable for direct terminal use. |
| M | Maintainer-facing: intended for diagnostics, tests, or repository operations. |

## Command Overview

### Exam-preparation loop

| Short command | Full command | Class | Purpose |
|---------------|--------------|:-----:|---------|
| `examlex check <file>` | `validate-profile` | U | Validate a learner profile. |
| `examlex plan <file> [opts]` | `daily-plan` | U | Generate a constrained daily plan. |
| `examlex log <file> [opts]` | `record-practice` | A | Append a practice record. |
| `examlex tag <text> [opts]` | `tag-error` | A | Infer deterministic error tags. |
| `examlex errors <file> [opts]` | `summarize-errors` | U | Summarize error-ledger statistics. |
| `examlex update <ability> <ledger>` | `update-ability` | A | Update an ability profile from evidence. |
| `examlex trends <file> [opts]` | `analyze-trends` | U | Analyze practice and ability trends. |
| `examlex write <writing-id> [opts]` | `writing-version` | A | Append a writing draft version. |
| `examlex score <essay> [opts]` | `score-writing` | U | Produce a deterministic, non-official writing estimate. |

### Knowledge management

| Short command | Full command | Class | Purpose |
|---------------|--------------|:-----:|---------|
| `examlex extract --input <source> [opts]` | `extract` | A | Extract source material from text, books, videos, or people. |
| `examlex source-list [opts]` | `source-list` | U | List merged CET/postgraduate source candidates and evidence labels. |
| `examlex source-collect --source <id> [opts]` | `source-collect` | A | Collect verified RSS/Atom metadata into a local corpus. |
| `examlex source-fetch --source <id> --item <id> --kind <text\|media>` | `source-fetch` | A | Explicitly materialize one indexed public item. |
| `examlex ingest <file> [opts]` | `ingest-strategy` | U | Ingest strategies into a library. |
| `examlex strategies [opts]` | `list-strategies` | U | List or search ingested strategies. |
| `examlex validate --artifacts-dir <path>` | `validate-strategies` | A | Validate distilled strategies and calculate structure scores. |
| `examlex commit --artifacts-dir <path> --library <path>` | `commit-strategies` | A | Commit strategies atomically after ratchet checks. |

### Data, vocabulary, and operations

| Short command | Full command | Class | Purpose |
|---------------|--------------|:-----:|---------|
| `examlex backup <dir> [opts]` | `backup` | U | Create a compressed learner-data backup. |
| `examlex restore <file> <dir> [opts]` | `restore` | U | Restore learner data. |
| `examlex report [opts]` | `visualize` | U | Generate an HTML progress report. |
| `examlex vocab [opts]` | `vocab-estimate` | U | Estimate vocabulary size by sampling. |
| `examlex prompt-check --private-dir <dir> [opts]` | `prompt-check` | U | Validate an external private prompt set without exposing its text. |
| `examlex tutor-prepare --request <text> [opts]` | `tutor-prepare` | A | Route a request and return at most two safe clarification questions. |
| `examlex resume <session-id> [opts]` | `resume` | U | Show guidance for resuming an existing distillation session. |
| `examlex sessions-cleanup [opts]` | `sessions-cleanup` | M | Preview or archive stale sessions. |
| `examlex check-deps [opts]` | `check-deps` | M | Check optional external tools. |
| `examlex ops-check [opts]` | `ops-check` | M | Run operational readiness checks. |
| `examlex validate-strategy <file>` | `validate-strategy` | M | Validate a strategy-library file. |

## Detailed Signatures

### `examlex check` — validate a learner profile

```bash
examlex check <profile>
examlex check learner-profile.json
```

Equivalent full command: `validate-profile --profile <profile>`.

### `examlex plan` — generate a daily plan

```bash
examlex plan <profile> --ability <file> --output <file> [--date YYYY-MM-DD]
examlex plan learner-profile.json --ability ability-profile.yaml --output daily-plan.md
```

Equivalent full command: `daily-plan --profile <profile>`.

### `examlex log` — record practice

```bash
examlex log <ledger> --date <YYYY-MM-DD> --exam-type <exam> --module <module> --task-id <id> --duration-minutes <minutes> --total-items <count> --correct-items <count> [options]
examlex log practice.json --date 2026-07-13 --exam-type CET4 --module reading --task-id reading-001 --duration-minutes 30 --total-items 20 --correct-items 16
```

Equivalent full command: `record-practice --ledger <ledger>`.

### `examlex tag` — infer error tags

```bash
examlex tag <description> [--module <module>]
examlex tag "article omitted before a singular noun" --module writing
```

Equivalent full command: `tag-error --text <description>`.

### `examlex errors` — summarize errors

```bash
examlex errors <ledger> [--output <file>] [--json]
examlex errors practice.json --json
```

Equivalent full command: `summarize-errors --ledger <ledger>`.

### `examlex update` — update ability

```bash
examlex update <ability-profile> <practice-ledger> [--output <file>]
examlex update ability-profile.yaml practice.json
```

Equivalent full command: `update-ability --ability <ability-profile> --ledger <practice-ledger>`.

### `examlex trends` — analyze trends

```bash
examlex trends <ledger> [--history <file>] [--output <file>]
examlex trends practice.json --history ability-history.json
```

Equivalent full command: `analyze-trends --ledger <ledger>`.

### `examlex write` — manage writing versions

```bash
examlex write <writing-id> --file <versions.json> --text <essay> [options]
examlex write essay-001 --file writing-versions.json --text "Improved version" --version V2
```

Equivalent full command: `writing-version --file <versions.json> --writing-id <writing-id> --text <essay>`.

### `examlex score` — estimate writing quality

```bash
examlex score <essay-file> [--exam-type CET4] [--json]
examlex score essay.txt --exam-type CET6 --json
```

Equivalent full command: `score-writing --text-file <essay-file>`. Results are local estimates, not official exam scores.

### `examlex source-list` — inspect the evidence-labeled source catalog

```bash
examlex source-list
  [--exam cet|postgraduate]
  [--section <section>]
  [--evidence S|A|B|C|R]
  [--media article|audio|video|report]
  [--collectable]
  [--references]
  [--json]
```

Named outlets are maintained as `B` or `C` until an article-level trace supplies
the exam, section, original title or URL, and comparison evidence. The catalog
does not contain fixed outlet percentages.

### `examlex source-collect` — index verified RSS/Atom feeds

```bash
examlex source-collect --source <id-or-alias>
  [--limit 1..100]
  [--content-mode metadata|text]
  [--delay 0..60]
  [--output-dir <dir>]
  [--json]
```

`metadata` is the default. `text` also attempts readable-text extraction only
when the source page is public and `robots.txt` allows it. No cookie, login, or
paywall bypass is used.

### `examlex source-fetch` — materialize one indexed item

```bash
examlex source-fetch --source <id-or-alias> --item <item-id> --kind text
  [--output-dir <dir>] [--json]

examlex source-fetch --source <id-or-alias> --item <item-id> --kind media
  [--max-media-mb 1..1024] [--output-dir <dir>] [--json]
```

Media download requires an audio/video enclosure from a maintained source feed
and an explicit item selection. The default hard limit is 100 MiB. See
`skills/examlex/references/source-collection.md` for the evidence, safety, and
simulation-provenance contract.

### `examlex extract` — extract source material

```bash
examlex extract --input <file-or-symbolic-source> --type <auto|text|book|video|person> [options]
examlex extract --input notes.txt --type text
examlex extract --input VIDEO_URL --type video
```

The command writes extraction artifacts into a session directory for later distillation.

### `examlex ingest` — ingest strategies

```bash
examlex ingest <file> --library <file> [--source-type <type>] [--json]
examlex ingest strategy.md --library strategy-library.json
```

Equivalent full command: `ingest-strategy --file <file>`.

Ingest is idempotent for the same source bytes and ingestion scope. Repeating
the same file with the same exam types, modules, source type, distillation
method, source URL, and explicit structured fields returns the existing
strategy instead of appending a duplicate. The same source may still produce a
separate strategy when its exam or module scope differs.

### `examlex strategies` — list strategies

```bash
examlex strategies --library <file> [--query <text>] [--module <module>] [--json]
examlex strategies --library strategy-library.json --module reading
```

Equivalent full command: `list-strategies`.

### `examlex validate` — validate distilled artifacts

```bash
examlex validate --artifacts-dir <dir> [--json]
examlex validate --artifacts-dir session-artifacts --json
```

Equivalent full command: `validate-strategies`.

### `examlex commit` — commit distilled strategies

```bash
examlex commit --artifacts-dir <dir> --library <file> [--json]
examlex commit --artifacts-dir session-artifacts --library strategy-library.json
```

Equivalent full command: `commit-strategies`.

### `examlex backup` and `examlex restore`

```bash
examlex backup <data-dir> [--output <archive>] [--json]
examlex restore <archive> <data-dir> [--force] [--dry-run] [--json]
```

The full commands are `backup` and `restore`. Compatibility spellings `backup-data` and `restore-data` route to the same implementations.

### `examlex report` — generate progress HTML

```bash
examlex report --ability-history <file> --ledger <file> [--error-summary <file>] [--output <html>]
examlex report --ability-history ability-history.json --ledger practice.json --output report.html
```

Equivalent full command: `visualize`.

### `examlex vocab` — estimate vocabulary size

```bash
examlex vocab --interactive [--bands <range>] [--samples-per-band <n>] [--nonwords-per-band <n>]
examlex vocab --wordlist answers.json [--json]
```

Equivalent full command: `vocab-estimate`. Reference word data is included in the installed package.

### `examlex prompt-check` — validate external private prompts

```powershell
examlex prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" [--json]
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --save --json
```

The directory must contain exactly one UTF-8 `<role-id>.md` file for each of the eight public role contracts. The command validates filenames and file safety and reports byte sizes and SHA-256 hashes only. It never prints prompt bodies or the directory path. `--save` stores the external directory in local user configuration. Keep it outside the repository and never commit it.

### `examlex tutor-prepare` — route and clarify a tutor request

```powershell
examlex tutor-prepare --request "Correct: I has finished it yesterday." [--role auto] [--asked-field <name>] [--json]
python run.py tutor-prepare --request "Plan my CET-6 study" --json
```

This public-safe preflight does not load private prompts or call a model. It selects one to three roles and returns at most two material clarification questions. Repeat `--asked-field` for fields already asked so a later turn does not repeat them. Actual private execution is an in-process library call through `run_tutor_turn()` and an injected trusted provider.

### `examlex resume` — resume a distillation session

```bash
examlex resume <session-id> [--sessions-root <dir>] [--json]
examlex resume 12345678-1234-1234-1234-123456789abc --json
```

The command reads the existing pipeline state and returns the current stage, artifacts directory, and next action without creating a new session.

### `examlex sessions-cleanup` — archive or prune stale sessions

```bash
examlex sessions-cleanup [--sessions-root <dir>] [--archive-root <dir>] [--older-than-hours 24]
examlex sessions-cleanup --sessions-root sessions --older-than-hours 24 --apply
examlex sessions-cleanup --older-than-hours 168 --prune-terminal-artifacts
examlex sessions-cleanup --older-than-hours 168 --prune-terminal-artifacts --apply
```

The default is a dry run. Without a pruning option, `--apply` moves eligible
non-terminal sessions without overwriting an existing archive target.
`--prune-terminal-artifacts` instead selects stale committed sessions and, only
with `--apply`, removes reproducible `full_text`, audio, transcript, and chapter
artifacts. Pipeline state, distilled strategies, validation/evaluation reports,
and other audit files remain in place.

### `examlex check-deps` and `examlex ops-check`

```bash
examlex check-deps [--json]
examlex ops-check [--library <file>] [--json] [--offline]
```

`check-deps` reports optional tools. `ops-check` runs the operational readiness suite. Use `--offline` for deterministic local or CI diagnostics without live Bilibili, YouTube, or SiliconFlow requests.

## Full Command Names

The dispatcher also accepts these full names directly:

```text
analyze-trends       backup              check-deps
commit-strategies    daily-plan          extract
ingest-strategy      list-strategies     ops-check
prompt-check         record-practice     restore
resume
score-writing        sessions-cleanup    summarize-errors
tag-error            tutor-prepare       update-ability
validate-profile
validate-strategies  validate-strategy   visualize
vocab-estimate       writing-version
```

## Equivalent Invocation Forms

```bash
examlex plan learner-profile.json --ability ability-profile.yaml
python -m examlex daily-plan --profile learner-profile.json --ability ability-profile.yaml
examlex daily-plan --profile learner-profile.json --ability ability-profile.yaml
```
