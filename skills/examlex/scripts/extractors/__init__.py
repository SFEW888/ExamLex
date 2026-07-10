"""Extractor registry and plugin system."""

from __future__ import annotations

from .base import BaseExtractor, ExtractionResult
from .book import BookExtractor
from .text import TextExtractor
from .url_resolver import InputType, resolve_input
from .video import VideoExtractor

# Registry: maps InputType to Extractor class.
# PERSON_NAME has no extractor (handled by Agent directly) and is omitted.
EXTRACTORS: dict = {
    InputType.LOCAL_TEXT: TextExtractor,
    InputType.LOCAL_BOOK: BookExtractor,
    InputType.URL_VIDEO: VideoExtractor,
}

__all__ = [
    "BaseExtractor",
    "ExtractionResult",
    "InputType",
    "resolve_input",
    "TextExtractor",
    "EXTRACTORS",
]
