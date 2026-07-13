# P1/P2 Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all confirmed P1/P2 correctness, security, installation, privacy, backup, concurrency, schema, CLI, and bilingual documentation findings.

**Architecture:** Keep the current standard-library-only Python package and CLI. Add small shared primitives for canonical strategy digests, locked strategy-library mutation, bounded archive streaming, and session locking; use the existing mirror tool after canonical runtime edits.

**Tech Stack:** Python 3.10-3.13, `unittest`, JSON Schema, PowerShell/Bash wrappers, GitHub Actions.

## Global Constraints

- Do not add mandatory third-party Python dependencies.
- Keep public-safe prompt content and the eight tutor roles unchanged.
- Keep `examlex/` and `skills/examlex/` mirrored through `sync_mirror.py`.
- Keep English and Chinese documentation aligned.
- Do not restore a Roadmap section in either README.
- Write a failing regression test before each production behavior change.

---

### Task 1: Ledger, Planning, And Data Contracts

**Files:**
- Modify: `tests/test_update_ability_profile.py`
- Modify: `tests/test_generate_daily_plan.py`
- Modify: `tests/test_tem_support.py`
- Modify: `tests/test_manage_writing_versions.py`
- Modify: `tests/test_record_practice.py`
- Modify: `examlex/scripts/update_ability_profile.py`
- Modify: `examlex/scripts/generate_daily_plan.py`
- Modify: `examlex/assets/schemas/*.schema.json`
- Modify: `examlex/assets/templates/*`

**Interfaces:**
- `update_ability_profile(profile, full_ledger) -> recomputed_profile`
- `generate_daily_plan(..., vocab_pool=pool) -> plan` with a reserved vocabulary task

- [ ] Add idempotence, official-template vocabulary, TEM schema, unbounded version,
      and positive exercise-total tests.
- [ ] Run `python -m unittest tests.test_update_ability_profile tests.test_generate_daily_plan tests.test_tem_support tests.test_manage_writing_versions tests.test_record_practice` and confirm the new assertions fail for the audited reasons.
- [ ] Recompute all derived ability statistics from the supplied full ledger,
      reserve vocabulary time before ability allocation, and align schemas/templates.
- [ ] Re-run the focused tests and commit as `fix: make learner data updates deterministic`.

### Task 2: Approval Evidence And Strategy-Library Concurrency

**Files:**
- Create: `examlex/scripts/strategy_store.py`
- Modify: `examlex/scripts/common.py`
- Modify: `examlex/scripts/cli_validate.py`
- Modify: `examlex/scripts/cli_commit.py`
- Modify: `examlex/scripts/ingest_strategy.py`
- Modify: `examlex/scripts/optimizers/ratchet.py`
- Modify: `examlex/scripts/prompts/effect.py`
- Modify: `tests/test_continuous_learning_p0.py`
- Modify: `tests/test_continuous_learning_p1.py`
- Modify: `tests/test_optimizers/test_ratchet.py`

**Interfaces:**
- `canonical_json_sha256(value) -> lowercase_sha256`
- `mutate_strategy_library(path, callback) -> callback_result`

- [ ] Add tests that mutate a strategy after validation, omit or duplicate report
      digests, and race two library writers.
- [ ] Run the focused continuous-learning tests and confirm stale evidence and lost
      updates are reproduced.
- [ ] Put canonical per-strategy digests in validation/evaluation contracts, reject
      mismatches at commit, and route ingest/commit through one locked mutation.
- [ ] Re-run focused tests and commit as `fix: bind approvals and serialize strategy writes`.

### Task 3: Self-Contained Installation, Resume, Privacy, And Bilingual CLI Docs

**Files:**
- Create: `examlex/run.py`
- Modify: `examlex/cli.py`
- Modify: `examlex/scripts/session.py`
- Modify: `tests/test_install_scripts.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_validate_project.py`
- Modify: `.gitignore`
- Modify: `scripts/validate_repo.py`
- Modify: `install.sh`
- Modify: `bin/examlex`
- Modify: `README.md`, `zh-CN/README.md`, `cli-reference.md`, `zh-CN/cli-reference.md`
- Modify: maintained Skill workflow documents in both languages

**Interfaces:**
- `python run.py <command>` from the installed `examlex` Skill directory
- `examlex resume <session-id> [--sessions-root PATH] [--json]`

- [ ] Add tests for copied-Skill CLI execution, executable Git modes, resume dispatch,
      ignored learner outputs, tracked-artifact rejection, and exact bilingual examples.
- [ ] Run install/CLI/validator tests and confirm the new assertions fail.
- [ ] Add the portable runner and resume command, set Git executable bits, add privacy
      patterns and validation, and correct all bilingual command examples.
- [ ] Re-run focused tests and commit as `fix: make skill installs self contained`.

### Task 4: Extraction And Agent Trust Boundaries

**Files:**
- Modify: `examlex/scripts/cli_extract.py`
- Modify: `examlex/scripts/config.py`
- Modify: `examlex/scripts/extractors/video.py`
- Modify: `examlex/scripts/extractors/book.py`
- Modify: `examlex/scripts/prompts/base.py`
- Modify: `examlex/scripts/prompts/ria.py`
- Modify: `examlex/scripts/prompts/cognitive.py`
- Modify: `examlex/scripts/prompts/effect.py`
- Modify: `examlex/SKILL.md`
- Modify: extraction and security tests
- Modify: bilingual multi-source documentation

**Interfaces:**
- `VideoExtractor(config).extract(valid_https_platform_url, output_dir)`
- `untrusted_source_policy(allowed_artifacts) -> instructions`

- [ ] Add tests for forced-video bypass, option-like input, userinfo, HTTP/private DNS,
      `--` separation, `asr_backend=none`, local-only auto ASR, Calibre EPUB preflight,
      structured HTML parsing, and prompt-injection markers.
- [ ] Run focused extractor/security tests and confirm each audited path fails.
- [ ] Enforce validation inside the extractor, respect explicit ASR configuration,
      preflight EPUBs before Calibre, use `HTMLParser`, and include the shared trust policy.
- [ ] Re-run focused tests and commit as `fix: harden external content extraction`.

### Task 5: Backup, Operational Checks, And Session Races

**Files:**
- Modify: `examlex/scripts/backup_data.py`
- Modify: `examlex/scripts/ops.py`
- Modify: `examlex/scripts/file_lock.py`
- Modify: `examlex/scripts/session.py`
- Modify: `examlex/scripts/cleanup_sessions.py`
- Modify: `tests/test_continuous_learning_p1.py`
- Modify: `tests/test_ops.py`
- Modify: `tests/test_common.py`
- Modify: `tests/test_session.py`
- Modify: `tests/test_cleanup_sessions.py`
- Modify: `tests/test_security.py`

**Interfaces:**
- Archive verification is streaming and quota bounded.
- Restore commits a staging directory only after all members are verified and written.
- Cleanup revalidates a candidate under the same session lock used by checkpoints.

- [ ] Add tests for source-contained output, repeated backup, member quotas, streaming
      reads, failed forced restore rollback, byte-stable ops checks, live stale locks,
      and checkpoint-versus-cleanup races.
- [ ] Run focused tests and confirm the audited corruption/mutation/race paths fail.
- [ ] Implement atomic bounded backup/restore, temporary ops libraries, owner-aware stale
      locks, atomic checkpoints, and locked cleanup revalidation.
- [ ] Re-run focused tests and commit as `fix: make backup and session operations atomic`.

### Task 6: Mirror, Full Verification, And Publication

**Files:**
- Update generated mirror: `skills/examlex/**`
- Update bilingual maintained docs and regression contracts as required

- [ ] Run `python skills/examlex/scripts/sync_mirror.py` and then `--check`.
- [ ] Run `python -m unittest discover -s tests` and require zero failures.
- [ ] Run `python scripts/validate_repo.py --root . --json` and require zero errors/warnings.
- [ ] Run `git diff --check`, source/wheel builds, isolated wheel smoke, and secret scans.
- [ ] Push `codex/p1-p2-full-remediation`, open a PR, wait for exact-head CI and CodeQL,
      merge it, and verify public `master` content and commit SHA.
