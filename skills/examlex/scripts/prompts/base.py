"""Base prompt guide interface and shared utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePromptGuide(ABC):
    """Abstract guide that provides Agent instructions for a pipeline stage."""

    METHOD_NAME: str = "base"

    @abstractmethod
    def stage_instructions(self, stage: str, context: dict | None = None) -> str:
        """Return the Agent instructions for a given pipeline stage.

        Args:
            stage: One of "distill", "evaluate", "optimize"
            context: Dict with keys like artifacts_dir, exam_types, modules, etc.
        """
        ...

    @abstractmethod
    def output_schema(self) -> dict:
        """Return the JSON Schema that the Agent's output must conform to."""
        ...


def triple_verify_guide() -> str:
    """Shared triple-verification methodology used by both RIA and cognitive guides."""
    return """## Triple Verification (三重验证)

For each candidate method/insight, apply three checks:

1. **V1 Cross-domain (跨域复现)**: Does this appear in ≥2 independent sections/sources?
   If only mentioned once, downgrade to "observation" and reject.

2. **V2 Predictive power (生成力)**: Can you use this method to answer a problem
   the source doesn't explicitly address? If not, it may just be a description.

3. **V3 Uniqueness (排他性)**: Is this NOT something any generic tutor would say?
   If it's generic advice like "多读多练", reject.

Pass rate from real runs: 25-50%. Report the pass rate in pipeline_report.
Results: 3/3 passes → mental model. 1-2/3 → heuristic. 0/3 → reject."""
