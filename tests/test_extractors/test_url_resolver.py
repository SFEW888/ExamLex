"""Tests for URL resolver / input type detection."""
import unittest

from skills.english_exam_ai_tutor.scripts.extractors.url_resolver import (
    InputType,
    resolve_input,
)


class ResolveInputTests(unittest.TestCase):
    def test_bilibili_video_url(self):
        self.assertEqual(
            resolve_input("https://www.bilibili.com/video/BV1xx411c7mD"),
            InputType.URL_VIDEO,
        )

    def test_b23_tv_short_url(self):
        self.assertEqual(
            resolve_input("https://b23.tv/abc123"),
            InputType.URL_VIDEO,
        )

    def test_youtube_url(self):
        self.assertEqual(
            resolve_input("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            InputType.URL_VIDEO,
        )

    def test_youtu_be_short_url(self):
        self.assertEqual(
            resolve_input("https://youtu.be/dQw4w9WgXcQ"),
            InputType.URL_VIDEO,
        )

    def test_unknown_url(self):
        self.assertEqual(
            resolve_input("https://example.com/article"),
            InputType.URL_UNKNOWN,
        )

    def test_person_name(self):
        self.assertEqual(
            resolve_input("赖世雄"),
            InputType.PERSON_NAME,
        )

    def test_person_name_english(self):
        self.assertEqual(
            resolve_input("Paul Graham"),
            InputType.PERSON_NAME,
        )

    def test_empty_or_flag_returns_unknown(self):
        self.assertEqual(resolve_input("--help"), InputType.UNKNOWN)

    def test_pdf_file_extension(self):
        # File doesn't exist, but extension suggests book
        self.assertEqual(
            resolve_input("./books/cet4-guide.pdf"),
            InputType.LOCAL_BOOK,
        )


if __name__ == "__main__":
    unittest.main()
