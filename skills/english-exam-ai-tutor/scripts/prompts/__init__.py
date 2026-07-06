"""Prompt guides for Agent-driven distillation and evaluation.

Each module provides structured instructions that the Agent reads and follows
during the DISTILL and EVALUATE stages of the pipeline. These are NOT
executable Python scripts — they are Agent SOP guides.
"""

from __future__ import annotations

from .base import BasePromptGuide, triple_verify_guide
from .ria import RIAGuide
from .cognitive import CognitiveGuide
from .effect import EffectGuide
from .climb import ClimbGuide

__all__ = [
    "BasePromptGuide",
    "triple_verify_guide",
    "RIAGuide",
    "CognitiveGuide",
    "EffectGuide",
    "ClimbGuide",
]
