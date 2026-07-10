# Release Readiness Fixes Design

## Context

The project is not published and has no configured Git remote. Core source-tree tests pass, but the local installation and release paths are inconsistent:

- the importable package does not contain the data files required by its default CLI behavior;
- wrapper command names and installed console commands differ;
- documentation contains unusable remote-install placeholders and deprecated configuration variables;
- CI does not test the built wheel;
- three incomplete sessions older than 24 hours remain in the local operational directory.

The repair must preserve the public-safe prompt policy, the eight assistant roles, the existing hyphenated Agent Skill directory, and the user's changes under `_research`.

## Goals

1. Make both editable installs and built wheels include every runtime resource needed by the standalone CLI.
2. Make `tutor` and `english-exam-tutor` expose the same documented commands.
3. Make all English and Chinese installation/configuration documentation truthful for an unpublished local project.
4. Make CI validate the artifact users actually install.
5. Provide a safe, reversible way to remove stale sessions from active operational checks and archive the three existing stale sessions.

## Non-goals

- Publishing the project or inventing a GitHub repository address.
- Reconstructing or changing private tutor prompt bodies.
- Installing optional external media tools such as ffmpeg, yt-dlp, Whisper, Poppler, or Calibre.
- Refactoring the full learning pipeline or changing its data formats.
- Modifying or cleaning the dirty `_research` repositories.

## Chosen Approach

Keep the current dual-directory design and make its contract explicit:

- `skills/english-exam-ai-tutor/` remains the Agent Skill source.
- `skills/english_exam_ai_tutor/` remains the importable Python package.
- Python files, `SKILL.md`, and `assets/` are mirrored from the Agent Skill into the importable package.
- setuptools package-data configuration includes `SKILL.md` and all files under `assets/` in the wheel.
- repository validation and tests reject mirror drift.

This is less invasive than renaming the Agent Skill directory and more reliable than installing resources through global `data_files` paths.

## Packaging and Resource Flow

`sync_mirror.py` will gain resource mirroring in addition to its current Python-file mirroring. Resource copying will preserve relative paths and bytes. Check mode will report missing, changed, and extra managed resource files so stale package data cannot silently survive.

`pyproject.toml` will declare package data for `skills.english_exam_ai_tutor`. The built wheel must contain:

- `skills/english_exam_ai_tutor/SKILL.md`;
- `skills/english_exam_ai_tutor/assets/data/**`;
- `skills/english_exam_ai_tutor/assets/schemas/**`;
- `skills/english_exam_ai_tutor/assets/templates/**`.

The default `vocab-estimate --interactive` path will continue to resolve relative to the importable package. No fallback to the source checkout will be added because that would conceal broken release artifacts.

## CLI Compatibility

Both console entry points will call the same `skills.english_exam_ai_tutor.cli:main` function:

- `english-exam-tutor`;
- `tutor`.

The Python CLI alias table will include wrapper-compatible names:

- `vocab` -> `vocab-estimate`;
- `report` -> `visualize`;
- `validate` -> `validate-strategies`;
- `commit` -> `commit-strategies`.

Existing canonical commands and aliases remain supported.

## Documentation and Configuration

All `your-org/english-exam-ai-tutor` URLs, remote badges, and remote installation commands will be removed. Documentation will state that the project is currently unpublished and provide local-checkout installation commands only.

`.env.example` will document only variables actually consumed by the repository:

- `SILICONFLOW_API_KEY`, consumed by `TutorConfig`;
- `TUTOR_PYTHON`, consumed by the shell wrappers.

Documentation will explicitly state that Python does not automatically load `.env`; users must export variables in their shell or use downstream tooling that loads the file. Claims about deprecated `ENGLISH_EXAM_TUTOR_*` variables, `.env` priority, and `~/.english-exam-ai-tutor/config.json` loading will be removed.

## CI Artifact Verification

CI will retain repository validation and the complete unittest suite, then:

1. install the standard `build` frontend;
2. build sdist and wheel artifacts;
3. create an isolated virtual environment;
4. install the wheel without using the source tree;
5. run `tutor --help` and `english-exam-tutor --help`;
6. run `tutor vocab --interactive` and parse its JSON output;
7. verify expected package resources are present.

The smoke test must run from a directory outside the checkout so source files cannot mask missing wheel contents.

## Stale Session Cleanup

A new deterministic cleanup module and CLI command will scan `TutorConfig.sessions_root` for `pipeline_state.json` files. A session is stale when:

- `updated_at` is valid and older than the configured threshold, defaulting to 24 hours; and
- `stage` is neither `committed` nor `failed`.

The command will be `tutor sessions-cleanup`. It defaults to dry-run output. `--apply` moves each stale session directory to a sibling `session-archive/` tree while preserving its date directory and session ID. Existing archive targets cause a clear error instead of overwrite. Empty date directories are removed after successful moves.

Archiving, rather than deletion, removes stale sessions from active health checks while preserving recovery data. After implementation and dry-run verification, the three currently stale sessions will be archived with `--apply`.

## Error Handling and Safety

- Resource sync reports filesystem errors and returns non-zero in check mode.
- CLI aliases delegate to existing parsers, so validation remains centralized.
- Wheel smoke tests fail on missing files, invalid JSON, or absent console scripts.
- Session cleanup never follows an `artifacts_dir` value from JSON; it operates only on the discovered state file's parent beneath the configured sessions root.
- Session cleanup never overwrites archives and performs no deletion of session contents.
- The cleanup command prints a structured summary of candidates, archived sessions, and failures.

## Testing Strategy

Implementation follows red-green-refactor cycles:

1. Add failing mirror/package-resource tests, then add resource mirroring and package-data configuration.
2. Add failing CLI alias/entry-point tests, then add aliases and the `tutor` console script.
3. Add failing documentation/config consistency checks, then update English and Chinese documentation.
4. Add failing session cleanup tests covering dry-run, archive, terminal stages, malformed timestamps, and collision protection, then implement cleanup.
5. Add CI wheel smoke commands and reproduce them locally against a clean built wheel.

Final verification requires:

- `python scripts\validate_repo.py --root . --json`;
- `python -m unittest discover -s tests`;
- `python -m compileall -q skills scripts tests`;
- `python -m build`;
- isolated wheel installation and CLI smoke tests;
- `tutor ops-check` showing no stale sessions after archival;
- `git diff --check` and confirmation that `_research` changes are untouched.
