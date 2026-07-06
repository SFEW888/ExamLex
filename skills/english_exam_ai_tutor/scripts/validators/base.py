"""Base validator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ValidationIssue:
    field: str
    severity: Literal["ERROR", "WARN"]
    message: str
    remedy: str | None = None


@dataclass
class ValidationReport:
    passed: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseValidator(ABC):
    """Abstract validator for strategy entries."""

    @abstractmethod
    def validate(self, strategy: dict[str, Any]) -> ValidationReport:
        ...
