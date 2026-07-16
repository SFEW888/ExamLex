"""Unified configuration management for the ExamLex.

Configuration priority (highest to lowest):
  1. CLI arguments / constructor kwargs
  2. Environment variables (SILICONFLOW_API_KEY, etc.)
  3. Code defaults

ExamLex deliberately does not auto-load ``.env`` files or user-home config
files. Deployments that use them must load/export values before starting.

Lazy dependency checking via DependencyReport.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path


DEFAULT_SESSION_RETENTION_HOURS = 168.0
DEFAULT_MAX_REPRODUCIBLE_ARTIFACT_BYTES = 4 * 1024 * 1024 * 1024
DEFAULT_STRATEGY_LIBRARY_WARNING_BYTES = 100 * 1024 * 1024


# ──────────────────────────────────────────────
# Dependency Report
# ──────────────────────────────────────────────


class DependencyReport:
    """Collects availability of external tools with install hints and feature mapping."""

    def __init__(self) -> None:
        self.available: dict[str, str] = {}     # tool → path
        self.missing: dict[str, str] = {}        # tool → install hint
        self.install_hints: dict[str, str] = {}
        self.features: dict[str, str] = {}        # tool → feature description

    def add(
        self,
        tool: str,
        *,
        available: bool,
        path: str | None = None,
        install_hint: str = "",
        feature: str = "",
    ) -> None:
        if available:
            self.available[tool] = path or tool
        else:
            self.missing[tool] = install_hint or f"install {tool}"
        if install_hint:
            self.install_hints[tool] = install_hint
        if feature:
            self.features[tool] = feature

    def all_available(self) -> bool:
        return len(self.missing) == 0

    def __bool__(self) -> bool:
        return self.all_available()

    def __repr__(self) -> str:
        lines = ["Dependency check for multi-source distillation:",""]
        # Show available tools
        for tool, path in sorted(self.available.items()):
            feat = self.features.get(tool, "")
            lines.append(f"  [OK] {tool}: {feat}  (found at {path})")
        # Show missing tools with feature + install command
        for tool, hint in sorted(self.missing.items()):
            feat = self.features.get(tool, "")
            lines.append(f"  [--] {tool}: {feat}")
            lines.append(f"       Install: {hint}")
            lines.append("")
        if not self.missing:
            lines.append("  All tools available. Full multi-source distillation is ready.")
        else:
            lines.append(f"  {len(self.available)}/{len(self.available)+len(self.missing)} tools available.")
            lines.append("  Missing tools only affect their specific feature;")
            lines.append("  text and person distillation work without any external tools.")
        return "\n".join(lines)


# ──────────────────────────────────────────────
# Platform helpers
# ──────────────────────────────────────────────


def _format_install_hint(tool: str, available: bool, inst_win: str, inst_mac: str, inst_linux: str) -> str:
    """Format platform-appropriate install instructions."""
    if available:
        return ""
    if os.name == "nt":
        return f"Windows: {inst_win}"
    try:
        is_mac = os.uname().sysname == "Darwin"
    except AttributeError:
        is_mac = False
    if is_mac:
        return f"macOS: {inst_mac}"
    return f"Linux: {inst_linux}"


def _safe_home() -> Path:
    """Return home directory, with fallbacks for sanitized environments."""
    # Try Path.home() first (respects HOME/USERPROFILE)
    try:
        return Path.home()
    except (RuntimeError, KeyError):
        pass
    # Try expanduser
    expanded = os.path.expanduser("~")
    if expanded and expanded != "~":
        return Path(expanded)
    # Last resort: use cwd
    return Path(os.getcwd())


def _default_sessions_root() -> Path:
    """Platform-appropriate default directory for session artifacts."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", str(_safe_home() / "AppData" / "Local"))
        return Path(base) / "ExamLex" / "sessions"
    try:
        is_mac = os.uname().sysname == "Darwin"
    except AttributeError:
        is_mac = False
    if is_mac:
        return _safe_home() / "Library" / "Application Support" / "ExamLex" / "sessions"
    return Path(
        os.environ.get("XDG_DATA_HOME", str(_safe_home() / ".local" / "share"))
    ) / "ExamLex" / "sessions"


def _default_strategy_library_path() -> Path:
    """Default durable strategy database next to the managed session root."""
    return _default_sessions_root().parent / "strategy-library.db"


# ──────────────────────────────────────────────
# TutorConfig
# ──────────────────────────────────────────────


@dataclass
class TutorConfig:
    """Unified configuration for the tutor pipeline.

    All fields can be set via constructor kwargs (highest priority),
    environment variables, or fall back to sensible defaults.
    """

    # ── Tool paths (None = auto-detect via which) ──
    yt_dlp_path: str | None = None
    ffmpeg_path: str | None = None
    whisper_path: str | None = None
    pdftotext_path: str | None = None
    calibre_ebook_convert: str | None = None

    # ── API keys (read from env if not provided) ──
    siliconflow_api_key: str | None = field(
        default_factory=lambda: os.environ.get("SILICONFLOW_API_KEY"),
        repr=False,
    )

    # ── ASR defaults ──
    asr_backend: str = "auto"       # auto | siliconflow | whisper | none
    asr_model: str = "base"
    asr_language: str = "auto"

    # ── Darwin scoring ──
    darwin_pass_score: float = 70.0
    darwin_max_rounds: int = 3
    darwin_touch_top_delta: float = 2.0   # 连续2轮 Δ < 此值 → 触顶

    # ── Session management ──
    sessions_root: Path = field(default_factory=_default_sessions_root)
    auto_cleanup: bool = True
    session_retention_hours: float = DEFAULT_SESSION_RETENTION_HOURS
    max_reproducible_artifact_bytes: int = DEFAULT_MAX_REPRODUCIBLE_ARTIFACT_BYTES
    strategy_library_path: Path = field(default_factory=_default_strategy_library_path)
    strategy_library_warning_bytes: int = DEFAULT_STRATEGY_LIBRARY_WARNING_BYTES

    # ── Content limits ──
    max_video_duration_seconds: int = 14400   # 4h hard limit
    warn_video_duration_seconds: int = 7200    # 2h warning
    min_text_length_chars: int = 500           # transcript minimum

    def to_dict(self) -> dict:
        d = asdict(self)
        d["sessions_root"] = str(d["sessions_root"])
        d["strategy_library_path"] = str(d["strategy_library_path"])
        # Redact sensitive values so the dict is safe to log or serialize.
        if d.get("siliconflow_api_key") is not None:
            d["siliconflow_api_key"] = "<redacted>"
        # Exclude None values
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> TutorConfig:
        if "sessions_root" in data and data["sessions_root"] is not None:
            data["sessions_root"] = Path(data["sessions_root"])
        if "strategy_library_path" in data and data["strategy_library_path"] is not None:
            data["strategy_library_path"] = Path(data["strategy_library_path"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    # Map a tool name to the config attribute holding its explicit path.
    _TOOL_TO_PATH_ATTR = {
        "yt-dlp": "yt_dlp_path",
        "ffmpeg": "ffmpeg_path",
        "whisper": "whisper_path",
        "pdftotext": "pdftotext_path",
        "ebook-convert": "calibre_ebook_convert",
    }

    def check_dependency(self, tool: str) -> bool:
        """Check if a single CLI tool is available (explicit path or PATH)."""
        attr = self._TOOL_TO_PATH_ATTR.get(tool)
        if attr:
            explicit = getattr(self, attr, None)
            if explicit:
                return Path(explicit).exists()
        return shutil.which(tool) is not None

    def check_all_dependencies(self) -> DependencyReport:
        """Produce a full dependency report for all tools this config references."""
        report = DependencyReport()

        # (tool, explicit_path, feature, install_win, install_mac, install_linux)
        _TOOLS = [
            ("yt-dlp", self.yt_dlp_path, "video download",
             "pip install yt-dlp", "pip3 install yt-dlp", "pip3 install yt-dlp"),
            ("ffmpeg", self.ffmpeg_path, "audio extraction from video",
             "winget install ffmpeg  or  choco install ffmpeg",
             "brew install ffmpeg", "apt install ffmpeg"),
            ("whisper", self.whisper_path, "local speech-to-text (video ASR)",
             "pip install openai-whisper", "pip3 install openai-whisper", "pip3 install openai-whisper"),
            ("pdftotext", self.pdftotext_path, "PDF book extraction",
             "winget install poppler  or  choco install poppler",
             "brew install poppler", "apt install poppler-utils"),
            ("ebook-convert", self.calibre_ebook_convert, "e-book conversion",
             "winget install calibre", "brew install calibre", "apt install calibre"),
        ]

        for name, explicit_path, feature, inst_win, inst_mac, inst_linux in _TOOLS:
            if explicit_path:
                available = Path(explicit_path).exists()
                path = explicit_path
            else:
                found = shutil.which(name)
                available = found is not None
                path = found or None
            hint = _format_install_hint(name, available, inst_win, inst_mac, inst_linux)
            report.add(name, available=available, path=path or None,
                       install_hint=hint, feature=feature)

        return report
