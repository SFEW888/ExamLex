from __future__ import annotations

import argparse
from collections.abc import Callable

from .scripts import (
    analyze_trends,
    generate_daily_plan,
    manage_writing_versions,
    record_practice,
    score_writing_rubric,
    summarize_errors,
    tag_error,
    update_ability_profile,
    validate_profile,
)

CommandMain = Callable[[list[str] | None], int]

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
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="english-exam-tutor",
        description="Command line interface for English Exam AI Tutor automation.",
    )
    parser.add_argument("command", choices=sorted(COMMANDS), help="Automation command to run.")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the selected command.")
    parsed = parser.parse_args(argv)

    _, command_main = COMMANDS[parsed.command]
    return command_main(parsed.args)


if __name__ == "__main__":
    raise SystemExit(main())
