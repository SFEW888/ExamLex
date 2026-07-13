"""Book extractor — structured extraction from books and documents.

Supports: PDF (pdftotext/Docling), EPUB, DOCX, HTML, Markdown, plain text, RTF.
Produces: full_text.txt, chapter structure, glossary, patterns, cheatsheet.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

from .base import BaseExtractor, ExtractionResult

# Supported file extensions
_BOOK_EXTENSIONS = {
    ".pdf", ".epub", ".docx", ".txt", ".md", ".markdown",
    ".html", ".htm", ".rst", ".adoc", ".rtf", ".mobi", ".azw", ".azw3",
}

# Chapter heading patterns (English + Chinese)
_CHAPTER_PATTERNS = [
    re.compile(r"^#{1,3}\s*(Chapter|CHAPTER|第[一二三四五六七八九十\d]+[章节]|Chapter\s+\d+)", re.MULTILINE),
    re.compile(r"^(Chapter|CHAPTER)\s+\d+", re.MULTILINE),
    re.compile(r"^第[一二三四五六七八九十\d]+\s*[章节篇]", re.MULTILINE),
    re.compile(r"^\d+\.\s+(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})", re.MULTILINE),
]


class _TextHTMLParser(HTMLParser):
    """Extract visible text while preserving basic block structure."""

    BLOCK_TAGS = {"address", "article", "aside", "blockquote", "div", "footer",
                  "h1", "h2", "h3", "h4", "h5", "h6", "header", "li", "main",
                  "nav", "p", "section", "table", "tr"}
    SKIPPED_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in self.SKIPPED_TAGS:
            self.skip_depth += 1
        elif self.skip_depth == 0 and (tag in self.BLOCK_TAGS or tag == "br"):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIPPED_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif self.skip_depth == 0 and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth == 0:
            self.parts.append(data)

    def text(self) -> str:
        value = "".join(self.parts)
        value = re.sub(r"[ \t\f\v]+", " ", value)
        value = re.sub(r" *\n *", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


def _html_to_text(html: str) -> str:
    parser = _TextHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.text()


class BookExtractor(BaseExtractor):
    SUPPORTED_INPUTS = [f"file:*{ext}" for ext in _BOOK_EXTENSIONS]
    REQUIRED_TOOLS: list[str] = []  # pdftotext and calibre are optional
    MAX_EPUB_ENTRIES = 2_000
    MAX_EPUB_HTML_BYTES = 10 * 1024 * 1024
    MAX_EPUB_TOTAL_HTML_BYTES = 50 * 1024 * 1024
    MAX_EPUB_COMPRESSION_RATIO = 100

    def extract(self, input_ref: str, output_dir: Path) -> ExtractionResult:
        source = Path(input_ref).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Book file not found: {source}")

        suffix = source.suffix.lower()
        if suffix not in _BOOK_EXTENSIONS:
            raise ValueError(
                f"Unsupported book format: {suffix}. "
                f"Supported: {', '.join(sorted(_BOOK_EXTENSIONS))}"
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract text based on format
        text = self._extract_text(source, suffix)
        warnings = _content_warnings(text)

        # Write full text
        full_text_path = output_dir / "full_text.txt"
        full_text_path.write_text(text, encoding="utf-8")

        # Detect chapters
        chapters = self._detect_chapters(text)

        # Extract key terms (simple heuristic)
        glossary = self._extract_glossary(text, chapters)

        artifacts = {
            "full_text": full_text_path,
        }
        if chapters:
            chapters_dir = output_dir / "chapters"
            chapters_dir.mkdir(exist_ok=True)
            for i, (title, start, end) in enumerate(chapters, 1):
                ch_path = chapters_dir / f"ch{i:02d}-{_slugify(title)}.txt"
                ch_path.write_text(text[start:end].strip(), encoding="utf-8")
            artifacts["chapters"] = chapters_dir

        if glossary:
            glossary_path = output_dir / "glossary.md"
            glossary_path.write_text(glossary, encoding="utf-8")
            artifacts["glossary"] = glossary_path

        return ExtractionResult(
            source_type="book",
            input_ref=str(source),
            artifacts=artifacts,
            metadata={
                "original_file": source.name,
                "format": suffix,
                "char_count": len(text),
                "line_count": text.count("\n") + 1,
                "word_count_approx": len(text.split()),
                "chapter_count": len(chapters),
            },
            warnings=warnings,
        )

    def _extract_text(self, source: Path, suffix: str) -> str:
        if suffix in (".txt", ".md", ".markdown", ".rst", ".adoc"):
            return source.read_text(encoding="utf-8").lstrip("﻿")
        if suffix in (".html", ".htm"):
            return self._extract_html(source)
        if suffix == ".pdf":
            return self._extract_pdf(source)
        if suffix == ".epub":
            return self._extract_epub(source)
        if suffix == ".docx":
            return self._extract_docx(source)
        if suffix == ".rtf":
            return self._extract_rtf(source)
        if suffix in (".mobi", ".azw", ".azw3"):
            return self._extract_mobi(source)
        # Fallback: try reading as UTF-8 text
        return source.read_text(encoding="utf-8", errors="replace")

    def _extract_html(self, source: Path) -> str:
        html = source.read_text(encoding="utf-8", errors="replace")
        return _html_to_text(html)

    def _extract_pdf(self, source: Path) -> str:
        # Try pdftotext first (fast, good for text PDFs)
        pdftotext = shutil.which("pdftotext")
        if pdftotext:
            try:
                result = subprocess.run(
                    [pdftotext, "-layout", str(source), "-"],
                    capture_output=True, text=True, timeout=300,
                )
            except subprocess.TimeoutExpired:
                raise RuntimeError(
                    f"pdftotext timed out after 300s while processing {source.name}"
                )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        # Fallback: try python-based extraction (find_spec returns None if absent)
        from importlib.util import find_spec
        if find_spec("docling"):
            return self._extract_pdf_docling(source)
        raise RuntimeError(
            "Cannot extract PDF: pdftotext not found and docling not installed. "
            "Install poppler-utils (brew install poppler) or docling (pip install docling)."
        )

    def _extract_pdf_docling(self, source: Path) -> str:
        try:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            result = converter.convert(str(source))
            return result.document.export_to_markdown()
        except ImportError:
            raise RuntimeError("docling is not installed. Run: pip install docling")

    def _extract_epub(self, source: Path) -> str:
        import zipfile
        try:
            with zipfile.ZipFile(source, "r") as zf:
                self._validated_epub_html_infos(zf, source)
        except zipfile.BadZipFile:
            raise ValueError("File is not a valid EPUB/ZIP archive.")

        # Try using ebook-convert (calibre)
        calibre = shutil.which("ebook-convert")
        if calibre:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                try:
                    result = subprocess.run(
                        [calibre, str(source), str(tmp_path)],
                        capture_output=True, text=True, timeout=300,
                    )
                except subprocess.TimeoutExpired:
                    raise RuntimeError(
                        f"ebook-convert timed out after 300s while processing {source.name}"
                    )
                if result.returncode == 0 and tmp_path.exists():
                    return tmp_path.read_text(encoding="utf-8", errors="replace")
            finally:
                tmp_path.unlink(missing_ok=True)

        # Fallback: extract HTML from EPUB zip and strip tags
        return self._extract_epub_simple(source)

    def _validated_epub_html_infos(self, archive, source: Path):
        if "META-INF/encryption.xml" in archive.namelist():
            raise ValueError(
                "This EPUB file has DRM protection and cannot be extracted. "
                "Please remove DRM first using a tool like calibre + DeDRM."
            )
        infos = archive.infolist()
        if len(infos) > self.MAX_EPUB_ENTRIES:
            raise ValueError(
                f"EPUB entry count exceeds {self.MAX_EPUB_ENTRIES}: {source.name}"
            )
        html_infos = [
            info
            for info in infos
            if info.filename.lower().endswith((".html", ".htm", ".xhtml"))
        ]
        total_html_bytes = 0
        for info in html_infos:
            if info.file_size < 0 or info.compress_size < 0:
                raise ValueError(f"EPUB contains invalid ZIP metadata: {info.filename}")
            if info.file_size > self.MAX_EPUB_HTML_BYTES:
                raise ValueError(
                    f"EPUB HTML entry exceeds {self.MAX_EPUB_HTML_BYTES} bytes: {info.filename}"
                )
            total_html_bytes += info.file_size
            if total_html_bytes > self.MAX_EPUB_TOTAL_HTML_BYTES:
                raise ValueError(
                    f"EPUB total HTML exceeds {self.MAX_EPUB_TOTAL_HTML_BYTES} bytes: {source.name}"
                )
            ratio = float("inf") if info.compress_size == 0 and info.file_size else (
                info.file_size / max(info.compress_size, 1)
            )
            if ratio > self.MAX_EPUB_COMPRESSION_RATIO:
                raise ValueError(
                    f"EPUB compression ratio exceeds {self.MAX_EPUB_COMPRESSION_RATIO}: {info.filename}"
                )
        return sorted(html_infos, key=lambda item: item.filename)

    def _extract_epub_simple(self, source: Path) -> str:
        import zipfile
        parts = []
        with zipfile.ZipFile(source, "r") as zf:
            html_infos = self._validated_epub_html_infos(zf, source)
            for info in html_infos:
                html = zf.read(info).decode("utf-8", errors="replace")
                parts.append(_html_to_text(html))
        return "\n\n".join(parts)

    def _extract_docx(self, source: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(source))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text)
        except ImportError:
            raise RuntimeError("python-docx is not installed. Run: pip install python-docx")

    def _extract_rtf(self, source: Path) -> str:
        try:
            from striprtf.striprtf import rtf_to_text
            # RTF is ANSI/ASCII-based; decode as latin-1 to preserve raw control
            # bytes rather than corrupting them with U+FFFD replacements.
            raw = source.read_bytes()
            return rtf_to_text(raw.decode("latin-1", errors="replace"))
        except ImportError:
            raise RuntimeError("striprtf is not installed. Run: pip install striprtf")

    def _extract_mobi(self, source: Path) -> str:
        calibre = shutil.which("ebook-convert")
        if not calibre:
            raise RuntimeError(
                "MOBI/AZW extraction requires calibre. Install: brew install calibre"
            )
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            try:
                result = subprocess.run(
                    [calibre, str(source), str(tmp_path)],
                    capture_output=True, text=True, timeout=300,
                )
            except subprocess.TimeoutExpired:
                raise RuntimeError(
                    f"ebook-convert timed out after 300s while processing {source.name}"
                )
            if result.returncode == 0 and tmp_path.exists():
                return tmp_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(f"calibre conversion failed: {result.stderr[:300]}")
        finally:
            tmp_path.unlink(missing_ok=True)

    def _detect_chapters(self, text: str) -> list[tuple[str, int, int]]:
        """Detect chapter boundaries in the text. Returns [(title, start_pos, end_pos)]."""
        lines = text.split("\n")
        chapter_starts = []

        for i, line in enumerate(lines):
            for pat in _CHAPTER_PATTERNS:
                if pat.match(line.strip()):
                    title = line.strip().lstrip("#").strip()
                    char_pos = sum(len(l) + 1 for l in lines[:i])
                    chapter_starts.append((title, char_pos, i))
                    break

        if not chapter_starts:
            return []

        chapters = []
        for j, (title, char_pos, line_idx) in enumerate(chapter_starts):
            if j + 1 < len(chapter_starts):
                end_pos = chapter_starts[j + 1][1]
            else:
                end_pos = len(text)
            chapters.append((title, char_pos, end_pos))
        return chapters

    def _extract_glossary(self, text: str,
                          chapters: list[tuple[str, int, int]]) -> str:
        """Extract key terms using bold/italic patterns and English-Chinese pairs."""
        terms = set()
        # Pattern: **term** or *term* or `term`
        for match in re.finditer(r"\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`", text):
            term = match.group(1) or match.group(2) or match.group(3)
            if len(term) >= 2 and len(term) <= 60:
                terms.add(term.strip())

        if not terms:
            return ""

        lines = ["# Glossary\n"]
        for term in sorted(terms):
            lines.append(f"- **{term}**")
        return "\n".join(lines) + "\n"


def _content_warnings(text: str) -> list[str]:
    warnings = []
    word_count = len(text.split())
    if word_count < 2000:
        warnings.append(
            f"Book content is short ({word_count} words). "
            "May not contain enough material for strategy extraction."
        )
    return warnings


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9一-鿿]+", "-", title.lower())
    return slug.strip("-")[:60]
