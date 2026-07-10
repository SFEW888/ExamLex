from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from .scripts import (
    analyze_trends,
    backup_data,
    cleanup_sessions,
    estimate_vocabulary,
    generate_daily_plan,
    ingest_strategy,
    list_strategies,
    manage_writing_versions,
    record_practice,
    score_writing_rubric,
    summarize_errors,
    tag_error,
    update_ability_profile,
    validate_strategy,
    validate_profile,
    visualize,
)
from .scripts.cli_extract import main as extract_main
from .scripts.cli_validate import main as validate_main
from .scripts.cli_commit import main as commit_main
from .scripts.cli_ops import main as ops_main
from .scripts.config import TutorConfig

CommandMain = Callable[[list[str] | None], int]


def _check_deps_main(argv: list[str] | None = None) -> int:
    try:
        cfg = TutorConfig()
        report = cfg.check_all_dependencies()
    except Exception as exc:
        print(f"Failed to check dependencies: {exc}", file=sys.stderr)
        return 1
    if report.all_available():
        print("All external dependencies are available.")
        return 0
    else:
        print("Dependency report:")
        print(report)
        return 1


COMMANDS: dict[str, tuple[str, CommandMain]] = {
    "validate-profile": ("Validate a learner profile.", validate_profile.main),
    "daily-plan": ("Generate a constrained daily plan.", generate_daily_plan.main),
    "record-practice": ("Append a practice record to a ledger.", record_practice.main),
    "tag-error": ("Infer deterministic error tags from observed text.", tag_error.main),
    "summarize-errors": ("Summarize error tags from a practice ledger.", summarize_errors.main),
    "update-ability": ("Update an ability profile from practice records.", update_ability_profile.main),
    "writing-version": ("Append a writing draft version.", manage_writing_versions.main),
    "score-writing": ("Score a writing draft with the deterministic rubric.", score_writing_rubric.main),
    "analyze-trends": ("Analyze practice and ability trends.", analyze_trends.main),
    "ingest-strategy": ("Ingest a strategy note into a strategy library.", ingest_strategy.main),
    "list-strategies": ("List or search strategy library entries.", list_strategies.main),
    "validate-strategy": ("Validate a strategy library file.", validate_strategy.main),
    "backup": ("Backup learner data to a tar.gz archive.", backup_data.backup_main),
    "restore": ("Restore learner data from a tar.gz archive.", backup_data.restore_main),
    "extract": ("Extract raw materials from a source (URL/file/name).", extract_main),
    "validate-strategies": ("Validate distilled strategies and score structure.", validate_main),
    "commit-strategies": ("Commit strategies to library with ratchet check.", commit_main),
    "check-deps": ("Check external tool dependencies.", _check_deps_main),
    "ops-check": ("Run 13-point operational readiness check.", ops_main),
    "sessions-cleanup": ("Preview or archive stale sessions.", cleanup_sessions.main),
    "vocab-estimate": ("Estimate vocabulary size via Yes/No sampling.", estimate_vocabulary.main),
    "visualize": ("Generate HTML progress report with SVG charts.", visualize.main),
}


def _option_present(values: list[str], option: str) -> bool:
    """Detect an option in either "--opt value" or combined "--opt=value" form."""
    return any(value == option or value.startswith(option + "=") for value in values)


def _prepend_option(args: list[str] | None, option: str) -> list[str]:
    values = list(args or [])
    if not values or values[0].startswith("-") or _option_present(values, option):
        return values
    return [option, values[0], *values[1:]]


def _prepend_two_options(args: list[str] | None, first: str, second: str) -> list[str]:
    values = list(args or [])
    if len(values) < 2 or values[0].startswith("-") or values[1].startswith("-"):
        return values
    if _option_present(values, first) or _option_present(values, second):
        return values
    return [first, values[0], second, values[1], *values[2:]]


ALIASES: dict[str, tuple[str, Callable[[list[str] | None], list[str]]]] = {
    "check": ("validate-profile", lambda args: _prepend_option(args, "--profile")),
    "plan": ("daily-plan", lambda args: _prepend_option(args, "--profile")),
    "log": ("record-practice", lambda args: _prepend_option(args, "--ledger")),
    "tag": ("tag-error", lambda args: _prepend_option(args, "--text")),
    "errors": ("summarize-errors", lambda args: _prepend_option(args, "--ledger")),
    "update": ("update-ability", lambda args: _prepend_two_options(args, "--ability", "--ledger")),
    "trends": ("analyze-trends", lambda args: _prepend_option(args, "--ledger")),
    "write": ("writing-version", lambda args: _prepend_option(args, "--writing-id")),
    "score": ("score-writing", lambda args: _prepend_option(args, "--text-file")),
    "ingest": ("ingest-strategy", lambda args: _prepend_option(args, "--file")),
    "strategies": ("list-strategies", lambda args: list(args or [])),
    "vocab": ("vocab-estimate", lambda args: list(args or [])),
    "report": ("visualize", lambda args: list(args or [])),
    "validate": ("validate-strategies", lambda args: list(args or [])),
    "commit": ("commit-strategies", lambda args: list(args or [])),
    "backup-data": ("backup", lambda args: _prepend_option(args, "--data-dir")),
    "restore-data": ("restore", lambda args: _prepend_two_options(args, "--input", "--data-dir")),
}

_alias_commands: dict[str, tuple[str, CommandMain]] = {}
for _alias, (_target, _) in ALIASES.items():
    if _target not in COMMANDS:
        raise ValueError(
            f"Alias '{_alias}' references unknown command '{_target}'. "
            f"Available commands: {sorted(COMMANDS)}"
        )
    _alias_commands[_alias] = COMMANDS[_target]
ALL_COMMANDS = {**COMMANDS, **_alias_commands}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="examlex",
        description="Command line interface for ExamLex automation.",
    )
    parser.add_argument("command", choices=sorted(ALL_COMMANDS), help="Automation command to run.")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the selected command.")
    parsed = parser.parse_args(argv)

    command = parsed.command
    command_args = parsed.args
    if command in ALIASES:
        command, transform = ALIASES[command]
        command_args = transform(command_args)

    _, command_main = COMMANDS[command]
    return command_main(command_args)


if __name__ == "__main__":
    raise SystemExit(main())
