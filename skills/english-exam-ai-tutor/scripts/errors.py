"""Standardized error types for the English Exam AI Tutor pipeline.

All errors inherit from TutorError and carry structured metadata
so the Agent (or CLI user) can determine whether to retry or abort.
"""

from __future__ import annotations

from typing import Any


class TutorError(Exception):
    """Base error for the tutor pipeline."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        recoverable: bool = False,
        remedy: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.recoverable = recoverable
        self.remedy = remedy

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "recoverable": self.recoverable,
            "remedy": self.remedy,
        }


class ExtractionError(TutorError):
    """Raised when downloading, parsing, or converting input fails."""

    def __init__(
        self,
        message: str,
        *,
        recoverable: bool = True,
        remedy: str | None = None,
    ) -> None:
        super().__init__(
            "EXTRACTION_FAILED", message, recoverable=recoverable, remedy=remedy
        )


class ValidationError(TutorError):
    """Raised when format, schema, or content validation fails."""

    def __init__(
        self,
        message: str,
        *,
        recoverable: bool = True,
        remedy: str | None = None,
    ) -> None:
        super().__init__(
            "VALIDATION_FAILED", message, recoverable=recoverable, remedy=remedy
        )


class ASRError(TutorError):
    """Raised when speech-to-text transcription fails."""

    def __init__(
        self,
        message: str,
        *,
        recoverable: bool = True,
        remedy: str | None = None,
    ) -> None:
        super().__init__(
            "ASR_FAILED", message, recoverable=recoverable, remedy=remedy
        )


class DependencyError(TutorError):
    """Raised when a required external tool is missing."""

    def __init__(
        self,
        tool_name: str,
        *,
        recoverable: bool = True,
        remedy: str | None = None,
    ) -> None:
        super().__init__(
            "DEPENDENCY_MISSING",
            f"Required tool '{tool_name}' is not installed or not on PATH.",
            recoverable=recoverable,
            remedy=remedy,
        )


class NetworkError(TutorError):
    """Raised when a network request fails (download, API call)."""

    def __init__(
        self,
        message: str,
        *,
        recoverable: bool = True,
        remedy: str | None = None,
    ) -> None:
        super().__init__(
            "NETWORK_FAILED", message, recoverable=recoverable, remedy=remedy
        )


class DarwinError(TutorError):
    """Raised when Darwin scoring or optimization fails."""

    def __init__(
        self,
        message: str,
        *,
        recoverable: bool = True,
        remedy: str | None = None,
    ) -> None:
        super().__init__(
            "DARWIN_FAILED", message, recoverable=recoverable, remedy=remedy
        )
