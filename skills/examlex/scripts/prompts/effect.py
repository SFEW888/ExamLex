"""Darwin effect scoring guide (dimensions 7-8, 35 points).

Used by the Agent during the EVALUATE stage.
"""

from __future__ import annotations

from typing import Any

from .base import BasePromptGuide


class EffectGuide(BasePromptGuide):
    METHOD_NAME = "darwin-effect"

    def stage_instructions(self, stage: str, context: dict | None = None) -> str:
        ctx = context or {}
        artifacts_dir = ctx.get("artifacts_dir") or "<artifacts_dir>"

        return f"""# Darwin Effect Scoring Guide

Score the distilled strategies on the 2 effect dimensions (35 points total).

## Input
- Distilled strategies: {artifacts_dir}/distilled.json
- Structure scores: {artifacts_dir}/validation_report.json (from 'examlex validate')

## Dimension 7 — Overall Architecture (12 points)
Rate 1-10 on:
- Structure hierarchy: clear, not redundant, no missing parts
- No AI-slop filler phrases or redundancy
- Consistent with the project's established patterns

## Dimension 8 — Performance (23 points)
For each strategy:
1. Design 2-3 test prompts (typical usage, edge case, decoy)
2. Run each prompt with and without the strategy
3. Compare: does the strategy output show clear improvement over baseline?
4. Score 1-10 based on:
   - Task completion: did it help achieve the user's goal?
   - Quality lift: is the output notably better than no-strategy baseline?
   - Side effects: any negative impacts (verbosity, off-topic, format issues)?

If you cannot run actual test prompts (subagent unavailable), mark eval as dry_run
and note the limitation. Dry runs should not claim full confidence.

## Output
Write to {artifacts_dir}/evaluation.json with structure:
{{
  "strategies": [
    {{
      "strategy_id": "...",
      "strategy_sha256": "copy the exact digest from validation_report.json",
      "dim7_architecture": {{"score": 8, "notes": "..."}},
      "dim8_performance": {{"score": 7, "test_results": [...], "eval_mode": "full_test|dry_run"}},
      "effect_total": 22.0
    }}
  ],
  "summary": {{
    "average_effect_score": 0.0,
    "dry_run_ratio": 0.0,
    "dry_run_warning": false
  }}
}}
"""

    def output_schema(self) -> dict:
        return {
            "type": "object",
            "required": ["strategies", "summary"],
            "properties": {
                "strategies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["strategy_id", "strategy_sha256", "dim7_architecture", "dim8_performance", "effect_total"],
                        "properties": {
                            "strategy_id": {"type": "string"},
                            "strategy_sha256": {
                                "type": "string",
                                "pattern": "^[a-f0-9]{64}$",
                            },
                            "dim7_architecture": {"type": "object"},
                            "dim8_performance": {"type": "object"},
                            "effect_total": {"type": "number"},
                        },
                    },
                },
                "summary": {
                    "type": "object",
                    "required": ["average_effect_score", "dry_run_ratio", "dry_run_warning"],
                    "properties": {
                        "average_effect_score": {"type": "number"},
                        "dry_run_ratio": {"type": "number"},
                        "dry_run_warning": {"type": "boolean"},
                    },
                },
            },
        }
