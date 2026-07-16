"""Compatibility entry point backed by the canonical Skill package."""

from skills.examlex import cli as _canonical_cli
from skills.examlex.cli import *  # noqa: F401,F403
from skills.examlex.cli import main


def __getattr__(name: str):
    """Forward private compatibility imports to the canonical CLI module."""
    return getattr(_canonical_cli, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_canonical_cli)))
