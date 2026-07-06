"""Base extractor interface."""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExtractionResult:
    """Output from an extraction phase."""

    source_type: str
    input_ref: str                        # original URL or file path
    artifacts: dict[str, Path] = field(default_factory=dict)
    # e.g. {"transcript": Path, "video": Path, "metadata": Path}
    metadata: dict[str, Any] = field(default_factory=dict)
    # e.g. {"duration_seconds": 3600, "word_count": 5000}
    warnings: list[str] = field(default_factory=list)


class BaseExtractor(ABC):
    """Abstract base for input extractors.

    Each extractor handles one type of input (video URL, book file, etc.)
    and produces artifact files in the session's artifacts_dir.
    """

    # Override in subclasses (assign a new list/tuple when overriding)
    SUPPORTED_INPUTS: tuple[str, ...] = ()
    REQUIRED_TOOLS: tuple[str, ...] = ()

    @abstractmethod
    def extract(self, input_ref: str, output_dir: Path) -> ExtractionResult:
        """Download/parse/convert the input into workable artifacts."""
        ...

    @classmethod
    def check_dependencies(cls) -> list[str]:
        """Return list of missing tool names (empty = all available).

        Note: REQUIRED_TOOLS must be set as a class attribute (not as an
        instance attribute in __init__), otherwise this method will not see it.
        """
        missing: list[str] = []
        for tool in cls.REQUIRED_TOOLS:
            if shutil.which(tool) is None:
                missing.append(tool)
        return missing
