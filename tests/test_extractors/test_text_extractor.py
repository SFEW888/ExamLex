"""Tests for text extractor."""
import tempfile
import unittest
from pathlib import Path

from examlex.scripts.extractors.text import TextExtractor


class TextExtractorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.output_dir = Path(self.tmp) / "artifacts"

    def test_extract_normal_text(self):
        src = Path(self.tmp) / "sample.md"
        src.write_text("# Hello\n\nThis is a test strategy.\n\n1. Step one\n2. Step two\n", encoding="utf-8")
        extractor = TextExtractor()
        result = extractor.extract(str(src), self.output_dir)
        self.assertEqual(result.source_type, "text")
        self.assertIn("full_text", result.artifacts)
        self.assertTrue(result.artifacts["full_text"].exists())
        content = result.artifacts["full_text"].read_text(encoding="utf-8")
        self.assertIn("Hello", content)
        self.assertIn("Step one", content)

    def test_strips_bom(self):
        src = Path(self.tmp) / "bom.txt"
        src.write_bytes("﻿content without BOM\n".encode("utf-8-sig"))
        extractor = TextExtractor()
        result = extractor.extract(str(src), self.output_dir)
        content = result.artifacts["full_text"].read_text(encoding="utf-8")
        self.assertTrue(content.startswith("content without BOM"))

    def test_short_content_warns(self):
        src = Path(self.tmp) / "short.txt"
        src.write_text("tiny", encoding="utf-8")
        extractor = TextExtractor()
        result = extractor.extract(str(src), self.output_dir)
        self.assertTrue(any("short" in w.lower() for w in result.warnings))

    def test_normalizes_line_endings(self):
        src = Path(self.tmp) / "crlf.txt"
        src.write_bytes(b"line1\r\nline2\rline3\n")
        extractor = TextExtractor()
        result = extractor.extract(str(src), self.output_dir)
        content = result.artifacts["full_text"].read_text(encoding="utf-8")
        self.assertNotIn("\r\n", content)
        self.assertNotIn("\r", content)

    def test_nonexistent_file_raises(self):
        extractor = TextExtractor()
        with self.assertRaises(FileNotFoundError):
            extractor.extract("/nonexistent/path.txt", self.output_dir)

    def test_no_tools_required(self):
        self.assertEqual(TextExtractor.check_dependencies(), [])


if __name__ == "__main__":
    unittest.main()
