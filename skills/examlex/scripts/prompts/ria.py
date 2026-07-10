"""RIA-TV++ distillation guide for video, podcast, and course content.

Adapted from cangjie-skill's six-phase methodology.
The Agent reads these instructions and executes them during the DISTILL stage.
"""

from __future__ import annotations

from typing import Any

from .base import BasePromptGuide, triple_verify_guide


class RIAGuide(BasePromptGuide):
    METHOD_NAME = "video"

    def stage_instructions(self, stage: str, context: dict | None = None) -> str:
        ctx = context or {}
        artifacts_dir = ctx.get("artifacts_dir", "<artifacts_dir>")
        from ..common import DEFAULT_EXAM_TYPES, ABILITY_TREE
        exam_types = ctx.get("exam_types", DEFAULT_EXAM_TYPES)
        modules = ctx.get("modules", sorted(ABILITY_TREE.keys()))

        if stage == "distill":
            return self._distill_instructions(artifacts_dir, exam_types, modules)
        if stage == "evaluate":
            return self._evaluate_instructions(artifacts_dir)
        return f"RIA guide: stage '{stage}' not applicable."

    def _distill_instructions(self, artifacts_dir: str, exam_types: list,
                               modules: list) -> str:
        return f"""# RIA-TV++ Distillation Guide

You are distilling a video/podcast/course transcript into exam strategies.

## Input
- Transcript: {artifacts_dir}/transcript.txt
- Post caption: {artifacts_dir}/post_caption.txt (if available)
- Target exams: {', '.join(exam_types) if exam_types else ', '.join(DEFAULT_EXAM_TYPES)}
- Target modules: {', '.join(modules) if modules else 'all'}

## Phase 0 — Whole-content analysis
Read the full transcript. Identify:
1. The main thesis and section structure
2. Key terminology and recurring concepts
3. Natural break points (chapters, timestamps, topic shifts)

## Phase 1 — Parallel extraction
Extract five categories simultaneously:
(a) Named frameworks: explicitly named methodologies
(b) Actionable principles: "when X, do Y" rules
(c) Concrete examples: specific cases where a method succeeded
(d) Counter-examples: warnings, pitfalls
(e) Key terms: specialized vocabulary with definitions

## Phase 1.5 — Triple verification
{triple_verify_guide()}

## Phase 2 — RIA++ construction (per verified method)
For each verified method, produce a strategy entry with:
- **R (Reading)**: Direct quote ≤150 chars, with timestamp
- **I (Interpretation)**: Restate core logic in your own words
- **A1 (Past)**: Concrete example from the source
- **A2 (Trigger)**: Specific CET exam scenario + Chinese trigger phrases
- **E (Execution)**: Numbered steps (1. 2. 3.) with completion criteria
- **B (Boundary)**: When this method does NOT apply

## Phase 3 — Zettelkasten linking
For each strategy, identify related strategies:
- A complements B (used together)
- A contrasts with B (different approach to same problem)
- A depends on B (prerequisite)

## Output
Write your results to {artifacts_dir}/distilled.json using the output schema.
Include pipeline_report with pass rate, verified count, rejected count.
"""

    def _evaluate_instructions(self, artifacts_dir: str) -> str:
        return f"""# RIA Effect Evaluation

Read the distilled strategies from {artifacts_dir}/distilled.json.

For each strategy:
1. Read its test-prompts (if available)
2. Run each test prompt, comparing with-skill vs without-skill output
3. Score dimension 7 (Overall architecture, 12pts) and dimension 8 (Performance, 23pts)

Write evaluation results to {artifacts_dir}/evaluation.json.
"""

    def output_schema(self) -> dict:
        return {
            "type": "object",
            "required": ["strategies", "pipeline_report"],
            "properties": {
                "strategies": {
                    "type": "array",
                    "minItems": 0,
                    "items": {
                        "type": "object",
                        "required": ["strategy_id", "title", "content", "steps", "ria_structure"],
                        "properties": {
                            "strategy_id": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string", "minLength": 20},
                            "steps": {"type": "array", "items": {"type": "string"}},
                            "ria_structure": {
                                "type": "object",
                                "required": ["r_reading", "i_interpretation", "a1_past",
                                            "a2_trigger", "e_execution", "b_boundary"],
                                "properties": {
                                    "r_reading": {"type": "string"},
                                    "i_interpretation": {"type": "string"},
                                    "a1_past": {"type": "string"},
                                    "a2_trigger": {"type": "string"},
                                    "e_execution": {"type": "string"},
                                    "b_boundary": {"type": "string"},
                                },
                            },
                            "related_strategies": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "pipeline_report": {
                    "type": "object",
                    "required": ["total_candidates", "verified_count", "rejected_count", "pass_rate"],
                },
            },
        }
