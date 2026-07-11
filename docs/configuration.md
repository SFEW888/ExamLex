# Configuration

The `TutorConfig` dataclass in `examlex/scripts/config.py` is the authoritative configuration interface.

The public repository runs without secrets. Configuration is optional and mainly exists for local experiments or downstream integrations.

## Configuration Priority

Settings are resolved from highest to lowest priority:

1. Constructor kwargs / CLI arguments (highest priority)
2. `SILICONFLOW_API_KEY` for the cloud ASR key
3. Code defaults (lowest priority)

ExamLex does not automatically load `.env` or a user-home JSON configuration file.

## The `TutorConfig` Dataclass

All configuration is managed by the `TutorConfig` dataclass in `scripts/config.py`. Below are all fields, their defaults, and descriptions.

### Tool Paths

Paths to external CLI tools. When set to `None` (the default), the tool is located via `shutil.which()` (i.e. looked up on `PATH`).

| Field | Default | Description |
|-------|---------|-------------|
| `yt_dlp_path` | `None` (auto-detect) | Explicit path to `yt-dlp` for video download |
| `ffmpeg_path` | `None` (auto-detect) | Explicit path to `ffmpeg` for stream merging, media conversion, and audio extraction |
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
| `sessions_root` | Platform-specific default | Root directory for session artifacts. On Windows: `%LOCALAPPDATA%/ExamLex/sessions`. On macOS: `~/Library/Application Support/ExamLex/sessions`. On Linux: `$XDG_DATA_HOME/ExamLex/sessions` |
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
from examlex.scripts.config import TutorConfig

config = TutorConfig(
    ffmpeg_path="C:/tools/ffmpeg/bin/ffmpeg.exe",
    siliconflow_api_key="sk-...",
    asr_backend="siliconflow",
)
```

### Environment Variables

Export variables in the current shell. `.env.example` is documentation only unless your environment tooling loads it.

```bash
export SILICONFLOW_API_KEY="sk-..."
```

## Dependency Checking

`TutorConfig.check_all_dependencies()` produces a `DependencyReport` showing which external tools are available and which are missing, along with platform-specific install instructions. The report covers:

- `yt-dlp` — video download
- `ffmpeg` — merge separate media streams and convert/extract audio before ASR
- `whisper` (openai-whisper) — local speech-to-text
- `pdftotext` (poppler) — PDF book extraction
- `ebook-convert` (Calibre) — e-book conversion

Use `TutorConfig.check_dependency("ffmpeg")` to check a single tool.

## Secret Handling

Never commit `.env`, private prompt files, learner-identifying records, tokens, passwords, or local database credentials.

The `TutorConfig.to_dict()` method automatically redacts the `siliconflow_api_key` field (replaced with `<redacted>`) and excludes `None` values, making it safe for logging or serialization.

The repository validation script enforces the public-safe prompt mode in `pyproject.toml`, but contributors are still responsible for reviewing examples, screenshots, release notes, and issues before publishing.
