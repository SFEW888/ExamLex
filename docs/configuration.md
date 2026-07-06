# Configuration

> **Migration Notice:** This document now describes the `TutorConfig` dataclass (`scripts/config.py`), which is the authoritative configuration interface.
> The earlier environment-variable-based configuration (`ENGLISH_EXAM_TUTOR_PROMPT_MODE`, etc.) is **deprecated and no longer consumed by the code**.
> If you are migrating from the old env-var approach: simply remove those variables — `TutorConfig` uses code defaults for all settings.

The public repository runs without secrets. Configuration is optional and mainly exists for local experiments or downstream integrations.

## Configuration Priority

Settings are resolved from highest to lowest priority:

1. Constructor kwargs / CLI arguments (highest priority)
2. Environment variables (see per-field notes below)
3. `.env` file in project root
4. `~/.english-exam-ai-tutor/config.json`
5. Code defaults (lowest priority)

## The `TutorConfig` Dataclass

All configuration is managed by the `TutorConfig` dataclass in `scripts/config.py`. Below are all fields, their defaults, and descriptions.

### Tool Paths

Paths to external CLI tools. When set to `None` (the default), the tool is located via `shutil.which()` (i.e. looked up on `PATH`).

| Field | Default | Description |
|-------|---------|-------------|
| `yt_dlp_path` | `None` (auto-detect) | Explicit path to `yt-dlp` for video download |
| `ffmpeg_path` | `None` (auto-detect) | Explicit path to `ffmpeg` for audio extraction |
| `whisper_path` | `None` (auto-detect) | Explicit path to `whisper` (OpenAI Whisper) for local speech-to-text |
| `pdftotext_path` | `None` (auto-detect) | Explicit path to `pdftotext` (poppler) for PDF book extraction |
| `calibre_ebook_convert` | `None` (auto-detect) | Explicit path to `ebook-convert` (Calibre) for e-book conversion |

### API Keys

| Field | Default | Description |
|-------|---------|-------------|
| `siliconflow_api_key` | `SILICONFLOW_API_KEY` env var, or `None` | API key for SiliconFlow ASR service. Read from environment if not explicitly provided. |

### ASR (Automatic Speech Recognition) Defaults

| Field | Default | Description |
|-------|---------|-------------|
| `asr_backend` | `"auto"` | ASR backend selection. Options: `auto` (pick best available), `siliconflow`, `whisper`, `none` |
| `asr_model` | `"base"` | ASR model variant (e.g. `base`, `small`, `medium`, `large`) |
| `asr_language` | `"auto"` | Language hint for ASR. `"auto"` enables language detection |

### Darwin Scoring

The "Darwin" scoring system controls adaptive pass thresholds for learning rounds.

| Field | Default | Description |
|-------|---------|-------------|
| `darwin_pass_score` | `70.0` | Minimum passing score (0–100 scale) |
| `darwin_max_rounds` | `3` | Maximum number of scoring rounds before forced stop |
| `darwin_touch_top_delta` | `2.0` | If score delta stays below this value for 2 consecutive rounds, the learner is considered "topped out" |

### Session Management

| Field | Default | Description |
|-------|---------|-------------|
| `sessions_root` | Platform-specific default | Root directory for session artifacts. On Windows: `%LOCALAPPDATA%/english-exam-ai-tutor/sessions`. On macOS: `~/Library/Application Support/english-exam-ai-tutor/sessions`. On Linux: `$XDG_DATA_HOME/english-exam-ai-tutor/sessions` |
| `auto_cleanup` | `True` | Whether to automatically clean up old session artifacts |

### Content Limits

| Field | Default | Description |
|-------|---------|-------------|
| `max_video_duration_seconds` | `14400` (4 hours) | Hard limit on video duration for processing |
| `warn_video_duration_seconds` | `7200` (2 hours) | Threshold beyond which a warning is emitted |
| `min_text_length_chars` | `500` | Minimum transcript length (in characters) required for processing |

## Usage Examples

### Python (constructor kwargs)

```python
from skills.english_exam_ai_tutor.scripts.config import TutorConfig

config = TutorConfig(
    ffmpeg_path="C:/tools/ffmpeg/bin/ffmpeg.exe",
    siliconflow_api_key="sk-...",
    asr_backend="siliconflow",
)
```

### Environment Variables

```bash
export SILICONFLOW_API_KEY="sk-..."
```

### JSON Config File

Create `~/.english-exam-ai-tutor/config.json`:

```json
{
  "yt_dlp_path": "/usr/local/bin/yt-dlp",
  "asr_backend": "whisper",
  "asr_model": "medium",
  "darwin_pass_score": 75.0
}
```

## Dependency Checking

`TutorConfig.check_all_dependencies()` produces a `DependencyReport` showing which external tools are available and which are missing, along with platform-specific install instructions. The report covers:

- `yt-dlp` — video download
- `ffmpeg` — audio extraction from video
- `whisper` (openai-whisper) — local speech-to-text
- `pdftotext` (poppler) — PDF book extraction
- `ebook-convert` (Calibre) — e-book conversion

Use `TutorConfig.check_dependency("ffmpeg")` to check a single tool.

## Secret Handling

Never commit `.env`, private prompt files, learner-identifying records, tokens, passwords, or local database credentials.

The `TutorConfig.to_dict()` method automatically redacts the `siliconflow_api_key` field (replaced with `<redacted>`) and excludes `None` values, making it safe for logging or serialization.

The repository validation script enforces the public-safe prompt mode in `pyproject.toml`, but contributors are still responsible for reviewing examples, screenshots, release notes, and issues before publishing.
