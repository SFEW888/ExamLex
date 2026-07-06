"""Video extractor — download, audio extraction, and ASR transcription.

Adapted from kangarooking/video-downloader's provider pattern.
Supports Bilibili and YouTube via yt-dlp. Audio extracted with ffmpeg,
transcribed via SenseVoiceSmall (SiliconFlow API) or local whisper CLI.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import BaseExtractor, ExtractionResult


# ── URL detection ──────────────────────────────────

_VIDEO_HOSTS = [
    r"(?:www\.)?bilibili\.com",
    r"(?:www\.)?b23\.tv",
    r"(?:www\.)?youtube\.com",
    r"(?:www\.)?youtu\.be",
    r"(?:www\.)?v\.douyin\.com",
    r"(?:www\.)?xiaohongshu\.com",
    r"(?:www\.)?xhslink\.com",
]

_VIDEO_PATTERN = re.compile(
    r"^https?://(" + "|".join(_VIDEO_HOSTS) + r")/", re.IGNORECASE
)

# ── SiliconFlow ASR ────────────────────────────────

SILICONFLOW_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"
SILICONFLOW_MODEL = "FunAudioLLM/SenseVoiceSmall"


def _cookie_retry_enabled() -> bool:
    """Whether to retry yt-dlp with browser cookies.

    Off by default: `--cookies-from-browser chrome` sends the user's Chrome
    session cookies to the target URL, which a crafted/compromised URL could
    exfiltrate. Enable explicitly by setting TUTOR_YTDLP_COOKIES_FROM_BROWSER=1.
    """
    return os.environ.get("TUTOR_YTDLP_COOKIES_FROM_BROWSER", "").strip().lower() in (
        "1", "true", "yes",
    )


# ── Extractor ──────────────────────────────────────


class VideoExtractor(BaseExtractor):
    SUPPORTED_INPUTS = [
        "url:bilibili.com", "url:b23.tv",
        "url:youtube.com", "url:youtu.be",
        "url:douyin.com", "url:v.douyin.com",
        "url:xiaohongshu.com", "url:xhslink.com",
    ]
    REQUIRED_TOOLS = ["yt-dlp", "ffmpeg"]

    def extract(self, input_ref: str, output_dir: Path) -> ExtractionResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        warnings: list[str] = []

        # 1. Check tools
        for tool in self.REQUIRED_TOOLS:
            if not shutil.which(tool):
                raise FileNotFoundError(
                    f"{tool} is required but not found. Install it and retry."
                )

        # 2. Download video + metadata via yt-dlp
        metadata = self._extract_metadata(input_ref)

        # Validate duration before any expensive download/ASR work
        duration = metadata.get("duration") or 0
        if duration > 14400:  # 4h
            raise ValueError(
                f"Video too long ({duration}s, >4h). Refusing to process."
            )
        if duration > 7200:  # 2h
            warnings.append(f"Video is {duration}s (>2h). Transcription may be slow.")

        item_id = self._item_id(metadata)
        video_path = self._download_video(input_ref, output_dir, metadata, item_id)

        # 3. Write post caption
        caption = self._post_caption(metadata)
        caption_path = output_dir / "post_caption.txt"
        caption_path.write_text(caption, encoding="utf-8")

        # 4. Write metadata
        meta_path = output_dir / "metadata.json"
        normalized = self._normalize_metadata(input_ref, metadata, item_id, caption, video_path)
        meta_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        artifacts = {
            "video": video_path,
            "post_caption": caption_path,
            "metadata": meta_path,
        }

        # 5. ASR
        backend = _select_backend("auto")
        if backend and video_path:
            try:
                model = _resolve_model(backend, "auto")
                audio_suffix = ".mp3" if backend == "siliconflow" else ".m4a"
                audio_path = output_dir / f"audio{audio_suffix}"
                transcript_path = output_dir / "transcript.txt"

                _extract_audio(video_path, audio_path)

                if backend == "siliconflow":
                    _transcribe_siliconflow(audio_path, transcript_path,
                                            output_dir / "transcript.siliconflow.json", model)
                else:
                    _transcribe_whisper(audio_path, output_dir, transcript_path,
                                        output_dir / "transcript.whisper.json", model)

                artifacts["audio"] = audio_path
                artifacts["transcript"] = transcript_path
            except RuntimeError as exc:
                warnings.append(f"ASR failed ({backend}): {exc}")

        return ExtractionResult(
            source_type="video",
            input_ref=input_ref,
            artifacts=artifacts,
            metadata={
                "platform": self._detect_platform(input_ref),
                "duration_seconds": duration,
                "title": metadata.get("title", ""),
                "uploader": metadata.get("uploader") or metadata.get("channel", ""),
                "word_count_approx": _count_words(artifacts.get("transcript")),
            },
            warnings=warnings,
        )

    # ── URL support ──

    def _supports(self, url: str) -> bool:
        return bool(_VIDEO_PATTERN.search(url))

    def _detect_platform(self, url: str) -> str:
        host = urlparse(url).netloc.lower()
        if "bilibili" in host or "b23.tv" in host:
            return "bilibili"
        if "youtube" in host or "youtu.be" in host:
            return "youtube"
        if "douyin" in host:
            return "douyin"
        if "xiaohongshu" in host or "xhslink" in host:
            return "xiaohongshu"
        return "unknown"

    # ── yt-dlp wrappers ──

    def _extract_metadata(self, url: str) -> dict:
        yt_dlp = shutil.which("yt-dlp")
        if not yt_dlp:
            raise FileNotFoundError(
                "yt-dlp is required but not found. Install it and retry."
            )
        cmd = [yt_dlp, "--no-playlist", "--dump-single-json", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0 and _cookie_retry_enabled():
            # Opt-in retry with browser cookies (see _cookie_retry_enabled)
            cmd2 = [yt_dlp, "--cookies-from-browser", "chrome", "--no-playlist",
                    "--dump-single-json", url]
            result = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp metadata extraction failed: {result.stderr[:500]}")
        return json.loads(result.stdout)

    def _download_video(self, url: str, folder: Path,
                        metadata: dict, item_id: str) -> Path:
        yt_dlp = shutil.which("yt-dlp")
        if not yt_dlp:
            raise FileNotFoundError(
                "yt-dlp is required but not found. Install it and retry."
            )
        stem = _safe_filename(metadata.get("title"), item_id)
        output_path = folder / f"{stem}.mp4"
        cmd = [
            yt_dlp, "--no-playlist", "-f", "bv*+ba/b",
            "--merge-output-format", "mp4", "-o", str(output_path), url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0 and _cookie_retry_enabled():
            # Opt-in retry with browser cookies (see _cookie_retry_enabled)
            cmd2 = [yt_dlp, "--cookies-from-browser", "chrome", "--no-playlist",
                    "-f", "bv*+ba/b", "--merge-output-format", "mp4",
                    "-o", str(output_path), url]
            result = subprocess.run(cmd2, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp download failed: {result.stderr[:500]}")
        if output_path.exists():
            return output_path
        matches = sorted(folder.glob(f"{stem}.*"))
        if matches:
            return matches[0]
        raise RuntimeError("yt-dlp completed but no video file found")

    # ── Metadata helpers ──

    def _item_id(self, metadata: dict) -> str:
        for key in ("id", "display_id", "webpage_url_basename"):
            value = metadata.get(key)
            if value:
                sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-")
                if sanitized:
                    return sanitized
        return "unknown"

    def _post_caption(self, metadata: dict) -> str:
        parts = []
        title = (metadata.get("title") or "").strip()
        desc = (metadata.get("description") or "").strip()
        if title:
            parts.append(title)
        if desc and desc != title:
            parts.append(desc)
        return "\n\n".join(parts)

    def _normalize_metadata(self, source_url: str, metadata: dict,
                            item_id: str, caption: str,
                            video_path: Path | None) -> dict:
        width = metadata.get("width")
        height = metadata.get("height")
        from time import strftime
        return {
            "platform": self._detect_platform(source_url),
            "source_url": source_url,
            "final_url": metadata.get("webpage_url") or source_url,
            "fetched_at": strftime("%Y-%m-%dT%H:%M:%S%z"),
            "id": item_id,
            "caption": caption,
            "title": metadata.get("title"),
            "description": metadata.get("description"),
            "author": {
                "nickname": metadata.get("uploader") or metadata.get("channel"),
                "id": metadata.get("uploader_id") or metadata.get("channel_id"),
            },
            "video": {
                "width": width, "height": height,
                "resolution": f"{width}x{height}" if width and height else None,
                "duration_seconds": metadata.get("duration"),
            },
            "download": {
                "method": "yt_dlp",
                "video_path": str(video_path) if video_path else None,
            },
        }


# ── ASR helpers ────────────────────────────────────


def _select_backend(backend: str) -> str | None:
    if backend == "siliconflow":
        if not os.environ.get("SILICONFLOW_API_KEY"):
            raise RuntimeError("SILICONFLOW_API_KEY not set")
        return "siliconflow"
    if backend == "whisper":
        if not shutil.which("whisper"):
            raise RuntimeError("whisper CLI not found")
        return "whisper"
    if backend == "auto":
        if os.environ.get("SILICONFLOW_API_KEY"):
            return "siliconflow"
        if shutil.which("whisper"):
            return "whisper"
        return None
    raise RuntimeError(f"Unsupported ASR backend: {backend}")


def _resolve_model(backend: str, model: str) -> str:
    if backend == "siliconflow" and model in ("auto", "base", ""):
        return SILICONFLOW_MODEL
    if backend == "whisper" and model in ("auto", ""):
        return "base"
    return model


def _build_ffmpeg_command(video_path: Path, audio_path: Path) -> list[str]:
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
    ]
    if audio_path.suffix.lower() == ".mp3":
        cmd.extend(["-codec:a", "libmp3lame"])
    cmd.append(str(audio_path))
    return cmd


def _extract_audio(video_path: Path, audio_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found")
    cmd = _build_ffmpeg_command(video_path, audio_path)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg extraction failed: {result.stderr[:500]}")


def _transcribe_whisper(audio_path: Path, output_dir: Path,
                        transcript_path: Path, json_path: Path,
                        model: str = "base", language: str = "auto") -> None:
    whisper = shutil.which("whisper")
    if not whisper:
        raise RuntimeError("whisper CLI not found")
    with tempfile.TemporaryDirectory(dir=str(output_dir)) as tmp:
        cmd = [
            whisper, str(audio_path), "--model", model,
            "--output_dir", tmp, "--output_format", "json",
            "--task", "transcribe", "--fp16", "False", "--verbose", "False",
        ]
        if language and language.lower() != "auto":
            cmd.extend(["--language", language])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            raise RuntimeError(f"whisper failed: {result.stderr[:500]}")

        src = Path(tmp) / f"{audio_path.stem}.json"
        if not src.exists():
            raise RuntimeError("whisper produced no JSON output")
        data = json.loads(src.read_text(encoding="utf-8"))
        text = (data.get("text") or "").strip()
        transcript_path.write_text(text + ("\n" if text else ""), encoding="utf-8")
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _transcribe_siliconflow(audio_path: Path, transcript_path: Path,
                            json_path: Path, model: str) -> None:
    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not api_key:
        raise RuntimeError("SILICONFLOW_API_KEY not set")

    file_size = audio_path.stat().st_size
    max_size = 200 * 1024 * 1024  # 200 MB safety limit
    if file_size > max_size:
        raise RuntimeError(
            f"Audio file too large ({file_size} bytes, >{max_size})"
        )

    boundary = f"----tutor-{uuid.uuid4().hex}"
    body_parts = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="model"\r\n\r\n',
        model.encode(), b"\r\n",
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{audio_path.name}"\r\n'.encode(),
        b"Content-Type: audio/mpeg\r\n\r\n",
        audio_path.read_bytes(), b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    body = b"".join(body_parts)

    req = Request(
        SILICONFLOW_URL, data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SiliconFlow HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"SiliconFlow network error: {exc}") from exc

    text = (data.get("text") or "").strip()
    if not text:
        raise RuntimeError("SiliconFlow returned empty transcript")
    transcript_path.write_text(text + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Utilities ──────────────────────────────────────


def _safe_filename(title: str | None, item_id: str) -> str:
    stem = title or item_id
    stem = re.sub(r"[\\/:*?\"<>|\n\r\t]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem[:80].strip() or item_id


def _count_words(path: Path | None) -> int | None:
    if not path or not path.exists():
        return None
    return len(path.read_text(encoding="utf-8").split())
