# Python 3.10-3.13 Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify ExamLex on Python 3.10, 3.11, 3.12, and 3.13 across Ubuntu and Windows in every CI run.

**Architecture:** Keep the existing single GitHub Actions matrix and extend its Python axis from two versions to four. Protect the matrix contract with a repository test, then validate the added interpreters locally before using GitHub Actions as the authoritative cross-platform check.

**Tech Stack:** Python `unittest`, GitHub Actions YAML, `actions/setup-python`, Python packaging via `build`.

## Global Constraints

- Supported Python versions are exactly 3.10, 3.11, 3.12, and 3.13.
- Supported GitHub runners are exactly `ubuntu-latest` and `windows-latest`.
- Every matrix combination runs repository validation, the full unit test suite, package build, isolated wheel smoke testing, and whitespace validation.
- Keep `strategy.fail-fast: false`.
- Keep `requires-python = ">=3.10"` and the existing Python 3.10+ documentation wording.
- Do not restore or publish `docs/superpowers`.

---

### Task 1: Protect and extend the CI compatibility matrix

**Files:**
- Modify: `tests/test_validate_project.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: the existing workflow matrix keys `matrix.os` and `matrix.python-version`.
- Produces: eight CI combinations and a regression test that requires the two operating systems and four Python versions.

- [ ] **Step 1: Write the failing workflow matrix test**

Add this method to `ValidateProjectTests` in `tests/test_validate_project.py`:

```python
def test_ci_covers_supported_python_versions_and_platforms(self):
    ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    self.assertIn("os: [ubuntu-latest, windows-latest]", ci)
    self.assertIn(
        'python-version: ["3.10", "3.11", "3.12", "3.13"]',
        ci,
    )
    self.assertIn("fail-fast: false", ci)
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
python -m unittest tests.test_validate_project.ValidateProjectTests.test_ci_covers_supported_python_versions_and_platforms -v
```

Expected: `FAIL` because `.github/workflows/ci.yml` does not yet contain Python 3.11 and 3.13.

- [ ] **Step 3: Extend the workflow matrix**

Change the matrix in `.github/workflows/ci.yml` to:

```yaml
matrix:
  os: [ubuntu-latest, windows-latest]
  python-version: ["3.10", "3.11", "3.12", "3.13"]
```

Keep the existing workflow steps and `fail-fast: false` unchanged.

- [ ] **Step 4: Run the test and verify GREEN**

Run:

```powershell
python -m unittest tests.test_validate_project.ValidateProjectTests.test_ci_covers_supported_python_versions_and_platforms -v
```

Expected: `OK` with one passing test.

- [ ] **Step 5: Commit the matrix change**

```powershell
git add .github/workflows/ci.yml tests/test_validate_project.py
git commit -m "ci: test Python 3.10 through 3.13"
```

---

### Task 2: Verify the added Python interpreters

**Files:**
- Modify only if a version-specific regression is discovered: the failing source file, its authoritative counterpart under `skills/examlex/`, and the focused regression test.

**Interfaces:**
- Consumes: the package contract `requires-python = ">=3.10"`.
- Produces: passing full test suites on Python 3.11 and Python 3.13 without weakening Python 3.10 or 3.12 behavior.

- [ ] **Step 1: Provision and run Python 3.11 tests**

Run:

```powershell
uv run --python 3.11 python -m unittest discover -s tests
```

Expected: all discovered tests pass. If a failure occurs, capture the full traceback, add a focused failing regression test, make the minimal cross-version fix in `skills/examlex/`, run `python skills\examlex\scripts\sync_mirror.py`, and rerun this command.

- [ ] **Step 2: Provision and run Python 3.13 tests**

Run:

```powershell
uv run --python 3.13 python -m unittest discover -s tests
```

Expected: all discovered tests pass. Handle any failure with the same test-first and mirror-sync sequence described in Step 1.

- [ ] **Step 3: Recheck the minimum and baseline versions after any source fix**

If Task 2 changed production code, run:

```powershell
uv run --python 3.10.11 python -m unittest discover -s tests
python -m unittest discover -s tests
```

Expected: all tests pass on Python 3.10.11 and the local Python 3.12 interpreter.

- [ ] **Step 4: Commit any compatibility fix**

If Task 2 changed files, stage only the focused source, synchronized mirror, and regression test, then run:

```powershell
git commit -m "fix: support Python 3.11 and 3.13"
```

If no files changed, skip this commit.

---

### Task 3: Validate packaging and remote matrix results

**Files:**
- Verify: `pyproject.toml`
- Verify: `.github/workflows/ci.yml`
- Verify: package contents under `examlex/` and `skills/examlex/`

**Interfaces:**
- Consumes: the completed matrix and any compatibility fixes.
- Produces: validated source, synchronized mirrors, build artifacts, a smoke-tested wheel, eight successful CI jobs, and successful CodeQL.

- [ ] **Step 1: Run repository and mirror validation**

```powershell
python scripts\validate_repo.py --root . --json
python skills\examlex\scripts\sync_mirror.py --check
```

Expected: repository validation returns `"ok": true` with no errors or warnings; mirror check prints `Mirror is in sync.`

- [ ] **Step 2: Build and smoke-test the distribution**

```powershell
python -m build
python scripts\smoke_test_wheel.py dist
```

Expected: both sdist and wheel build successfully; smoke output reports `"console_help": true` and a packaged vocabulary resource.

- [ ] **Step 3: Check whitespace and repository state**

```powershell
git diff --check
git status --short --branch
```

Expected: no whitespace errors and no unstaged source changes.

- [ ] **Step 4: Push master**

```powershell
git push origin master
```

Expected: the remote `master` advances to the local commit.

- [ ] **Step 5: Monitor GitHub Actions**

Inspect the CI run for the pushed commit and require these eight jobs to conclude with `success`:

```text
Python 3.10 on ubuntu-latest
Python 3.11 on ubuntu-latest
Python 3.12 on ubuntu-latest
Python 3.13 on ubuntu-latest
Python 3.10 on windows-latest
Python 3.11 on windows-latest
Python 3.12 on windows-latest
Python 3.13 on windows-latest
```

Expected: all eight jobs and CodeQL conclude with `success`. If any job fails, download its authenticated Actions log, identify the exact traceback, add a focused regression test, apply the minimal fix, rerun local verification, push, and monitor the replacement runs.
