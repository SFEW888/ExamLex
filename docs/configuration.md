# Configuration

The `TutorConfig` dataclass in `examlex/scripts/config.py` is the authoritative configuration interface.

The public repository runs without secrets. Configuration is optional and mainly exists for local experiments or downstream integrations.

## Configuration Priority

Settings are resolved from highest to lowest priority:

1. Constructor kwargs / CLI arguments (highest priority)
2. Environment variables such as `SILICONFLOW_API_KEY`
3. Code defaults (lowest priority)

ExamLex does not automatically load `.env`. The private tutor runtime separately supports a narrowly scoped user-home JSON file containing only its external prompt directory.

`examlex ops-check` produces a shareable, privacy-safe report by default: hostnames,
absolute local paths, credentials, provider response bodies, and raw exception text
are omitted. Treat learner artifacts and any manually added diagnostic output as
private data nonetheless.

The private prompt directory has its own order: an explicit `run_tutor_turn()` or CLI argument, `EXAMLEX_PRIVATE_PROMPT_DIR`, then `~/.examlex/prompt-config.json`.

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

`TutorConfig` never includes the API key in its representation, and `to_dict()`
redacts it. The cloud ASR request rejects redirects and does not include provider
response bodies in raised errors. Audio is uploaded only after explicitly selecting
`asr_backend="siliconflow"`.

Video downloads are anonymous by default. Setting
`EXAMLEX_YTDLP_COOKIES_FROM_BROWSER=1` opts into a retry with Chrome browser cookies
for supported video sites. Because those cookies may grant account access, prefer a
separate browser profile, do not publish cookie files, and unset the flag after use.

### ASR (Automatic Speech Recognition) Defaults

| Field | Default | Description |
|-------|---------|-------------|
| `asr_backend` | `"auto"` | ASR backend selection. `auto` uses local Whisper when available and never selects a cloud service; `siliconflow` must be selected explicitly; `none` disables ASR. |
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

### Source Corpus

`source-list` needs no network access. `source-collect` writes to the platform
default `ExamLex/source-corpus` directory unless `--output-dir` is supplied.
The collector defaults to `--content-mode metadata`, a 20-item limit, and a
one-second delay between requests. `source-fetch --kind media` has a 100 MiB
default hard limit, adjustable with `--max-media-mb` up to 1024 MiB.

Corpus settings are CLI-scoped rather than secret environment variables. The
collector never reads browser cookies or API keys.

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
    siliconflow_api_key="YOUR_SILICONFLOW_API_KEY",
    asr_backend="siliconflow",
)
```

### Environment Variables

Export variables in the current shell. `.env.example` is documentation only unless your environment tooling loads it.

```bash
export SILICONFLOW_API_KEY="YOUR_SILICONFLOW_API_KEY"
export EXAMLEX_PRIVATE_PROMPT_DIR="/path/outside/the/ExamLex/repository"
```

### Private tutor runtime

Validate and persist the external directory without printing its path or prompt contents:

```powershell
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --save
python run.py tutor-prepare --request "Polish this formal email: ..." --json
```

The saved file contains only `schema_version` and the external directory path. It is local state, not part of `TutorConfig`, and must not be committed. The `tutor-prepare` command is a public-safe preflight; only a trusted in-process provider passed to `run_tutor_turn()` can execute private prompts.

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
