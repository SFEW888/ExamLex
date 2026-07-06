"""Cognitive extraction guide for person/teacher distillation.

Adapted from nuwa-skill's five-layer extraction methodology.
The Agent reads these instructions and executes them during the DISTILL stage.
"""

from __future__ import annotations

from typing import Any

from .base import BasePromptGuide, triple_verify_guide


class CognitiveGuide(BasePromptGuide):
    METHOD_NAME = "person"

    def stage_instructions(self, stage: str, context: dict | None = None) -> str:
        ctx = context or {}
        artifacts_dir = ctx.get("artifacts_dir", "<artifacts_dir>")
        person_name = ctx.get("person_name", "the person")
        from ..common import DEFAULT_EXAM_TYPES
        exam_types = ctx.get("exam_types", DEFAULT_EXAM_TYPES)

        if stage == "distill":
            return self._distill_instructions(artifacts_dir, person_name, exam_types)
        if stage == "evaluate":
            return self._evaluate_instructions(artifacts_dir)
        return f"Cognitive guide: stage '{stage}' not applicable."

    def _distill_instructions(self, artifacts_dir: str, person_name: str,
                               exam_types: list) -> str:
        return f"""# Cognitive Extraction Guide — {person_name}

Distill {person_name}'s English teaching/learning methodology into strategies.

## Phase 1 — Multi-source collection
Research {person_name} across 6 dimensions:
1. Published works — books, articles, courses
2. Conversations — interviews, podcasts, talks
3. Expression DNA — social media, teaching style patterns
4. External views — student testimonials, peer reviews
5. Decision records — key teaching decisions, methodology choices
6. Timeline — career evolution, methodology changes over time

Save research notes to {artifacts_dir}/research/ (one .md per dimension).

## Phase 1.5 — Triple verification
{triple_verify_guide()}

## Phase 2 — Five-layer extraction
For each verified insight:

1. **Expression patterns**: How does {person_name} explain concepts?
   — Catchphrases, metaphors, analogies, teaching style
2. **Mental models** (3-7): Core frameworks for learning/teaching
   — Name, one-liner, evidence (≥2 sources), application, limitations
3. **Decision heuristics** (5-10): Rules of thumb
   — "If X, then Y" format, with scenario and example
4. **Anti-patterns**: What {person_name} explicitly advises against
5. **Honesty boundary**: What this methodology cannot do

Target exams: {', '.join(exam_types)}

## Output
Write results to {artifacts_dir}/distilled.json using the output schema.
Each mental model and heuristic becomes a strategy entry.
"""

    def _evaluate_instructions(self, artifacts_dir: str) -> str:
        return f"""# Cognitive Effect Evaluation

Read distilled strategies from {artifacts_dir}/distilled.json.

Quality checks:
1. **Sanity check**: Do 3 known public statements align with extracted models?
2. **Edge case**: Test 1 unstated problem — does the model make reasonable predictions?
3. **Voice check**: Write 100-word analysis — can you recognize {artifacts_dir} in the style?

Write results to {artifacts_dir}/evaluation.json.
"""

    def output_schema(self) -> dict:
        return {
            "type": "object",
            "required": ["strategies", "pipeline_report"],
            "properties": {
                "strategies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["strategy_id", "title", "content", "steps"],
                        "properties": {
                            "strategy_id": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string", "minLength": 20},
                            "steps": {"type": "array", "items": {"type": "string"}},
                            "mental_model": {"type": "object"},
                            "heuristic": {"type": "object"},
                        },
                    },
                },
                "pipeline_report": {
                    "type": "object",
                    "required": ["total_candidates", "verified_count", "rejected_count", "pass_rate"],
                },
            },
        }
