from __future__ import annotations

import argparse
import sys
from typing import Any

try:
    from . import common
except ImportError:  # pragma: no cover - supports direct script execution.
    import common  # type: ignore[no-redef]

REQUIRED_FIELDS = [
    "learner_id",
    "exam_type",
    "foundation_level",
    "target_band",
    "daily_time_budget_minutes",
]

EXAM_TYPES = ("CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8")
FOUNDATION_LEVELS = ("基础偏弱", "中等基础", "基础较好")
CET_TARGET_BANDS = ("425~499", "500~550", "550+", "600+")
POSTGRADUATE_TARGET_BANDS = ("50+", "70~80", "80+", "90+")
TEM_TARGET_BANDS = ("60~69", "70~79", "80+")


def validate_profile(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in profile:
            errors.append(f"{field} is required")

    exam_type = profile.get("exam_type")
    foundation_level = profile.get("foundation_level")
    target_band = profile.get("target_band")
    daily_time_budget_minutes = profile.get("daily_time_budget_minutes")

    if "exam_type" in profile and exam_type not in EXAM_TYPES:
        errors.append("exam_type must be one of CET4, CET6, POSTGRADUATE_ENGLISH, TEM4, TEM8")

    if "foundation_level" in profile and foundation_level not in FOUNDATION_LEVELS:
        errors.append("foundation_level must be one of 基础偏弱, 中等基础, 基础较好")

    if "target_band" in profile and exam_type in EXAM_TYPES:
        allowed_bands = _target_bands_for(str(exam_type))
        if target_band not in allowed_bands:
            allowed = ", ".join(allowed_bands)
            errors.append(f"target_band must be one of {allowed} for {exam_type}")

    if "daily_time_budget_minutes" in profile and (
        not isinstance(daily_time_budget_minutes, int)
        or isinstance(daily_time_budget_minutes, bool)
        or daily_time_budget_minutes <= 0
    ):
        errors.append("daily_time_budget_minutes must be a positive integer")

    return errors


def _target_bands_for(exam_type: str) -> tuple[str, ...]:
    if exam_type in {"CET4", "CET6"}:
        return CET_TARGET_BANDS
    if exam_type == "POSTGRADUATE_ENGLISH":
        return POSTGRADUATE_TARGET_BANDS
    if exam_type in {"TEM4", "TEM8"}:
        return TEM_TARGET_BANDS
    return ()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an English exam learner profile.")
    parser.add_argument("--profile", required=True, help="Path to a JSON profile file.")
    args = parser.parse_args(argv)

    profile = common.load_data(args.profile)
    errors = validate_profile(profile)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("profile valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
