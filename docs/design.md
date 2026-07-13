# Design Rationale

ExamLex is intentionally split into a portable Skill and small deterministic scripts.

The Skill gives agents the tutoring frame: supported exams, learner levels, target bands, the eight assistant roles, prompt modes, references, and templates. The scripts keep the measurable parts stable: profile validation, daily planning, practice recording, error summaries, ability updates, trend analysis, writing versioning, and writing rubric estimates.

## Public-Safe Release

This repository is suitable for public GitHub release because it publishes role boundaries and placeholders, not private prompt bodies. Public-safe docs can explain what each assistant does and how to route tasks, but they must not reproduce or reconstruct the original eight tutor prompts.

Full-local mode is a local operating mode only. It can select private prompt assets that live outside this repository, but those assets must stay out of shared files.

## Deterministic Automation

The scripts deliberately avoid probabilistic planning or scoring logic. This makes learner state auditable:

- `validate_profile.py` rejects unsupported exam tracks, bands, and required-field gaps.
- `generate_daily_plan.py` solves a constrained daily plan from time budget, target exam, ability state, and error evidence.
- `record_practice.py` stores repeatable ledger entries with explicit `total_items` and `correct_items`.
- `summarize_errors.py` groups error tags by tag, module, and dimension.
- `update_ability_profile.py` converts practice evidence into ability changes.
- `score_writing_rubric.py` gives a deterministic rubric estimate for revision guidance, not official scoring.

## Planning Model

Daily planning is constraint solving rather than generic advice. The planner respects:

- learner exam type and target band,
- foundation level,
- daily time budget,
- low-status ability nodes,
- repeated or high-impact error tags,
- module coverage across vocabulary, listening, reading, translation, and writing.

The agent may adapt learner-facing wording, but the planned modules, minutes, focus, and reasons should remain consistent with script output unless the learner changes constraints.

## Adapted Continuous-Learning Principles

ExamLex adapts ideas from Nuwa Skill, book-to-skill, Cangjie Skill, video-downloader, AI HOT, and Darwin Skill to an English-exam strategy library. It does not claim feature parity with those projects.

| Source principle | ExamLex implementation |
| --- | --- |
| Nuwa: multi-angle collection, triple verification, five cognitive layers, and an honesty boundary | `prompts/cognitive.py`, source provenance, RIA boundary fields, and validation tests |
| book-to-skill: structure instead of raw-text dumping, chapter-level progressive disclosure, glossary extraction, and actionable language | the book extractor's chapter/glossary artifacts, RIA prompts, and specificity checks |
| Cangjie: Adler overview, parallel method extraction, RIA-TV++, strategy linking, and pressure tests | `prompts/ria.py`, `related_strategies`, RIA schema validation, and effect evaluation |
| video-downloader: stable download/transcript artifacts and explicit media-tool boundaries | `yt-dlp` download/metadata, `ffmpeg` stream merging and audio conversion, and local `whisper` or SiliconFlow ASR |
| AI HOT: a fixed read-only source contract, intent-oriented routing, pagination discipline, attribution, and an untrusted-content boundary | the maintained source catalog, verified feed endpoints, bounded metadata collection, evidence labels, local deduplication, and explicit text/media materialization |
| Darwin: validation-gated edits, measurable scoring, ratchet retention, early stop, and auditable evidence | deterministic structure scoring, Agent effect tests, threshold-gated commit, immutable revisions, approval hashes, and score history |

The hard guarantees are the deterministic checks, hashes, immutable revision references, approval threshold, and ratchet behavior implemented in Python. Multi-agent research, parallel extractors, pressure-test execution, and independent judges are Agent-orchestrated requirements. ExamLex records and validates their artifacts, but the current Python CLI does not itself launch or prove two fresh independent reviewers for every optimization round. Video URL support is currently limited to Bilibili and YouTube; it does not claim the wider provider coverage of the upstream video-downloader project.
