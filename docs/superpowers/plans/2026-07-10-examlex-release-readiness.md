# ExamLex Release Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hard-rename the unpublished project to ExamLex and make its local install, wheel, CLI, documentation, CI, and operational session state release-ready.

**Architecture:** `skills/examlex` remains the authoritative Agent Skill while `examlex` is the importable Python package. A strict mirror tool copies shared scripts and runtime assets from the Skill into the package, setuptools embeds those resources in the wheel, and CI installs the wheel outside the checkout before exercising the CLI.

**Tech Stack:** Python 3.10+, argparse, setuptools/pyproject.toml, unittest, GitHub Actions, PowerShell and POSIX shell wrappers.

## Global Constraints

- Product name is `ExamLex`; distribution, import package, CLI, and Skill name are `examlex`.
- Do not retain compatibility aliases for previous unpublished product identifiers.
- Preserve public-safe mode, eight assistant roles, and private prompt placeholders.
- Keep generated `.task8-test-tmp/`, `.tmp-test/`, `dist/`, and `test-artifacts/` untracked.
- Do not modify or stage `_research` paths.
- Use PowerShell-friendly commands in documentation.

---

### Task 1: Lock the ExamLex naming contract with failing tests

**Files:**
- Modify: `tests/test_validate_project.py`
- Modify: `tests/test_cli.py`
- Modify: `scripts/validate_repo.py`

**Interfaces:**
- Consumes: `validate_repo.validate_project(root: Path) -> ValidationResult`.
- Produces: validation rules for `examlex`, `skills/examlex`, `[tool.examlex]`, and forbidden legacy identifiers.

- [ ] **Step 1: Write failing naming-contract tests**

```python
def test_current_repo_uses_examlex_identity(self):
    result = validate_repo.validate_project(PROJECT_ROOT)
    self.assertEqual([], result.errors)
    self.assertTrue((PROJECT_ROOT / "examlex" / "__init__.py").is_file())
    self.assertTrue((PROJECT_ROOT / "skills" / "examlex" / "SKILL.md").is_file())

def test_legacy_product_identifiers_are_rejected(self):
    with copy_project() as temp:
        root = Path(temp) / "repo"
        legacy = "english" + "-exam-ai-tutor"
        (root / "legacy.txt").write_text(legacy, encoding="utf-8")
        result = validate_repo.validate_project(root)
        self.assertTrue(any("legacy product identifier" in e for e in result.errors))
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run: `python -m unittest tests.test_validate_project tests.test_cli -v`

Expected: FAIL because `examlex/` and `skills/examlex/` do not exist and current metadata still uses the previous name.

- [ ] **Step 3: Update repository validation constants and rules**

```python
SKILL_NAME = "examlex"
IMPORTABLE_NAME = "examlex"
LEGACY_IDENTIFIERS = (
    "english" + "-exam-ai-tutor",
    "english" + "_exam_ai_tutor",
    "english" + "-exam-tutor",
    "ENGLISH" + "_EXAM_TUTOR",
)
```

Scan tracked public text files and add a validation error for each forbidden identifier.

- [ ] **Step 4: Keep the tests red until the filesystem rename is complete**

Run: `python -m unittest tests.test_validate_project tests.test_cli -v`

Expected: naming tests still fail for missing ExamLex paths, proving the test detects the pending rename.

### Task 2: Hard-rename packages, Skill, wrappers, imports, and metadata

**Files:**
- Move: the current hyphenated main Skill directory under `skills/` -> `skills/examlex/`
- Move: the current underscored import package under `skills/` -> `examlex/`
- Move: `bin/tutor` -> `bin/examlex`
- Move: `bin/tutor.ps1` -> `bin/examlex.ps1`
- Modify: `pyproject.toml`
- Modify: all tracked Python imports, paths, metadata, Skill routing text, and product-title text.
- Test: `tests/test_validate_project.py`
- Test: `tests/test_install_scripts.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: importable `examlex` package, main Skill at `skills/examlex`, console script `examlex`.

- [ ] **Step 1: Move the three tracked deliverables**

Use verified workspace-contained moves for the two directories and two wrapper files. Do not move the outer checkout directory.

- [ ] **Step 2: Apply exact mechanical identifier replacements**

Apply these replacements across tracked UTF-8 text files:

```text
English + Exam + AI + Tutor product title -> ExamLex
legacy hyphenated main Skill identifier -> examlex
legacy underscored import identifier -> examlex
legacy short console identifier -> examlex
legacy uppercase environment prefix -> EXAMLEX
TUTOR_PYTHON -> EXAMLEX_PYTHON
```

- [ ] **Step 3: Configure the distribution and package discovery**

```toml
[project]
name = "examlex"

[project.scripts]
examlex = "examlex.cli:main"

[tool.setuptools.packages.find]
include = ["examlex*"]

[tool.examlex]
skill-path = "skills/examlex"
prompt-mode = "public-safe"
```

- [ ] **Step 4: Update tests and installer expectations to ExamLex paths**

All direct imports use `examlex`; all Skill filesystem fixtures use `skills/examlex`; installer targets are named `examlex`.

- [ ] **Step 5: Run the naming and installer tests and verify GREEN**

Run: `python -m unittest tests.test_validate_project tests.test_install_scripts tests.test_cli -v`

Expected: PASS.

- [ ] **Step 6: Commit the hard rename**

```powershell
git add -- examlex skills scripts tests bin pyproject.toml *.md docs zh-CN integrations
git commit -m "refactor: rename project to ExamLex"
```

### Task 3: Package runtime resources and enforce mirror integrity

**Files:**
- Modify: `skills/examlex/scripts/sync_mirror.py`
- Sync: `examlex/scripts/sync_mirror.py`
- Create by sync: `examlex/assets/**`
- Modify: `pyproject.toml`
- Modify: `tests/test_validate_project.py`
- Modify: `tests/test_estimate_vocabulary.py`

**Interfaces:**
- Produces: `sync_resources(check_only: bool = False) -> list[str]` and a wheel containing `examlex/assets/**`.

- [ ] **Step 1: Add failing resource tests**

```python
def test_importable_package_contains_default_vocab_reference(self):
    from examlex.scripts.estimate_vocabulary import _DEFAULT_REF
    self.assertTrue(_DEFAULT_REF.is_file())

def test_resource_mirror_detects_changed_asset(self):
    package_asset.write_text("changed", encoding="utf-8")
    self.assertNotEqual([], sync_resources(check_only=True))
```

- [ ] **Step 2: Run resource tests and verify RED**

Run: `python -m unittest tests.test_estimate_vocabulary tests.test_validate_project -v`

Expected: FAIL because `examlex/assets/data/vocab-test-words.json` is missing.

- [ ] **Step 3: Implement strict resource mirroring**

Mirror `SKILL.md` and all regular files beneath `assets/`, compare file bytes, report extra managed package files, and use `shutil.copy2` for binary-safe copying.

- [ ] **Step 4: Declare package data**

```toml
[tool.setuptools.package-data]
examlex = ["SKILL.md", "assets/**/*"]
```

- [ ] **Step 5: Run the mirror, then verify GREEN**

Run: `python skills\examlex\scripts\sync_mirror.py`

Run: `python -m unittest tests.test_estimate_vocabulary tests.test_validate_project -v`

Expected: PASS.

### Task 4: Align the ExamLex CLI and wrappers

**Files:**
- Modify: `skills/examlex/cli.py`
- Sync: `examlex/cli.py`
- Modify: `bin/examlex`
- Modify: `bin/examlex.ps1`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_install_scripts.py`

**Interfaces:**
- Produces CLI aliases `vocab`, `report`, `validate`, and `commit`.

- [ ] **Step 1: Add failing alias tests**

```python
def test_documented_short_aliases_are_registered(self):
    for alias in ("vocab", "report", "validate", "commit"):
        self.assertIn(alias, cli.ALL_COMMANDS)
```

- [ ] **Step 2: Run CLI tests and verify RED**

Run: `python -m unittest tests.test_cli -v`

Expected: FAIL because the four aliases are absent.

- [ ] **Step 3: Add the minimal aliases and ExamLex program name**

```python
"vocab": ("vocab-estimate", lambda args: list(args or [])),
"report": ("visualize", lambda args: list(args or [])),
"validate": ("validate-strategies", lambda args: list(args or [])),
"commit": ("commit-strategies", lambda args: list(args or [])),
```

Set `argparse.ArgumentParser(prog="examlex")` and update both wrappers to invoke `python -m examlex` using `EXAMLEX_PYTHON`.

- [ ] **Step 4: Sync and verify GREEN**

Run: `python skills\examlex\scripts\sync_mirror.py`

Run: `python -m unittest tests.test_cli tests.test_install_scripts -v`

Expected: PASS.

### Task 5: Correct unpublished installation and configuration documentation

**Files:**
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `zh-CN/README.md`
- Modify: `docs/configuration.md`
- Modify: `zh-CN/docs/configuration.md`
- Modify: `docs/getting-started.md`
- Modify: `zh-CN/docs/getting-started.md`
- Modify: `integrations/**`
- Modify: remaining tracked documentation and metadata containing old identifiers or remote placeholders.
- Modify: `tests/test_validate_project.py`

**Interfaces:**
- Produces truthful local-only installation instructions and a validator-enforced documentation contract.

- [ ] **Step 1: Add failing documentation checks**

Require no `your-org`, no remote clone command, no deprecated product-prefixed variables, and an explicit `unpublished`/`尚未发布` notice in the main READMEs.

- [ ] **Step 2: Run validation tests and verify RED**

Run: `python -m unittest tests.test_validate_project -v`

Expected: FAIL on current placeholders and configuration drift.

- [ ] **Step 3: Replace documentation with local-checkout workflows**

Document `python -m pip install -e .`, `examlex --help`, and local installer scripts. Remove CI/CodeQL remote badges until a real repository exists.

- [ ] **Step 4: Replace `.env.example`**

```dotenv
# ExamLex does not automatically load this file.
SILICONFLOW_API_KEY=
EXAMLEX_PYTHON=python
```

- [ ] **Step 5: Run validation tests and verify GREEN**

Run: `python -m unittest tests.test_validate_project -v`

Expected: PASS.

### Task 6: Add safe stale-session archival

**Files:**
- Create: `skills/examlex/scripts/cleanup_sessions.py`
- Sync: `examlex/scripts/cleanup_sessions.py`
- Modify: `skills/examlex/cli.py`
- Sync: `examlex/cli.py`
- Modify: `skills/examlex/scripts/config.py`
- Sync: `examlex/scripts/config.py`
- Create: `tests/test_cleanup_sessions.py`

**Interfaces:**
- Produces: `find_stale_sessions(sessions_root: Path, older_than_hours: float, now: datetime | None = None) -> list[StaleSession]`.
- Produces: `archive_stale_sessions(candidates: list[StaleSession], sessions_root: Path, archive_root: Path) -> CleanupResult`.
- Produces CLI command `examlex sessions-cleanup [--sessions-root PATH] [--older-than-hours 24] [--apply]`.

- [ ] **Step 1: Write failing cleanup tests**

Cover dry-run non-mutation, stale `init`/`extract` detection, exclusion of `committed`/`failed`, malformed timestamps, explicit root selection, archive collision refusal, and preservation of session files.

- [ ] **Step 2: Run cleanup tests and verify RED**

Run: `python -m unittest tests.test_cleanup_sessions -v`

Expected: import failure because the cleanup module does not exist.

- [ ] **Step 3: Implement discovery and archival**

Use state-file parent paths only, resolve and validate source/target containment, move with `shutil.move`, never overwrite an archive, and remove only empty date directories.

- [ ] **Step 4: Register the command and rename default data paths**

Default session roots use `ExamLex/sessions` on every platform. `--sessions-root` accepts the legacy operational root for the one-time archival.

- [ ] **Step 5: Sync and verify GREEN**

Run: `python skills\examlex\scripts\sync_mirror.py`

Run: `python -m unittest tests.test_cleanup_sessions tests.test_ops tests.test_session -v`

Expected: PASS.

### Task 7: Add CI wheel and identity smoke tests

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `scripts/smoke_test_wheel.py`
- Create: `tests/test_wheel_smoke_script.py`

**Interfaces:**
- Produces: `python scripts/smoke_test_wheel.py dist/examlex-0.1.0-py3-none-any.whl` returning zero only when resources, console entry point, and vocabulary JSON output work from an isolated install.

- [ ] **Step 1: Add a failing smoke-script test**

Test that the script rejects a wheel without `examlex/assets/data/vocab-test-words.json` and accepts the built ExamLex wheel.

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m unittest tests.test_wheel_smoke_script -v`

Expected: FAIL because the script does not exist.

- [ ] **Step 3: Implement the smoke script and CI steps**

CI installs `build`, runs `python -m build`, then invokes the smoke script on the generated wheel. The script creates a temporary venv, installs the wheel with pip, changes to the venv's temporary directory, runs `examlex --help` and `examlex vocab --interactive`, and parses stdout as JSON.

- [ ] **Step 4: Verify GREEN locally**

Run: `python -m unittest tests.test_wheel_smoke_script -v`

Run: `python -m build`

Run: `python scripts\smoke_test_wheel.py (Get-ChildItem dist\*.whl | Select-Object -First 1).FullName`

Expected: all commands exit zero.

### Task 8: Archive legacy sessions and complete verification

**Files:**
- Operational state only: the legacy AppData sessions root and sibling archive root.
- No `_research` modifications.

**Interfaces:**
- Consumes: `examlex sessions-cleanup` and `examlex ops-check`.

- [ ] **Step 1: Preview legacy candidates**

Set `$legacyRoot = Join-Path $env:LOCALAPPDATA (('english' + '-exam-ai-tutor') + '\sessions')`, then run `python -m examlex sessions-cleanup --sessions-root $legacyRoot --older-than-hours 24` and confirm exactly three candidates.

- [ ] **Step 2: Archive the candidates**

Run `python -m examlex sessions-cleanup --sessions-root $legacyRoot --older-than-hours 24 --apply` and confirm all three move to `session-archive` without overwrite.

- [ ] **Step 3: Run complete verification**

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
python -m compileall -q examlex scripts tests
python -m build
python scripts\smoke_test_wheel.py (Get-ChildItem dist\*.whl | Select-Object -First 1).FullName
python -m examlex ops-check --json
git diff --check
```

Expected: repository validation passes, all tests pass, compilation passes, wheel smoke passes, and operational logs show zero stale sessions under the new default root.

- [ ] **Step 4: Confirm scope and commit**

Run `git status --short` and confirm `_research` entries are unchanged and unstaged. Commit only ExamLex project changes with message `feat: prepare ExamLex for local release`.
