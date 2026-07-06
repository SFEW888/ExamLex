"""Plain-text extractor — reads and normalizes text files."""

from __future__ import annotations

from pathlib import Path

from .base import BaseExtractor, ExtractionResult


class TextExtractor(BaseExtractor):
    """Extract and normalize plain-text input files."""

    SUPPORTED_INPUTS = ["file:*.txt", "file:*.md", "file:*.srt", "file:*.vtt", "file:*.json"]
    REQUIRED_TOOLS: list[str] = []

    def extract(self, input_ref: str, output_dir: Path) -> ExtractionResult:
        source = Path(input_ref).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Text file not found: {source}")

        raw = source.read_text(encoding="utf-8")
        # Strip BOM and normalize line endings
        text = raw.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")

        # Write normalized text as artifact
        normalized_path = output_dir / "full_text.txt"
        output_dir.mkdir(parents=True, exist_ok=True)
        normalized_path.write_text(text, encoding="utf-8")

        return ExtractionResult(
            source_type="text",
            input_ref=str(source),
            artifacts={"full_text": normalized_path},
            metadata={
                "original_file": source.name,
                "char_count": len(text),
                "line_count": text.count("\n") + 1,
                "word_count_approx": len(text.split()),
            },
            warnings=_content_warnings(text),
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
