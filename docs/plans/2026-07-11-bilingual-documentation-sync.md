# Bilingual Documentation Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the English README and every maintained English/Chinese documentation pair onto the same current ExamLex feature, installation, dependency, CLI, and continuous-learning baseline.

**Architecture:** Treat executable commands, public repository URLs, dependency URLs, platform paths, data fields, and workflow stages as language-neutral invariants. Synchronize prose around those invariants, then enforce the most drift-prone README contract with regression tests while retaining the repository's existing link and bilingual-coverage validator.

**Tech Stack:** Markdown, Python `unittest`, repository validator, PowerShell-compatible command examples.

## Global Constraints

- Preserve public-safe mode and all eight tutor role placeholders.
- Do not add `README.md` or `INSTALL.md` under `skills/examlex/`.
- Keep all commands PowerShell-friendly and retain official URLs for yt-dlp, FFmpeg, Whisper, Poppler, and Calibre.
- Keep `skills/examlex/` and `examlex/` mirrors synchronized.
- Do not publish `docs/superpowers` or modify `_research`.

---

### Task 1: Establish the bilingual parity contract

**Files:**
- Modify: `tests/test_validate_project.py`

- [x] Add assertions that both READMEs contain the current installation verification, supported Python matrix, workflow stages, data model, design principles, backup/report commands, and official dependency links.
- [x] Run the focused tests and confirm they fail against the stale English README.

### Task 2: Synchronize the English README

**Files:**
- Modify: `README.md`

- [x] Translate and adapt every current Chinese README section missing from English.
- [x] Preserve English-relative links and executable command spelling.
- [x] Run the focused README contract and link validation tests.

### Task 3: Synchronize remaining stale bilingual pairs

**Files:**
- Modify as required: `cli-reference.md`, `zh-CN/cli-reference.md`
- Modify as required: `docs/*.md`, `zh-CN/docs/*.md`
- Modify as required: `skills/examlex/references/*.md`, `zh-CN/skill/references/*.md`
- Modify as required: `integrations/*/README.md`, `zh-CN/integrations/*.md`

- [x] Audit paired files for current commands, fields, workflow stages, dependencies, and links.
- [x] Bring the lagging language in each materially stale pair to the authoritative current content.
- [x] Confirm all maintained English and Chinese counterparts exist and all relative links resolve.

### Task 4: Verify, commit, push, and inspect GitHub Actions

**Files:**
- Modify: `CHANGELOG.md`

- [ ] Add a concise unreleased documentation-sync entry.
- [x] Run all 333 unit tests, repository validation, mirror check, and `git diff --check`.
- [ ] Commit the synchronized documentation on `master` and push `origin/master`.
- [ ] Confirm the resulting CI and CodeQL runs reach successful terminal states.
