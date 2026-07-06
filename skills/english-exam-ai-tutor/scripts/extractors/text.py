"""Plain-text extractor — reads and normalizes text files."""

from __future__ import annotations

from pathlib import Path

from .base import BaseExtractor, ExtractionResult

# Refuse to load files larger than this into memory (guards against OOM)
_MAX_BYTES = 50 * 1024 * 1024  # 50 MiB


class TextExtractor(BaseExtractor):
    """Extract and normalize plain-text input files."""

    SUPPORTED_INPUTS = ["file:*.txt", "file:*.md", "file:*.srt", "file:*.vtt", "file:*.json"]
    REQUIRED_TOOLS: list[str] = []

    def extract(self, input_ref: str, output_dir: Path) -> ExtractionResult:
        source = Path(input_ref).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Text file not found: {source}")
        if source.is_dir():
            raise IsADirectoryError(f"Expected a file, got a directory: {source}")

        size = source.stat().st_size
        if size > _MAX_BYTES:
            raise ValueError(
                f"Text file too large ({size} bytes, >{_MAX_BYTES}). "
                "Refusing to load it entirely into memory."
            )

        raw = _read_text_with_fallback(source)
        # Strip BOM and normalize line endings
        text = raw.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")

        # Write normalized text as artifact
        normalized_path = output_dir / "full_text.txt"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            normalized_path.write_text(text, encoding="utf-8")
        except OSError as exc:
            raise OSError(f"Failed to write artifact to {normalized_path}: {exc}") from exc

        return ExtractionResult(
            source_type="text",
            input_ref=str(source),
            artifacts={"full_text": normalized_path},
            metadata={
                "original_file": source.name,
                "char_count": len(text),
                "line_count": text.count("\n") + (1 if text else 0),
                "word_count_approx": len(text.split()),
            },
            warnings=_content_warnings(text),
        )


def _read_text_with_fallback(source: Path) -> str:
    """Read text as UTF-8, falling back to GB18030 for legacy Chinese encodings."""
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise OSError(f"Failed to read {source}: {exc}") from exc
    for encoding in ("utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(
        f"Could not decode {source} as UTF-8 or GB18030. "
        "Please convert the file to UTF-8 and retry."
    )


def _content_warnings(text: str) -> list[str]:
    warnings = []
    word_count = len(text.split())
    if word_count < 500:
        warnings.append(
            f"Content is short ({word_count} words). May not contain enough "
            "material to extract meaningful strategies."
        )
    return warnings
