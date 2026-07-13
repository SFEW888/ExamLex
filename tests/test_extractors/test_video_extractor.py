"""Tests for video extractor — heavily mocked external tools."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from examlex.scripts.extractors.video import (
    VideoExtractor,
    _validate_video_url,
    _select_backend,
    _resolve_model,
    _build_ffmpeg_command,
)
from examlex.scripts.config import TutorConfig


PUBLIC_DNS = [
    (2, 1, 6, "", ("142.250.72.206", 443)),
]


class VideoExtractorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.output_dir = Path(self.tmp) / "artifacts"
        self.extractor = VideoExtractor()

    def test_check_dependencies_reports_missing(self):
        with mock.patch("shutil.which", return_value=None):
            missing = VideoExtractor.check_dependencies()
            self.assertIn("yt-dlp", missing)
            self.assertIn("ffmpeg", missing)

    def test_check_dependencies_all_present(self):
        with mock.patch("shutil.which", return_value="/usr/bin/tool"):
            missing = VideoExtractor.check_dependencies()
            self.assertEqual(missing, [])

    def test_extract_rejects_forced_http_video_before_tools_run(self):
        with mock.patch("shutil.which") as mock_which, mock.patch(
            "subprocess.run"
        ) as mock_run:
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                self.extractor.extract(
                    "http://www.youtube.com/watch?v=abc",
                    self.output_dir,
                )

        mock_which.assert_not_called()
        mock_run.assert_not_called()

    def test_video_url_rejects_userinfo_and_nonstandard_ports(self):
        for url in (
            "https://user@www.youtube.com/watch?v=abc",
            "https://www.youtube.com:8443/watch?v=abc",
            "https://www.youtube.com.evil.example/watch?v=abc",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _validate_video_url(url)

    @mock.patch(
        "examlex.scripts.extractors.video.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("127.0.0.1", 443))],
    )
    def test_video_url_rejects_private_dns_resolution(self, _mock_dns):
        with self.assertRaisesRegex(ValueError, "public"):
            _validate_video_url("https://www.youtube.com/watch?v=abc")

    @mock.patch(
        "examlex.scripts.extractors.video.socket.getaddrinfo",
        return_value=PUBLIC_DNS,
    )
    def test_video_url_accepts_exact_host_with_public_dns(self, _mock_dns):
        self.assertEqual(
            "https://www.youtube.com/watch?v=abc",
            _validate_video_url("https://www.youtube.com/watch?v=abc"),
        )

    @mock.patch("examlex.scripts.extractors.video.subprocess.run")
    @mock.patch("examlex.scripts.extractors.video.shutil.which", return_value="yt-dlp")
    def test_ytdlp_commands_separate_option_like_urls(self, _mock_which, mock_run):
        url = "https://www.youtube.com/watch?v=--config-location"
        mock_run.return_value = mock.MagicMock(
            returncode=0,
            stdout='{"id": "abc", "title": "test"}',
            stderr="",
        )

        self.extractor._extract_metadata(url)
        metadata_command = mock_run.call_args.args[0]
        self.assertEqual(["--", url], metadata_command[-2:])

        def create_download(command, **_kwargs):
            output = Path(command[command.index("-o") + 1])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"video")
            return mock.MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_download
        self.extractor._download_video(url, self.output_dir, {"title": "test"}, "abc")
        download_command = mock_run.call_args.args[0]
        self.assertEqual(["--", url], download_command[-2:])

    @mock.patch("examlex.scripts.extractors.video._validate_video_url")
    @mock.patch("examlex.scripts.extractors.video.shutil.which", return_value="tool")
    def test_extractor_respects_disabled_asr(self, _mock_which, mock_validate):
        extractor = VideoExtractor(TutorConfig(asr_backend="none"))
        mock_validate.return_value = "https://www.youtube.com/watch?v=abc"
        video = self.output_dir / "video.mp4"
        video.parent.mkdir(parents=True, exist_ok=True)
        video.write_bytes(b"video")

        with mock.patch.object(
            extractor, "_extract_metadata", return_value={"id": "abc", "duration": 1}
        ), mock.patch.object(
            extractor, "_download_video", return_value=video
        ), mock.patch(
            "examlex.scripts.extractors.video._extract_audio"
        ) as mock_audio:
            result = extractor.extract(mock_validate.return_value, self.output_dir)

        self.assertNotIn("transcript", result.artifacts)
        mock_audio.assert_not_called()

    @mock.patch(
        "examlex.scripts.extractors.video.socket.getaddrinfo",
        return_value=PUBLIC_DNS,
    )
    @mock.patch("subprocess.run")
    @mock.patch("shutil.which")
    @mock.patch.dict("os.environ", {"SILICONFLOW_API_KEY": ""}, clear=False)
    def test_extract_bilibili_full_flow(self, mock_which, mock_run, _mock_dns):
        mock_which.return_value = "/usr/bin/yt-dlp"
        yt_meta = json.dumps({
            "id": "BV1xx411c7mD", "title": "四级阅读技巧",
            "description": "CET4 reading strategies",
            "uploader": "英语老师", "duration": 1800.0,
            "width": 1920, "height": 1080,
        })

        def run_side_effect(*args, **kwargs):
            cmd = args[0] if args else []
            cmd_str = " ".join(str(c) for c in cmd)
            result = mock.MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            if "--dump-single-json" in cmd_str:
                result.stdout = yt_meta
            elif "whisper" in cmd_str:
                # Find --output_dir value and create fake output
                try:
                    odir_idx = cmd.index("--output_dir") + 1
                    tmp_dir = Path(cmd[odir_idx])
                    tmp_dir.mkdir(parents=True, exist_ok=True)
                    audio_stem = Path(cmd[2]).stem
                    (tmp_dir / f"{audio_stem}.json").write_text(
                        '{"text": "预读题干可以节省阅读时间"}', encoding="utf-8")
                except (ValueError, IndexError):
                    pass
            elif "ffmpeg" in cmd_str:
                output_file = Path(cmd[-1])
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake audio data")
            elif "-o" in cmd_str:
                try:
                    o_idx = cmd.index("-o") + 1
                    video_path = Path(cmd[o_idx])
                    video_path.parent.mkdir(parents=True, exist_ok=True)
                    video_path.write_bytes(b"fake video data")
                except (ValueError, IndexError):
                    pass
            return result

        mock_run.side_effect = run_side_effect

        result = self.extractor.extract(
            "https://www.bilibili.com/video/BV1xx411c7mD",
            self.output_dir,
        )
        self.assertEqual(result.source_type, "video")
        self.assertIsNotNone(result.metadata.get("duration_seconds"))

    def test_supported_urls(self):
        self.assertTrue(self.extractor._supports("https://www.bilibili.com/video/BV1xx"))
        self.assertTrue(self.extractor._supports("https://www.youtube.com/watch?v=abc"))
        self.assertFalse(self.extractor._supports("https://example.com/video"))


class ASRHelperTests(unittest.TestCase):
    def test_auto_backend_never_selects_cloud_asr(self):
        with mock.patch.dict("os.environ", {"SILICONFLOW_API_KEY": "sk-test"}):
            with mock.patch("shutil.which", return_value=None):
                self.assertIsNone(_select_backend("auto"))

    def test_explicit_siliconflow_backend_uses_cloud_asr(self):
        with mock.patch.dict("os.environ", {"SILICONFLOW_API_KEY": "sk-test"}):
            self.assertEqual(_select_backend("siliconflow"), "siliconflow")

    def test_explicit_siliconflow_backend_accepts_config_key(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                _select_backend("siliconflow", api_key="sk-configured"),
                "siliconflow",
            )

    def test_none_backend_disables_asr(self):
        with mock.patch.dict("os.environ", {"SILICONFLOW_API_KEY": "sk-test"}):
            self.assertIsNone(_select_backend("none"))

    @mock.patch("shutil.which", return_value="/usr/bin/whisper")
    def test_select_backend_whisper_when_no_api_key(self, _mock_which):
        with mock.patch.dict("os.environ", {}, clear=True):
            # Need PATH for which to work
            self.assertEqual(_select_backend("whisper"), "whisper")

    def test_select_backend_none_when_nothing_available(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch("shutil.which", return_value=None):
                self.assertIsNone(_select_backend("auto"))

    def test_resolve_model_whisper_auto(self):
        self.assertEqual(_resolve_model("whisper", "auto"), "base")

    def test_resolve_model_siliconflow_auto(self):
        self.assertEqual(_resolve_model("siliconflow", "auto"), "FunAudioLLM/SenseVoiceSmall")

    def test_build_ffmpeg_command_mp3(self):
        video = Path("/tmp/test.mp4")
        audio = Path("/tmp/test.mp3")
        cmd = _build_ffmpeg_command(video, audio)
        self.assertIn("-codec:a", cmd)
        self.assertIn("libmp3lame", cmd)

    def test_build_ffmpeg_command_m4a(self):
        video = Path("/tmp/test.mp4")
        audio = Path("/tmp/test.m4a")
        cmd = _build_ffmpeg_command(video, audio)
        self.assertNotIn("libmp3lame", cmd)


if __name__ == "__main__":
    unittest.main()
