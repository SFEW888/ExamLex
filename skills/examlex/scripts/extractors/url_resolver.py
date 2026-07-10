"""Input type detection — resolves user input to a known type."""

from __future__ import annotations

import os
import re
from enum import Enum, auto
from pathlib import Path


class InputType(Enum):
    URL_VIDEO = auto()      # https://bilibili.com/video/... etc.
    URL_UNKNOWN = auto()    # URL we can't handle
    LOCAL_BOOK = auto()     # .pdf / .epub / .docx / .mobi / .azw
    LOCAL_TEXT = auto()     # .txt / .md / .srt / .vtt / .json / .yaml
    PERSON_NAME = auto()    # plain text that looks like a person name
    UNKNOWN = auto()        # can't determine


# URL patterns for known video platforms
_VIDEO_HOSTS = [
    r"(?:www\.)?bilibili\.com",
    r"(?:www\.)?b23\.tv",
    r"(?:www\.)?youtube\.com",
    r"(?:www\.)?youtu\.be",
    r"(?:www\.)?v\.douyin\.com",
    r"(?:www\.)?douyin\.com",
    r"(?:www\.)?xiaohongshu\.com",
    r"(?:www\.)?xhslink\.com",
]

_VIDEO_PATTERN = re.compile(
    r"^https?://(" + "|".join(_VIDEO_HOSTS) + r")/",
    re.IGNORECASE,
)

_BOOK_EXTENSIONS = {".pdf", ".epub", ".docx", ".mobi", ".azw", ".azw3", ".rtf"}
_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".srt", ".vtt", ".json", ".yaml", ".yml", ".html", ".htm", ".rst", ".adoc"}


def resolve_input(input_ref: str) -> InputType:
    """Determine the input type from a user-provided reference string."""
    ref = input_ref.strip()

    # Is it a URL?
    if ref.startswith(("http://", "https://")):
        if _VIDEO_PATTERN.search(ref):
            return InputType.URL_VIDEO
        return InputType.URL_UNKNOWN

    # Is it a local file path?
    expanded = os.path.expanduser(ref)
    path = Path(expanded)
    if path.exists() and path.is_file():
        suffix = path.suffix.lower()
        if suffix in _BOOK_EXTENSIONS:
            return InputType.LOCAL_BOOK
        if suffix in _TEXT_EXTENSIONS:
            return InputType.LOCAL_TEXT
        # Unknown extension but exists — try text
        return InputType.LOCAL_TEXT

    # Is it a file glob or path that doesn't exist yet?
    if any(c in ref for c in ("/", "\\", ".")) and not ref.startswith("-"):
        suffix = Path(ref).suffix.lower()
        if suffix in _BOOK_EXTENSIONS:
            return InputType.LOCAL_BOOK
        if suffix in _TEXT_EXTENSIONS:
            return InputType.LOCAL_TEXT

    # Looks like a person name (no URL, no file extension, not a flag)
    if not ref.startswith("-") and len(ref) >= 2:
        return InputType.PERSON_NAME

    return InputType.UNKNOWN
