# ExamLex Release Readiness Design

## Context

The project is being renamed to **ExamLex** before its first publication. Because it has not been released and has no configured Git remote, the rename is a hard cutover: no legacy distribution names, commands, Python imports, Agent Skill directories, configuration prefixes, or compatibility aliases will remain.

Core source-tree tests pass, but the local installation and release paths are inconsistent:

- the importable package does not contain the data files required by its default CLI behavior;
- wrapper command names and installed console commands differ;
- documentation contains unusable remote-install placeholders and deprecated configuration variables;
- CI does not test the built wheel;
- three incomplete sessions older than 24 hours remain in the legacy local operational directory.

The repair must preserve the public-safe prompt policy, the eight assistant roles, and the user's changes under `_research`.

## Goals

1. Rename the complete product identity to ExamLex without a compatibility layer.
2. Make both editable installs and built wheels include every runtime resource needed by the standalone CLI.
3. Make the `examlex` CLI expose all documented commands.
4. Make all English and Chinese installation/configuration documentation truthful for an unpublished local project.
5. Make CI validate the artifact users actually install.
6. Provide a safe, reversible way to remove stale sessions from active operational checks and archive the three existing stale sessions.

## Non-goals

- Publishing the project or inventing a GitHub repository address.
- Preserving aliases or migration shims for the previous unpublished name.
- Reconstructing or changing private tutor prompt bodies.
- Installing optional external media tools such as ffmpeg, yt-dlp, Whisper, Poppler, or Calibre.
- Refactoring the learning pipeline or changing its data formats.
- Modifying or cleaning the dirty `_research` repositories.
- Renaming the outer workspace checkout directory, which is not part of the product's tracked interface.

## Naming Contract

The final repository uses these names consistently:

- Product and documentation title: `ExamLex`.
- Python distribution: `examlex`.
- Python import package: `examlex`.
- Console command: `examlex`.
- Main Agent Skill: `skills/examlex` with Skill name `examlex`.
- Local application-data directory: `ExamLex`.
- Tool configuration table: `[tool.examlex]`.
- Environment prefix for future product-specific variables: `EXAMLEX_`.

After the hard cutover, repository validation will reject occurrences of the previous product identifiers outside Git history.

## Chosen Architecture

Keep two explicit deliverables with one-way mirroring:

- `skills/examlex/` is the Agent Skill source, containing `SKILL.md`, references, scripts, templates, schemas, and data.
- `examlex/` is the importable Python package, containing `__init__.py`, `__main__.py`, `cli.py`, mirrored scripts, `SKILL.md`, and mirrored assets.

`skills/examlex` remains authoritative for shared scripts and resources because platform installers consume that directory directly. A renamed `sync_mirror.py` implementation copies managed Python files and resources into `examlex` and supports a strict check mode. This is less invasive than generating an Agent Skill during installation and more reliable than installing resources through global `data_files` paths.

Shortcut Skills retain their own names, but their routing text points to the `examlex` main Skill.

## Packaging and Resource Flow

The mirror tool will copy:

- all Python files below `skills/examlex/scripts/` into `examlex/scripts/`;
- `skills/examlex/cli.py` into `examlex/cli.py`;
- `skills/examlex/SKILL.md` into `examlex/SKILL.md`;
- the complete `skills/examlex/assets/` tree into `examlex/assets/`.

Resource copying preserves relative paths and bytes. Check mode reports missing, changed, and extra managed files so stale package data cannot silently survive.

`pyproject.toml` will discover only `examlex*` packages and declare package data for `examlex`. The built wheel must contain:

- `examlex/SKILL.md`;
- `examlex/assets/data/**`;
- `examlex/assets/schemas/**`;
- `examlex/assets/templates/**`.

The default vocabulary reference continues to resolve relative to the importable package. No source-checkout fallback will conceal a broken artifact.

## CLI Contract

The single installed console entry point is:

- `examlex = "examlex.cli:main"`.

The CLI program name, help text, wrapper names, documentation, and module execution examples use `examlex`. The alias table includes concise names:

- `vocab` -> `vocab-estimate`;
- `report` -> `visualize`;
- `validate` -> `validate-strategies`;
- `commit` -> `commit-strategies`.

Existing domain aliases such as `check`, `plan`, `log`, `errors`, and `score` remain supported. Commands based on the previous product name are removed.

## Documentation and Configuration

All placeholder repository URLs, remote badges, and remote installation commands will be removed. Documentation states that ExamLex is currently unpublished and provides local-checkout installation commands only.

`.env.example` documents only variables actually consumed by the repository:

- `SILICONFLOW_API_KEY`, consumed by `TutorConfig`;
- `EXAMLEX_PYTHON`, consumed by shell wrappers.

Python does not automatically load `.env`; users must export variables in their shell or use downstream tooling that loads the file. Claims about deprecated product-prefixed variables, `.env` priority, and user-home JSON configuration loading will be removed.

All root documents, English and Chinese guides, integration adapters, installers, examples, test fixtures, metadata, and comments will use ExamLex naming. The public-safe validation policy and placeholder prompt identifiers remain unchanged.

## CI Artifact Verification

CI retains repository validation and the complete unittest suite, then:

1. installs the standard `build` frontend;
2. builds sdist and wheel artifacts;
3. creates an isolated virtual environment;
4. installs the wheel without using the source tree;
5. runs `examlex --help`;
6. runs `examlex vocab --interactive` and parses its JSON output;
7. verifies expected package resources are present;
8. scans tracked files for forbidden legacy product identifiers.

The smoke test runs from a directory outside the checkout so source files cannot mask missing wheel contents.

## Stale Session Cleanup and Data-Directory Cutover

`TutorConfig.sessions_root` changes to the platform-appropriate `ExamLex/sessions` directory. A new deterministic cleanup module and CLI command scan either this default or a caller-supplied `--sessions-root` for `pipeline_state.json` files.

A session is stale when:

- `updated_at` is valid and older than the configured threshold, defaulting to 24 hours; and
- `stage` is neither `committed` nor `failed`.

The command is `examlex sessions-cleanup`. It defaults to dry-run output. `--apply` moves each stale session directory to a sibling `session-archive/` tree while preserving its date directory and session ID. Existing archive targets cause a clear error instead of overwrite. Empty date directories are removed after successful moves.

The cleanup command never follows an `artifacts_dir` value from JSON; it operates only on the discovered state file's parent beneath the supplied sessions root. Archiving removes stale sessions from active health checks while preserving recovery data.

After implementation:

1. run a dry-run against the legacy sessions root;
2. archive its three currently stale sessions with `--apply`;
3. run the operational check against the new ExamLex default directory;
4. confirm the legacy active directory contains no stale session state files.

## Error Handling and Safety

- Resource sync reports filesystem errors and returns non-zero in check mode.
- CLI aliases delegate to existing parsers, so validation remains centralized.
- Wheel smoke tests fail on missing files, invalid JSON, or an absent console script.
- Session cleanup validates that discovered and target paths remain beneath their intended roots.
- Session cleanup never overwrites archives and performs no deletion of session contents.
- The cleanup command prints a structured summary of candidates, archived sessions, and failures.
- The rename does not stage or modify `_research` paths.

## Testing Strategy

Implementation follows red-green-refactor cycles:

1. Add failing naming-contract tests, then rename the distribution, package imports, Skill directory, metadata, and documents.
2. Add failing mirror/package-resource tests, then add resource mirroring and package-data configuration.
3. Add failing CLI alias and entry-point tests, then add the `examlex` entry point and aliases.
4. Add failing documentation/config consistency checks, then update English and Chinese documentation.
5. Add failing session cleanup tests covering dry-run, archive, terminal stages, malformed timestamps, explicit roots, and collision protection, then implement cleanup.
6. Add CI wheel smoke commands and reproduce them locally against a clean built wheel.

Final verification requires:

- `python scripts\validate_repo.py --root . --json`;
- `python -m unittest discover -s tests`;
- `python -m compileall -q examlex scripts tests`;
- `python -m build`;
- isolated wheel installation and `examlex` CLI smoke tests;
- an identifier scan showing no forbidden legacy names;
- `examlex ops-check` showing no stale sessions after archival;
- `git diff --check` and confirmation that `_research` changes are untouched.
