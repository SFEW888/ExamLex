"""Tests for standardized error types."""
import unittest

from examlex.scripts.errors import (
    TutorError,
    ExtractionError,
    ValidationError,
    ASRError,
    DependencyError,
    NetworkError,
    DarwinError,
)


class TutorErrorTests(unittest.TestCase):
    def test_base_error_has_code_message_recoverable_remedy(self):
        err = TutorError("E001", "something went wrong", recoverable=True, remedy="try again")
        self.assertEqual(err.code, "E001")
        self.assertEqual(err.message, "something went wrong")
        self.assertTrue(err.recoverable)
        self.assertEqual(err.remedy, "try again")

    def test_base_error_defaults(self):
        err = TutorError("E000", "msg")
        self.assertFalse(err.recoverable)
        self.assertIsNone(err.remedy)

    def test_str_includes_code_and_message(self):
        err = TutorError("E001", "disk full")
        self.assertIn("E001", str(err))
        self.assertIn("disk full", str(err))

    def test_extraction_error_is_tutor_error(self):
        err = ExtractionError("download failed", remedy="check network")
        self.assertIsInstance(err, TutorError)
        self.assertEqual(err.code, "EXTRACTION_FAILED")

    def test_validation_error_has_code(self):
        err = ValidationError("missing required field")
        self.assertEqual(err.code, "VALIDATION_FAILED")

    def test_asr_error_has_code(self):
        err = ASRError("whisper not found")
        self.assertEqual(err.code, "ASR_FAILED")

    def test_dependency_error_includes_tool_name(self):
        err = DependencyError("yt-dlp", remedy="pip install yt-dlp")
        self.assertIn("yt-dlp", err.message)
        self.assertEqual(err.code, "DEPENDENCY_MISSING")

    def test_network_error_has_code(self):
        err = NetworkError("timeout after 30s")
        self.assertEqual(err.code, "NETWORK_FAILED")

    def test_darwin_error_has_code(self):
        err = DarwinError("score decreased from 80 to 75")
        self.assertEqual(err.code, "DARWIN_FAILED")

    def test_to_dict_contains_all_fields(self):
        err = ExtractionError("video download failed", recoverable=True, remedy="retry with --cookies")
        d = err.to_dict()
        self.assertEqual(d["code"], "EXTRACTION_FAILED")
        self.assertEqual(d["message"], "video download failed")
        self.assertTrue(d["recoverable"])
        self.assertEqual(d["remedy"], "retry with --cookies")

    def test_subclasses_inherit_fields(self):
        err = ASRError("SenseVoice API key missing", recoverable=True, remedy="set SILICONFLOW_API_KEY")
        d = err.to_dict()
        self.assertEqual(d["code"], "ASR_FAILED")
        self.assertTrue(d["recoverable"])
        self.assertIn("SILICONFLOW_API_KEY", d["remedy"])


if __name__ == "__main__":
    unittest.main()
