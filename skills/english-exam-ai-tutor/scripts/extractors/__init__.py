"""Extractor registry and plugin system."""

from __future__ import annotations

from .base import BaseExtractor, ExtractionResult
from .text import TextExtractor
from .url_resolver import InputType, resolve_input

# Registry: maps InputType to Extractor class
EXTRACTORS: dict = {
    InputType.LOCAL_TEXT: TextExtractor,
    InputType.LOCAL_BOOK: None,   # book.BookExtractor (lazy)
    InputType.URL_VIDEO: None,    # video.VideoExtractor (lazy)
    InputType.PERSON_NAME: None,   # handled by Agent directly
}

__all__ = [
    "BaseExtractor",
    "ExtractionResult",
    "InputType",
    "resolve_input",
    "TextExtractor",
    "EXTRACTORS",
]
