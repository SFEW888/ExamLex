#!/usr/bin/env python3
"""Run the bundled ExamLex CLI from a copied Skill directory."""

from __future__ import annotations

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_ROOT.parent))

from examlex.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
