# Python 3.10-3.13 Compatibility Design

## Goal

Continuously verify that ExamLex installs, tests, builds, and runs its packaged CLI on Python 3.10, 3.11, 3.12, and 3.13 on both Ubuntu and Windows.

## Scope

The CI matrix will contain eight combinations:

- Ubuntu with Python 3.10, 3.11, 3.12, and 3.13.
- Windows with Python 3.10, 3.11, 3.12, and 3.13.

Every combination will run the existing repository validation, full unit test suite, distribution build, isolated wheel smoke test, and whitespace check. Matrix fail-fast remains disabled so one failure does not hide results from other versions.

The package requirement remains `Python >=3.10`. Existing installation documentation already communicates this requirement, so documentation wording changes are not needed unless verification reveals a version-specific prerequisite.

## Implementation

1. Extend `.github/workflows/ci.yml` with Python 3.11 and 3.13.
2. Extend the workflow regression test to require exactly Python 3.10 through 3.13 and both supported runner families.
3. Run the full test suite locally with Python 3.11 and 3.13. Retain the already verified Python 3.10.11 and 3.12 results, and rerun relevant checks after any compatibility fix.
4. Run repository validation, thin-package consistency, package build, isolated wheel smoke testing, and whitespace validation.
5. Push `master` and require all eight CI jobs plus CodeQL to complete successfully.

## Compatibility Handling

If a version-specific failure occurs, the fix must preserve behavior on the other supported versions and include a regression test where practical. Tests must not rely on APIs absent from the declared minimum Python version. Environment-dependent tests should isolate the behavior under test instead of invoking unrelated network, disk, or scheduler checks.

## Acceptance Criteria

- The CI workflow visibly contains all eight operating-system and Python-version combinations.
- All eight CI jobs pass on GitHub Actions.
- CodeQL passes for the same pushed commit.
- `python scripts/validate_repo.py --root . --json` reports no errors or warnings.
- `python skills/examlex/scripts/sync_mirror.py --check` reports that the thin compatibility package is clean.
- Distribution build and isolated wheel smoke test succeed.
- The working tree is clean after the final push.
