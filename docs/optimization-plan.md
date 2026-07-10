# Optimization Plan

This roadmap records implemented optimization work and the remaining release priorities. Keep README claims limited to commands that exist and are covered by tests.

## Implemented In This Repository

- Agent Skill invocation for Codex, Claude Code, Codex App, and Cursor.
- Short terminal wrappers: `bin/examlex` and `bin/examlex.ps1`.
- Core learning loop: profile validation, constrained daily plans, practice logging, error attribution, summaries, ability updates, trends, writing versions, and writing scoring.
- Strategy library basics: ingest text strategies, list or search strategies, and validate a strategy library.
- Local data backup and restore.
- Vocabulary-size estimation with packaged reference data.
- Timed-practice metadata and spaced-review scheduling.
- Generated HTML progress visualization.
- Sample essays, writing references, and packaged runtime resources.
- Safe stale-session archival and operational readiness checks.

## Next Priorities

1. Deepen TEM-4 and TEM-8 workflow examples and regression coverage.
2. Complete the offline English and Simplified-Chinese documentation contract.
3. Prepare the first public release checklist and version decision.
4. Add optional coverage reporting without making it a runtime dependency.
5. Expand local-only example workflows for different learner foundations.

## Rule

Do not add README feature claims until the command, script, and tests exist.
