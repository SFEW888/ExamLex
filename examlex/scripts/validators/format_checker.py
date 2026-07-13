"""Deterministic format and schema validation for strategy entries."""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseValidator, ValidationIssue, ValidationReport

# strategy_id pattern: {exam-abbr}-{module}-{keyword}-{seq}
_STRATEGY_ID_RE = re.compile(r"^[a-z0-9]+-[a-z-]+-[a-z0-9-]+-\d{3}$")

# Prefixes that mark source_file as a remote/identifier reference (not a local path)
_REMOTE_PREFIXES = ("http://", "https://", "nuwa-", "bilibili-", "youtube-")

# Step numbering patterns: "1. " or "1) " or "Step 1:" or "- " or "* "
_STEP_LINE_RE = re.compile(
    r"^(\s*(\d+[\.\)、]\s|[-*]\s|Step\s+\d+[\s:]))"
)

# Vague phrasing to flag
_VAGUE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"建议(?:可以)?",
        r"可以考虑",
        r"根据情况",
        r"灵活[把握处理]",
        r"视情况而定",
    ]
]


class FormatChecker(BaseValidator):
    """Validate a strategy dict against format and content rules."""

    def validate(self, strategy: dict) -> ValidationReport:
        if not isinstance(strategy, dict):
            return ValidationReport(
                passed=False,
                errors=[ValidationIssue("strategy", "ERROR", "Input must be a dict")],
                warnings=[],
                score=0.0,
            )

        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        # 1. strategy_id
        sid = strategy.get("strategy_id")
        if not isinstance(sid, str) or not sid.strip():
            errors.append(ValidationIssue("strategy_id", "ERROR", "strategy_id is required and must be a non-empty string"))
        elif not _STRATEGY_ID_RE.match(sid):
            errors.append(ValidationIssue("strategy_id", "ERROR",
                f"strategy_id '{sid}' does not match pattern {{exam}}-{{module}}-{{keyword}}-{{seq}}"))

        # 2. title
        title = strategy.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(ValidationIssue("title", "ERROR", "title is required"))

        # 3. content
        content = strategy.get("content", "")
        if not isinstance(content, str) or len(content.strip()) < 20:
            errors.append(ValidationIssue("content", "ERROR",
                "content must be at least 20 characters"))

        # 4. steps — require numbered/list format
        steps = strategy.get("steps", [])
        if isinstance(steps, list) and steps:
            unnumbered = [
                i + 1 for i, s in enumerate(steps)
                if isinstance(s, str) and s.strip() and not _STEP_LINE_RE.match(s)
            ]
            if unnumbered:
                warnings.append(ValidationIssue("steps", "WARN",
                    f"Steps {unnumbered} may lack numbering — consider '1. ' or '- ' format",
                    remedy="Prefix each step with a number (1. 2. 3.) or bullet (- *)"))

        # 5. source_file — required, must exist if it's a local path
        source_file = strategy.get("source_file")
        if not isinstance(source_file, str) or not source_file.strip():
            errors.append(ValidationIssue("source_file", "ERROR", "source_file is required"))
        elif not source_file.startswith(_REMOTE_PREFIXES):
            # Looks like a local file path
            try:
                path = Path(source_file)
                exists = path.exists()
            except ValueError:
                warnings.append(ValidationIssue("source_file", "WARN",
                    f"source_file '{source_file}' contains invalid path characters",
                    remedy="Remove null bytes or other invalid path characters"))
            else:
                if not exists:
                    warnings.append(ValidationIssue("source_file", "WARN",
                        f"source_file '{source_file}' is not accessible at this path",
                        remedy="Verify the file exists or use a URL/identifier"))

        # 6. exam_types
        exam_types = strategy.get("exam_types", [])
        if not isinstance(exam_types, list) or not exam_types:
            errors.append(ValidationIssue("exam_types", "ERROR",
                "exam_types must be a non-empty list"))

        # 7. modules
        modules = strategy.get("modules", [])
        if not isinstance(modules, list) or not modules:
            errors.append(ValidationIssue("modules", "ERROR",
                "modules must be a non-empty list"))

        # 8. RIA++ structure completeness (if applicable)
        ria = strategy.get("ria_structure")
        if isinstance(ria, dict):
            expected = ["r_reading", "i_interpretation", "a1_past", "a2_trigger", "e_execution", "b_boundary"]
            missing = [k for k in expected if not str(ria.get(k) or "").strip()]
            if missing:
                errors.append(ValidationIssue("ria_structure", "ERROR",
                    f"RIA++ structure missing: {', '.join(missing)}",
                    remedy="Fill all six RIA++ segments"))
            # Check citation length
            r_text = ria.get("r_reading", "")
            if isinstance(r_text, str) and len(r_text) > 200:
                warnings.append(ValidationIssue("ria_structure.r_reading", "WARN",
                    f"Reading citation is {len(r_text)} chars (recommend ≤150)"))

        # 9. Scan for vague phrasing in content
        if isinstance(content, str):
            vague_hits = []
            for pat in _VAGUE_PATTERNS:
                hits = pat.findall(content)
                vague_hits.extend(hits)
            if len(vague_hits) >= 3:
                warnings.append(ValidationIssue("content", "WARN",
                    f"Found {len(vague_hits)} vague phrases (建议/可以考虑/根据情况/灵活). "
                    "Replace with concrete, executable instructions.",
                    remedy="Use specific actions: 'When X happens, do Y' instead of '建议Y'"))

        # 10. Check for executable steps in e_execution
        e_exec = (strategy.get("ria_structure", {}).get("e_execution") if isinstance(strategy.get("ria_structure"), dict) else None)
        if isinstance(e_exec, list) and not e_exec:
            warnings.append(ValidationIssue("ria_structure.e_execution", "WARN",
                "Execution steps are empty — strategy may not be actionable"))

        has_errors = len(errors) > 0
        return ValidationReport(
            passed=not has_errors,
            errors=errors,
            warnings=warnings,
            score=0.0,  # format checker doesn't score, Darwin does
        )
