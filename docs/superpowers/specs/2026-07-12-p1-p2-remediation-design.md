# P1/P2 Audit Remediation Design

## Goal

Resolve every confirmed P1 and P2 finding from the 2026-07-12 full audit without
reintroducing either bilingual Roadmap section or weakening the public-safe Skill
contract.

## Scope And Decisions

1. Ability updates treat the complete practice ledger as the source of truth.
   Existing derived statistics are cleared and recomputed so repeated runs are
   idempotent and ledger corrections are reflected.
2. Daily planning reserves one ten-minute vocabulary slot when a non-empty
   vocabulary pool is supplied and the budget can support both vocabulary and
   another task.
3. JSON Schemas and starter templates follow runtime behavior: TEM4/TEM8 are
   valid learner exams, writing versions accept `V1` and later positive integer
   versions, and practice totals are positive and internally consistent.
4. Validation and evaluation evidence is bound to the canonical SHA-256 digest
   of each distilled strategy. Commit rejects missing, duplicate, stale, or
   mismatched evidence.
5. Strategy-library mutations share one lock-protected read/modify/write helper.
   Atomic writes use unique temporary files, flush to disk, and preserve a
   coherent backup.
6. The Agent installer remains a file-copy installation, but the installed main
   Skill includes a portable Python runner. Skill instructions resolve commands
   from the directory containing `SKILL.md`, so no repository checkout or
   separately installed `examlex` command is required.
7. POSIX entry points are tracked as executable. The documented `resume` command
   becomes a real CLI command that returns structured session guidance.
8. External source text, metadata, URLs, and person names are explicitly
   untrusted data. Source content cannot authorize tool calls, file access,
   secret access, URL navigation, or changes to the distillation procedure.
9. Video extraction validates HTTPS URLs at the extractor boundary using exact
   hosts, no userinfo, standard ports, and public DNS addresses. yt-dlp receives
   `--` before the URL. Cloud ASR is used only when `siliconflow` is explicitly
   selected; `none` disables ASR and `auto` remains local-only.
10. Standard learner artifacts are ignored at the repository root and under a
    dedicated `learner-data/` directory. Repository validation rejects tracked
    learner artifacts outside maintained examples, fixtures, and templates.
11. Backup creation rejects output inside the source tree, writes through a
    temporary archive, and hashes streams in chunks. Verification and restore
    enforce member-count, member-size, total-size, and metadata limits. Restore
    stages the full destination and swaps it only after successful extraction.
12. Operational checks exercise ratchet serialization only in a temporary copy.
    Session checkpoints, resume, and stale-session archival coordinate through
    a shared session lock and revalidate state immediately before moving data.
    Stale file locks are reclaimed only when their recorded owner is no longer
    alive.
13. English CLI examples are corrected, the Chinese workflow passes the strategy
    library, and both languages document the same runtime and security contract.
14. HTML extraction uses `html.parser` instead of regex tag filtering, addressing
    the two production CodeQL alerts. Any remaining test-only alert is reviewed
    against its non-network sink before dismissal.

## Compatibility

- Python remains 3.10 through 3.13 with no mandatory third-party dependency.
- Existing public CLI names remain valid; stricter evidence and archive checks
  fail closed with actionable errors.
- `examlex/` is canonical runtime content and `skills/examlex/` remains its exact
  generated mirror.
- English and Chinese maintained documentation stay aligned. Neither README may
  contain a Roadmap heading or link.

## Verification

Each behavior change follows red-green TDD. Completion requires the full unit
suite, repository validator, mirror check, whitespace check, source and wheel
builds, isolated wheel smoke tests, secret scan, and successful CI/CodeQL checks
on the exact commit merged to `master`.
