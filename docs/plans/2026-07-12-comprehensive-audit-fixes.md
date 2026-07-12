# Comprehensive Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair every confirmed audit finding while preserving existing ExamLex CLI and vocabulary-path compatibility.

**Architecture:** Align packaged starter assets with their consumers, make installers and local persistence safe by default, and enforce bounded parsing and exact validation at trust boundaries. Keep legacy vocabulary paths as verified compatibility copies while moving maintained examples to truthful canonical names.

**Tech Stack:** Python 3.10+ standard library, `unittest`, PowerShell, POSIX shell, GitHub Actions, GitHub REST API.

## Global Constraints

- Existing CLI commands and public Python entry points remain available.
- Python 3.10 is the minimum supported interpreter; no runtime dependency is added.
- Legacy vocabulary files remain packaged and data-equivalent to canonical replacements.
- Installation overwrites only when force is explicitly supplied.
- Failed or concurrent record writes do not corrupt or silently lose valid records.

---

### Task 1: Align packaged templates with runtime contracts

**Files:**
- Modify: `examlex/assets/templates/ability-profile.yaml`
- Modify: `examlex/assets/templates/exercise-record.json`
- Modify: `examlex/assets/templates/exercise-record.yaml`
- Modify: `examlex/assets/templates/writing-version-record.yaml`
- Modify: `scripts/validate_repo.py`
- Test: `tests/test_generate_daily_plan.py`, `tests/test_record_practice.py`, `tests/test_manage_writing_versions.py`, `tests/test_validate_project.py`

**Interfaces:**
- Consumes: `generate_daily_plan._ability_candidates`, `record_practice.record_practice`, `manage_writing_versions._load_records`.
- Produces: accepted packaged templates and `validate_template_contracts(root, result)`.

- [x] **Step 1: Add failing integration tests.** Load the ability template and assert at least five non-fallback candidates; load practice and writing templates and assert each top level is a list accepted by its append command.
- [x] **Step 2: Run RED.** `python -m unittest tests.test_generate_daily_plan tests.test_record_practice tests.test_manage_writing_versions`; expect failures for string nodes and object-shaped stores.
- [x] **Step 3: Fix template shapes.** Represent every ability node as `{"node":"阅读速度","level":1,"status":"needs_work","stats":{"total_items":0,"correct_items":0,"error_count":0,"accuracy":0.0}}`; wrap practice and writing examples in arrays; remove unsupported `notes` and `next_action`.
- [x] **Step 4: Add contract validation.** Reject non-object ability nodes and non-list practice/writing templates with file-specific errors.
- [x] **Step 5: Run GREEN.** Run the four focused modules plus `python scripts/validate_repo.py --root . --json`; expect all pass and `"ok": true`.
- [x] **Step 6: Commit.** Stage the four templates, validator, and four tests; commit `fix: align starter templates with CLI contracts`.

### Task 2: Make installers truthful and non-destructive

**Files:**
- Modify: `scripts/install_cursor.py`, `install.ps1`, `install.sh`, `README.md`, `zh-CN/README.md`
- Test: `tests/test_install_scripts.py`

**Interfaces:**
- Produces: Cursor default `Path.home() / ".cursor" / "skills"`, explicit force flags, and Python 3.10 version rejection.

- [x] **Step 1: Add failing tests.** Assert the Cursor default equals `~/.cursor/skills`; PowerShell contains `[switch]$Force` and no `if (-not $NoForce)`; shell contains `force=false`; fake Python 3.9 interpreters produce `Python 3.10+ is required` and a nonzero exit.
- [x] **Step 2: Run RED.** `python -m unittest tests.test_install_scripts`; expect path, implicit-force, and version-check failures.
- [x] **Step 3: Implement safe defaults.** Append `--force` only for explicit `-Force`/`--force`; validate `sys.version_info >= (3, 10)` before invoking installer modules.
- [x] **Step 4: Correct Cursor docs and destinations.** Use `.cursor/skills` for personal/project installation in code, dry runs, and both READMEs.
- [x] **Step 5: Run GREEN.** `python -m unittest tests.test_install_scripts tests.test_validate_project`; expect all pass.
- [x] **Step 6: Commit.** Commit the wrappers, Cursor installer, READMEs, and tests as `fix: make skill installation safe by default`.

### Task 3: Publish truthful canonical vocabulary pools

**Files:**
- Create: `examlex/assets/data/vocabulary/cet4-core-200.json`, `cet6-core-150.json`, `postgraduate-core-100.json`, `tem4-core-100.json`, `tem8-core-100.json`
- Modify: `examlex/assets/data/vocabulary/index.json`, bilingual README and vocabulary documentation, `scripts/validate_repo.py`
- Test: `tests/test_vocab_pool.py`, `tests/test_validate_project.py`

**Interfaces:**
- Produces: canonical index entries containing `path`, exact `count`, `scope: "curated_starter"`, and `legacy_paths`.

- [ ] **Step 1: Add failing tests.** Parse each canonical filename's final numeric suffix and assert it equals JSON length; assert every legacy file's parsed data equals its canonical file.
- [ ] **Step 2: Run RED.** `python -m unittest tests.test_vocab_pool`; expect missing canonical paths and metadata.
- [ ] **Step 3: Create canonical copies and index.** Use keys `cet4-core`, `cet6-core`, `postgraduate-core`, `tem4-core`, `tem8-core`; preserve each old path in `legacy_paths`.
- [ ] **Step 4: Update examples and validation.** Maintained examples use canonical paths and call all 650 entries a curated starter set; validator rejects suffix/count and legacy-data mismatches.
- [ ] **Step 5: Run GREEN.** `python -m unittest tests.test_vocab_pool tests.test_validate_project`; expect canonical and legacy paths pass.
- [ ] **Step 6: Commit.** Commit data, index, docs, validator, and tests as `fix: publish truthful vocabulary pool names`.

### Task 4: Make record updates atomic and concurrency-safe

**Files:**
- Create: `examlex/scripts/file_lock.py`, `tests/test_common.py`
- Modify: `examlex/scripts/common.py`, `examlex/scripts/record_practice.py`, `examlex/scripts/manage_writing_versions.py`
- Test: `tests/test_record_practice.py`, `tests/test_manage_writing_versions.py`, `tests/test_security.py`

**Interfaces:**
- Produces: `exclusive_file_lock(target: Path, timeout_seconds=5.0, stale_after_seconds=60.0)` and `atomic_save_data(path, data)`.

- [ ] **Step 1: Add failing tests.** Patch `Path.replace` to raise and assert original JSON is unchanged; use two threads appending distinct records and assert both survive; test timeout and stale-lock recovery.
- [ ] **Step 2: Run RED.** Run the four persistence/security test modules; expect missing APIs and unsafe update failures.
- [ ] **Step 3: Implement atomic save.** Serialize first; write a unique same-directory `NamedTemporaryFile`; flush and `os.fsync`; replace target; remove an unused temporary file in `finally`.
- [ ] **Step 4: Implement bounded lock files.** Acquire `<target>.lock` with `O_CREAT|O_EXCL`, record PID/time, retry to a monotonic deadline, remove locks older than 60 seconds, and release only the acquired lock; timeout text is `Timed out waiting for file lock: <path>`.
- [ ] **Step 5: Lock read-modify-write transactions.** Practice and writing commands hold the lock from load through atomic replace and convert lock/I/O failures to one-line CLI errors.
- [ ] **Step 6: Run GREEN.** Run all persistence/security modules; expect atomicity and concurrent-append tests pass.
- [ ] **Step 7: Commit.** Commit implementation and tests as `fix: protect learner records from partial writes`.

### Task 5: Bound EPUB fallback extraction

**Files:**
- Modify: `examlex/scripts/extractors/book.py`
- Test: `tests/test_extractors/test_book_extractor.py`

**Interfaces:**
- Produces limits: 2,000 entries, 10 MiB per HTML file, 50 MiB cumulative HTML, compression ratio 100.

- [ ] **Step 1: Add failing tests.** Build small EPUBs with patched `ZipInfo` metadata and assert rejection for entry count, one uncompressed HTML size, cumulative size, and compression ratio; retain ordinary EPUB success.
- [ ] **Step 2: Run RED.** `python -m unittest tests.test_extractors.test_book_extractor`; expect unsafe cases accepted.
- [ ] **Step 3: Validate metadata before reads.** Reject negative/inconsistent sizes, excessive entry count, per-file/total HTML bytes, zero-byte compressed positive output, and ratio above 100 with actionable `ValueError` messages.
- [ ] **Step 4: Run GREEN.** Re-run the extractor module; expect normal input pass and all unsafe cases fail closed.
- [ ] **Step 5: Commit.** Commit as `fix: bound EPUB fallback extraction`.

### Task 6: Make external URL validation exact

**Files:**
- Modify: `scripts/validate_repo.py`
- Test: `tests/test_validate_project.py`

**Interfaces:**
- Produces: `extract_external_urls(text: str) -> set[str]` and exact normalized allowlist membership.

- [ ] **Step 1: Add failing bypass tests.** Place bare `https://github.com/SFEW888/ExamLex.evil.invalid` and an allowed badge URL with an appended suffix in maintained Markdown; assert both report `external URL`.
- [ ] **Step 2: Run RED.** `python -m unittest tests.test_validate_project`; expect the bare prefix bypass to be accepted incorrectly.
- [ ] **Step 3: Implement exact parsing.** Extract Markdown targets and bare HTTP(S) tokens; trim terminal Markdown punctuation; normalize only scheme/host casing with `urllib.parse.urlsplit`; compare complete values to the allowlist.
- [ ] **Step 4: Run GREEN.** Re-run validator tests; expect known badges pass and both bypasses fail.
- [ ] **Step 5: Commit.** Commit as `fix: validate external URLs by exact value`.

### Task 7: Harden CI and remove stale execution documentation

**Files:**
- Modify: `.github/workflows/ci.yml`, `.github/workflows/codeql.yml`, `tests/test_validate_project.py`
- Delete: `docs/plans/2026-07-11-python-compatibility.md`

**Interfaces:**
- Produces: least-privilege workflows pinned to immutable official commits.

- [ ] **Step 1: Add failing workflow policy tests.** Require CI top-level `permissions: contents: read`; require all `uses:` values to end in 40 hex characters; approve checkout `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0`, setup-python `ece7cb06caefa5fff74198d8649806c4678c61a1`, and CodeQL `99df26d4f13ea111d4ec1a7dddef6063f76b97e9`.
- [ ] **Step 2: Run RED.** `python -m unittest tests.test_validate_project`; expect mutable-tag and permission failures.
- [ ] **Step 3: Pin workflows.** Replace tags with approved SHAs plus version comments; add CI `permissions: contents: read`; retain CodeQL `security-events: write`.
- [ ] **Step 4: Delete stale plan.** Remove only `docs/plans/2026-07-11-python-compatibility.md`, retaining its design record.
- [ ] **Step 5: Run GREEN.** Run validator tests and repository validation; expect no errors or warnings.
- [ ] **Step 6: Commit.** Commit as `ci: enforce least privilege and immutable actions`.

### Task 8: Verify, publish, merge, and protect `master`

**Files:**
- Modify: this plan by marking executed checkboxes complete.
- Generated and ignored: `dist/`, `build/`, `test-artifacts/`.

**Interfaces:**
- Produces: merged `master`, successful checks, and verified branch protection.

- [ ] **Step 1: Run complete local verification.** Run `python -m unittest discover -s tests`, repository JSON validation, `python -m build`, wheel smoke test, and `git diff --check origin/master...HEAD`; require zero failures.
- [ ] **Step 2: Repeat security scans.** Search tracked files for nonempty credentials, private-key headers, `shell=True`, `os.system`, `eval`, `exec`, unsafe pickle, and unbounded archive reads; allow only reviewed fake fixtures and safe call sites.
- [ ] **Step 3: Complete this plan.** Change every executed checkbox to `[x]`, validate again, and commit `docs: record completed audit remediation`.
- [ ] **Step 4: Publish PR.** Push `codex/comprehensive-audit-fixes`, open a ready PR to `master`, and verify remote head SHA equals local HEAD.
- [ ] **Step 5: Merge after checks.** Require every CI matrix job and CodeQL to report `success`; merge, fetch `origin/master`, and require `git diff --quiet HEAD origin/master`.
- [ ] **Step 6: Protect `master`.** Require pull requests and observed CI/CodeQL contexts, enforce for administrators, disable force pushes/deletions, then read the API response back and assert every field.
