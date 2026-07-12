"""Tests for book extractor."""
import shutil
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

from examlex.scripts.extractors.book import BookExtractor


class BookExtractorTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2] / ".task8-test-tmp"
        root.mkdir(parents=True, exist_ok=True)
        self.tmp = str(root / f"book-{uuid.uuid4().hex}")
        Path(self.tmp).mkdir()
        self.output_dir = Path(self.tmp) / "artifacts"
        self.extractor = BookExtractor()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_epub(self, name, entries):
        path = Path(self.tmp) / name
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for filename, content in entries:
                archive.writestr(filename, content)
        return path

    def test_epub_rejects_excessive_entry_count(self):
        source = self._write_epub("entries.epub", [("a.xhtml", "a"), ("b.xhtml", "b")])
        with patch.object(BookExtractor, "MAX_EPUB_ENTRIES", 1):
            with self.assertRaisesRegex(ValueError, "entry count"):
                self.extractor._extract_epub_simple(source)

    def test_epub_rejects_large_html_entry(self):
        source = self._write_epub("large.epub", [("a.xhtml", "a" * 20)])
        with patch.object(BookExtractor, "MAX_EPUB_HTML_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "HTML entry"):
                self.extractor._extract_epub_simple(source)

    def test_epub_rejects_large_total_html(self):
        source = self._write_epub(
            "total.epub", [("a.xhtml", "a" * 10), ("b.xhtml", "b" * 10)]
        )
        with patch.object(BookExtractor, "MAX_EPUB_TOTAL_HTML_BYTES", 15):
            with self.assertRaisesRegex(ValueError, "total HTML"):
                self.extractor._extract_epub_simple(source)

    def test_epub_rejects_suspicious_compression_ratio(self):
        source = self._write_epub("ratio.epub", [("a.xhtml", "a" * 1000)])
        with patch.object(BookExtractor, "MAX_EPUB_COMPRESSION_RATIO", 2):
            with self.assertRaisesRegex(ValueError, "compression ratio"):
                self.extractor._extract_epub_simple(source)

    def test_check_dependencies_empty(self):
        # Book extractor has no hard requirements (uses Python libs)
        missing = BookExtractor.check_dependencies()
        # pdftotext and calibre are optional
        self.assertNotIn("python", missing)

    def test_extract_txt_book(self):
        # Create a mock book as a text file
        src = Path(self.tmp) / "cet4-book.txt"
        src.write_text(
            "# CET4 Reading Guide\n\n"
            "## Chapter 1: Speed Reading\n\n"
            "快速阅读的核心是预读题干。When you preview questions first...\n\n"
            "### Method 1: 关键词定位法\n\n"
            "1. Scan all questions in 30 seconds\n"
            "2. Circle keywords in each question\n"
            "3. Locate each keyword in the passage\n\n"
            "## Chapter 2: Vocabulary Inference\n\n"
            "遇到生词时不要立刻查字典。Instead, infer meaning from context.\n\n"
            "## Chapter 3: Long Sentence Analysis\n\n"
            "长难句先找主谓宾。Find subject, verb, object first.\n",
            encoding="utf-8",
        )

        result = self.extractor.extract(str(src), self.output_dir)
        self.assertEqual(result.source_type, "book")
        self.assertIn("full_text", result.artifacts)
        self.assertTrue(result.artifacts["full_text"].exists())
        self.assertGreater(result.metadata.get("char_count", 0), 100)

    def test_detects_chapters(self):
        text = (
            "# Chapter 1: Introduction\nContent here\n\n"
            "## Chapter 2: Methods\nMore content\n\n"
            "# Chapter 3: Practice\nEven more\n"
        )
        chapters = self.extractor._detect_chapters(text)
        self.assertGreaterEqual(len(chapters), 3)

    def test_extract_markdown_book(self):
        src = Path(self.tmp) / "guide.md"
        content = """# 四级词汇突破

## Chapter 1: 词根记忆法

通过词根记忆单词是最有效的方法。

### 常见前缀
- pre- = before
- re- = again

## Chapter 2: 联想记忆

将单词与熟悉的事物建立联系。

## Chapter 3: 语境记忆

在句子中记忆单词的使用场景。
"""
        src.write_text(content, encoding="utf-8")
        result = self.extractor.extract(str(src), self.output_dir)
        self.assertIn("full_text", result.artifacts)
        chapters = self.extractor._detect_chapters(
            result.artifacts["full_text"].read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(len(chapters), 3)

    def test_short_book_warns(self):
        src = Path(self.tmp) / "tiny.txt"
        src.write_text("very short book", encoding="utf-8")
        result = self.extractor.extract(str(src), self.output_dir)
        short_warnings = [w for w in result.warnings if "short" in w.lower()]
        self.assertGreater(len(short_warnings), 0)

    def test_unsupported_format_raises(self):
        src = Path(self.tmp) / "book.xyz"
        src.write_text("content", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.extractor.extract(str(src), self.output_dir)


if __name__ == "__main__":
    unittest.main()
