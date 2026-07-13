"""Darwin 6-dimension static structure scoring (59 points total).

Adapted from darwin-skill's 9-dimension rubric. The 6 structure dimensions
are fully deterministic and scored by Python without requiring Agent reasoning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Dimension definitions ──
# Each: (name, weight, description)

DIMENSIONS = [
    ("dim1_frontmatter",     7,  "Frontmatter quality"),
    ("dim2_workflow_clarity",  12, "Workflow clarity"),
    ("dim3_failure_encoding",  12, "Failure mode encoding"),
    ("dim4_checkpoints",       6,  "Checkpoint design"),
    ("dim5_specificity",       17, "Actionable specificity"),
    ("dim6_resources",         4,  "Resource integration"),
]

TOTAL_STRUCTURE_POINTS = 59


@dataclass
class DimensionScore:
    name: str
    label: str
    weight: int
    raw: int           # 1-10
    weighted: float    # raw * weight / 10
    issues: list[str] = field(default_factory=list)


@dataclass
class StructureScore:
    total: float
    dimensions: list[DimensionScore]
    passed: bool       # True if ≥ 70% of 59


class DarwinStructureScorer:
    """Score a strategy entry on the 6 static structure dimensions."""

    def score(self, strategy: dict) -> StructureScore:
        dims = [
            self._score_dim1(strategy),
            self._score_dim2(strategy),
            self._score_dim3(strategy),
            self._score_dim4(strategy),
            self._score_dim5(strategy),
            self._score_dim6(strategy),
        ]
        total = sum(d.weighted for d in dims)
        passed = total >= (TOTAL_STRUCTURE_POINTS * 0.70)
        return StructureScore(total=round(total, 1), dimensions=dims, passed=passed)

    # ── dim1: Frontmatter quality (7 pts) ──
    def _score_dim1(self, s: dict) -> DimensionScore:
        issues = []
        raw = 10
        # Check if there are exam_types and modules (proxy for metadata quality)
        exam_types = s.get("exam_types", [])
        if not isinstance(exam_types, list) or not exam_types:
            issues.append("Missing exam_types")
            raw -= 3
        modules = s.get("modules", [])
        if not isinstance(modules, list) or not modules:
            issues.append("Missing modules")
            raw -= 2
        title = s.get("title", "")
        if not title or len(str(title)) < 3:
            issues.append("Title too short or missing")
            raw -= 2
        # Check for "空话" in content ending
        content = str(s.get("content", ""))
        stripped = re.sub(r'[，。！？、；："\'）\)\s]+$', "", content.rstrip())
        if stripped.endswith(("灵活应用", "根据情况判断", "视情况而定")):
            issues.append("Content ends with vague placeholder phrase")
            raw -= 2
        return DimensionScore("dim1_frontmatter", "Frontmatter quality", 7,
                              max(1, raw), max(1, raw) * 7 / 10, issues)

    # ── dim2: Workflow clarity (12 pts) ──
    def _score_dim2(self, s: dict) -> DimensionScore:
        issues = []
        raw = 10
        steps = s.get("steps", [])
        if not isinstance(steps, list) or not steps:
            issues.append("No steps defined")
            raw -= 5
        else:
            # Check if steps are numbered / clearly ordered
            numbered = sum(1 for step in steps if isinstance(step, str)
                          and re.match(r"^\d+[\.\)、]", step.strip()))
            if len(steps) > 0 and numbered == 0:
                issues.append("Steps are not numbered (1. 2. 3.)")
                raw -= 2
            if len(steps) < 2:
                issues.append("Only 1 step — may lack clear sequence")
                raw -= 2

        # Check if ria_structure has e_execution
        ria = s.get("ria_structure")
        if isinstance(ria, dict):
            e_exec = ria.get("e_execution", [])
            if isinstance(e_exec, list) and len(e_exec) >= 3:
                raw = min(10, raw + 1)  # bonus for detailed execution
        return DimensionScore("dim2_workflow_clarity", "Workflow clarity", 12,
                              max(1, raw), max(1, raw) * 12 / 10, issues)

    # ── dim3: Failure mode encoding (12 pts) ──
    def _score_dim3(self, s: dict) -> DimensionScore:
        issues = []
        raw = 10
        text = str(s.get("content", ""))
        ria = s.get("ria_structure")
        if isinstance(ria, dict):
            boundary = str(ria.get("b_boundary", ""))
            text += " " + boundary

        # Check for if-then patterns
        if_then = len(re.findall(r"(如果|若|if|when)\s*.+?\s*(则|那[么麼]|就|应|then)", text, re.IGNORECASE | re.DOTALL))
        if if_then == 0:
            issues.append("No if-then fallback patterns found")
            raw -= 5
        elif if_then < 2:
            issues.append(f"Only {if_then} if-then pattern(s) — recommend ≥2")
            raw -= 2

        # Check for explicit boundary/limitation
        has_boundary = bool(ria.get("b_boundary")) if isinstance(ria, dict) else False
        if not has_boundary:
            issues.append("Missing boundary section (when method does NOT apply)")
            raw -= 3
        return DimensionScore("dim3_failure_encoding", "Failure mode encoding", 12,
                              max(1, raw), max(1, raw) * 12 / 10, issues)

    # ── dim4: Checkpoint design (6 pts) ──
    def _score_dim4(self, s: dict) -> DimensionScore:
        issues = []
        raw = 10
        content = str(s.get("content", ""))
        steps_list = s.get("steps") if isinstance(s.get("steps"), list) else []
        steps_text = " ".join(str(step) for step in steps_list)
        combined = content + " " + steps_text

        has_checkpoint = bool(re.search(r"[🔴🛑⏸️]|STOP|CHECKPOINT|检查点|确认", combined))
        if not has_checkpoint:
            issues.append("No checkpoint/stop markers (STOP/CHECKPOINT)")
            raw -= 4
        return DimensionScore("dim4_checkpoints", "Checkpoint design", 6,
                              max(1, raw), max(1, raw) * 6 / 10, issues)

    # ── dim5: Actionable specificity (17 pts) ──
    def _score_dim5(self, s: dict) -> DimensionScore:
        issues = []
        raw = 10
        content = str(s.get("content", ""))

        vague_patterns = [
            (r"建议(可以)?", "建议"),
            (r"可以考虑", "可以考虑"),
            (r"根据情况", "根据情况"),
            (r"可能", "可能"),
            (r"大概|大约", "大概/大约"),
            (r"通常|一般.?情况", "通常/一般"),
            (r"尽量|尽可能", "尽量"),
            (r"适[当當]", "适当"),
        ]
        vague_count = 0
        for pat, label in vague_patterns:
            hits = len(re.findall(pat, content))
            if hits:
                vague_count += hits
        if vague_count >= 3:
            issues.append(f"Found {vague_count} vague phrases — use concrete actions")
            raw -= 4
        elif vague_count > 0:
            raw -= 1

        # Check for concrete parameters / numbers / examples
        has_numbers = bool(re.search(r"\d+", content))
        has_examples = bool(re.search(r"(例如|比如|例[：:]|e\.g\.|for example)", content, re.IGNORECASE))
        if not has_numbers:
            issues.append("No numeric parameters/examples")
            raw -= 2
        if not has_examples:
            issues.append("No concrete examples (例如/比如/e.g.)")
            raw -= 2
        return DimensionScore("dim5_specificity", "Actionable specificity", 17,
                              max(1, raw), max(1, raw) * 17 / 10, issues)

    # ── dim6: Resource integration (4 pts) ──
    def _score_dim6(self, s: dict) -> DimensionScore:
        issues = []
        raw = 10
        source_file = s.get("source_file", "")
        source_url = s.get("source_url", "")
        # Treat source_file and source_url symmetrically as valid references
        if not source_file and not source_url:
            issues.append("No source_file or source_url")
            raw -= 5
        elif not source_file or not source_url:
            issues.append("Missing source_file or source_url")
            raw -= 2

        # Check for tags as resource metadata
        tags = s.get("tags", [])
        if isinstance(tags, list) and tags:
            raw = min(10, raw + 1)
        return DimensionScore("dim6_resources", "Resource integration", 4,
                              max(1, raw), max(1, raw) * 4 / 10, issues)
