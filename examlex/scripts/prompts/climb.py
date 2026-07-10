"""Hill-climbing optimization guide.

Used by the Agent during the OPTIMIZE stage when a strategy scores below threshold.
"""

from __future__ import annotations

from typing import Any

from .base import BasePromptGuide


class ClimbGuide(BasePromptGuide):
    METHOD_NAME = "darwin-climb"

    def stage_instructions(self, stage: str, context: dict | None = None) -> str:
        ctx = context or {}
        # Escape curly braces to prevent f-string ValueError on untrusted input.
        strategy_id = str(ctx.get("strategy_id", "<strategy_id>")).replace('{', '{{').replace('}', '}}')
        current_score = float(ctx.get("current_score", 0.0))
        weakest = str(ctx.get("weakest_dimension", "unknown")).replace('{', '{{').replace('}', '}}')

        return f"""# Hill-Climbing Optimization Guide

Optimize strategy '{strategy_id}' (current score: {current_score}).

## Step 1 — Diagnose
Weakest dimension: {weakest}
Read the current strategy content and structure validation report.
Identify the specific issue (not just "dim3 is low" — what exactly is missing?).

## Step 2 — Propose improvement
For the weakest dimension ONLY, propose ONE concrete change:
- What exact text to change (quote the current text)
- What to replace it with (show the new text)
- Why this improves the score (reference the rubric)

## Step 3 — Apply
Make the edit to the strategy content.

## Step 4 — Re-score
Re-run validation and effect scoring.

## Step 5 — Decision
- If new score > old score: KEEP, record in score_history
- If new score <= old score: REVERT to previous version
- If last 2 rounds both had Δ < 2.0: STOP (touch-top signal)

## Anti-pattern blacklist (DO NOT DO):
1. Don't score your own edits — use independent judge
2. Don't change multiple dimensions in one round
3. Don't pad content just to increase score (no filler)
4. Don't change the strategy's core meaning
5. Don't skip eval — dry_run ratio > 30% means scores are unreliable

## Constraints
- Max rounds: 3 (then stop regardless)
- Each round: change ONE dimension only
- File size: must not exceed 150% of original
"""

    def output_schema(self) -> dict:
        return {
            "type": "object",
            "required": ["round", "dimension_targeted", "old_score", "new_score", "delta", "decision"],
            "properties": {
                "round": {"type": "integer"},
                "dimension_targeted": {"type": "string"},
                "old_score": {"type": "number"},
                "new_score": {"type": "number"},
                "delta": {"type": "number"},
                "decision": {"enum": ["keep", "revert", "stop"]},
                "change_description": {"type": "string"},
            },
        }
