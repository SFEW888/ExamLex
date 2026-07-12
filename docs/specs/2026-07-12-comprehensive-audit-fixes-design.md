# Comprehensive Audit Fixes Design

## Goal

Resolve the functional, installation, data-integrity, security, and repository-governance findings from the July 2026 full audit without breaking existing ExamLex users.

## Compatibility policy

The repair uses a compatibility-first policy:

- Existing CLI commands and public Python entry points remain available.
- Existing vocabulary filenames remain readable as deprecated compatibility copies.
- New documentation and examples use filenames whose numeric suffix matches the actual entry count.
- Installers stop before overwriting existing Skills unless the user explicitly requests `--force` or its platform-specific equivalent.
- Existing valid learner data remains readable; only malformed starter templates change shape.

## Template and CLI contracts

The ability-profile template will contain ability-node objects with `node`, `level`, `status`, and `stats`, matching the planner and documented data model. A template-driven planning test must prove that a normal time budget produces multiple prioritized tasks rather than the fallback-only plan.

Practice-ledger and writing-version templates will become top-level JSON arrays containing one example record. Their corresponding CLI tests will copy the packaged templates and append a new record successfully. Unsupported practice fields will be removed from the template unless the CLI accepts and persists them consistently.

Template validation will be added to repository validation so a future mismatch fails CI instead of remaining a runtime-only defect.

## Installer behavior

Cursor personal and project installation targets will be `~/.cursor/skills` and `.cursor/skills`, matching the bilingual README. Tests will assert the default and wrapper-selected paths.

PowerShell and POSIX wrappers will be non-destructive by default. Overwrite will require explicit `-Force` or `--force`; `-NoForce` will be retained only if needed for a short compatibility window and documented as deprecated. Installer tests will create a marker inside an existing target and prove a default invocation preserves it.

Both wrappers will query the selected interpreter and reject versions below Python 3.10 with a concise error before invoking any Python installer module.

## Vocabulary compatibility

Canonical vocabulary files will use truthful names:

- `cet4-core-200.json`
- `cet6-core-149.json` (the generator contains 149 unique entries; the previous 150-row file repeated `allege`)
- `postgraduate-core-100.json`
- `tem4-core-100.json`
- `tem8-core-100.json`

The old numeric filenames will remain packaged as deprecated compatibility copies for direct-path users. The vocabulary index will distinguish canonical pools from legacy aliases and state both included count and intended exam scope. Documentation will explicitly describe the 649 unique entries as a curated starter set, not a full exam lexicon.

Repository validation will verify that each canonical filename's numeric suffix equals the JSON entry count and that compatibility copies match their canonical source.

## File and extraction safety

EPUB fallback extraction will inspect ZIP metadata before reading content. It will reject archives that exceed explicit limits for entry count, individual uncompressed HTML size, cumulative uncompressed HTML size, or compression ratio. Tests will cover normal EPUB input and each rejection boundary without allocating oversized payloads.

Practice-ledger writes will use the same-directory temporary-file-and-replace pattern already used elsewhere in the project. Read-modify-write operations for practice ledgers and writing versions will use a cross-platform lock-file helper with bounded waiting and stale-lock handling. Tests will prove interrupted writes preserve the original file and concurrent append operations retain every record.

## Validation and CI hardening

External URL validation will parse complete Markdown links and bare URLs, then compare normalized URLs exactly against the allowlist. An allowlisted URL followed by an attacker-controlled suffix must fail validation.

GitHub workflows will declare least-privilege permissions explicitly and pin third-party actions to immutable commit SHAs with version comments. The completed Python compatibility implementation plan will be removed from maintained public documentation because its unchecked execution checklist is stale.

After the repair PR is merged and all required checks have reported on `master`, branch protection will require pull requests and the repository's CI/CodeQL checks, block force pushes and deletions, and apply to administrators. Secret scanning, push protection, and Dependabot security updates will remain enabled.

## Error handling and migration

Compatibility files and deprecated wrapper switches will not emit noisy output during ordinary use. Documentation will identify canonical vocabulary names and note that legacy names remain available temporarily.

Lock acquisition and EPUB limit failures will return actionable user-facing errors rather than tracebacks. Failed writes must leave the previously valid JSON file unchanged. Installer version and overwrite failures must explain the exact corrective option.

## Verification

Each finding receives a regression test that is observed failing before its implementation change. Completion requires:

- all focused regression tests passing;
- the complete unit-test suite passing on the local interpreter;
- repository validation returning no errors or warnings;
- source and wheel builds succeeding;
- wheel smoke testing succeeding;
- secret-pattern and dangerous-call scans remaining clean;
- the PR's CI and CodeQL checks succeeding;
- the merged `master` contents matching the reviewed commit;
- branch-protection settings being read back through the GitHub API.

## Out of scope

This repair does not attempt to create thousands of new vocabulary entries, change ExamLex scoring algorithms, add a new UI, or redesign the public CLI. Those changes require separate content-quality or product specifications.
