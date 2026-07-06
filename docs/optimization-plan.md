# Optimization Plan

This roadmap captures planned work from the external optimization specification. Keep README claims limited to implemented commands; use this file for staged future work.

## Implemented In This Repository

- Agent Skill invocation for Codex, Claude Code, Codex App, and Cursor.
- Short terminal wrappers: `bin/tutor` and `bin/tutor.ps1`.
- Core learning loop: profile validation, constrained daily plan, practice logging, error attribution, summaries, ability updates, trends, writing versions, and writing scoring.
- Strategy library basics: ingest text strategies, list/search strategies, and validate a strategy library.
- Local data backup and restore.

## Next Priorities

1. Add TEM-4 and TEM-8 support behind tests before advertising them as supported.
2. Add vocabulary-size estimation with a checked reference word pool.
3. Add timed-practice metadata and spaced-review scheduling.
4. Add progress visualization as generated HTML.
5. Add sample essay library and reference-anchored writing scoring.

## Rule

Do not add README feature claims until the command, script, and tests exist.
