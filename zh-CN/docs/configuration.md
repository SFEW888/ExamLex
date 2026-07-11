# 配置

`examlex/scripts/config.py` 中的 `TutorConfig` 数据类是权威配置接口。

公开仓库无需密钥即可运行。配置项主要服务于本地实验或下游集成，均为可选。

## 配置优先级

配置按以下优先级从高到低解析：

1. 构造函数参数 / CLI 参数（最高）
2. 云端 ASR 密钥环境变量 `SILICONFLOW_API_KEY`
3. 代码默认值（最低）

ExamLex 不会自动加载 `.env`，也不会自动读取用户主目录下的 JSON 配置文件。

## `TutorConfig` 数据类

所有配置均由 `scripts/config.py` 中的 `TutorConfig` 管理。以下列出当前字段、默认值和用途。

### 外部工具路径

路径为 `None`（默认）时，程序通过 `shutil.which()` 从 `PATH` 自动查找工具。

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `yt_dlp_path` | `None`（自动检测） | 视频下载工具 `yt-dlp` 的显式路径 |
| `ffmpeg_path` | `None`（自动检测） | 用于流合并、媒体转换和音频提取的 `ffmpeg` 路径 |
| `whisper_path` | `None`（自动检测） | 本地语音转文字工具 OpenAI Whisper 的路径 |
| `pdftotext_path` | `None`（自动检测） | PDF 图书提取工具 Poppler `pdftotext` 的路径 |
| `calibre_ebook_convert` | `None`（自动检测） | 电子书转换工具 Calibre `ebook-convert` 的路径 |

### API 密钥

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `siliconflow_api_key` | 环境变量 `SILICONFLOW_API_KEY`，否则为 `None` | SiliconFlow ASR 服务密钥；未显式传入时从环境变量读取 |

### ASR（自动语音识别）默认值

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `asr_backend` | `"auto"` | ASR 后端：`auto`、`siliconflow`、`whisper`、`none` |
| `asr_model` | `"base"` | ASR 模型规格，例如 `base`、`small`、`medium`、`large` |
| `asr_language` | `"auto"` | ASR 语言提示；`auto` 表示自动检测 |

### Darwin 评分

Darwin 评分控制持续学习各轮的自适应通过阈值。

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `darwin_pass_score` | `70.0` | 0–100 分制下的最低通过分 |
| `darwin_max_rounds` | `3` | 达到强制停止前的最大评分轮数 |
| `darwin_touch_top_delta` | `2.0` | 连续两轮分数增量低于此值时视为触顶 |

### 会话管理

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `sessions_root` | 平台默认目录 | Windows：`%LOCALAPPDATA%/ExamLex/sessions`；macOS：`~/Library/Application Support/ExamLex/sessions`；Linux：`$XDG_DATA_HOME/ExamLex/sessions` |
| `auto_cleanup` | `True` | 是否自动清理旧会话产物 |

### 内容限制

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `max_video_duration_seconds` | `14400`（4 小时） | 可处理视频时长硬上限 |
| `warn_video_duration_seconds` | `7200`（2 小时） | 超过后显示警告的时长阈值 |
| `min_text_length_chars` | `500` | 允许处理的最短转写字符数 |

## 使用示例

### Python（构造函数参数）

```python
from examlex.scripts.config import TutorConfig

config = TutorConfig(
    ffmpeg_path="C:/tools/ffmpeg/bin/ffmpeg.exe",
    siliconflow_api_key="sk-...",
    asr_backend="siliconflow",
)
```

### 环境变量

在当前 Shell 中导出变量。除非你的环境工具主动加载，否则 `.env.example` 仅用于说明。

```powershell
$env:SILICONFLOW_API_KEY = "sk-..."
```

## 依赖检查

`TutorConfig.check_all_dependencies()` 返回 `DependencyReport`，说明哪些外部工具可用、哪些缺失，并给出当前平台的安装建议：

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)：视频下载
- [FFmpeg](https://ffmpeg.org/download.html)：合并独立媒体流，并在 ASR 前转换媒体或提取音频
- [Whisper](https://github.com/openai/whisper)：本地语音转文字
- [Poppler / pdftotext](https://poppler.freedesktop.org/)：PDF 图书提取
- [Calibre / ebook-convert](https://calibre-ebook.com/download)：电子书转换

使用 `TutorConfig.check_dependency("ffmpeg")` 可检查单个工具。

## 密钥处理

不要提交 `.env`、私有提示词文件、可识别学习者身份的记录、Token、密码或本地数据库凭据。

`TutorConfig.to_dict()` 会自动把 `siliconflow_api_key` 替换为 `<redacted>`，并排除值为 `None` 的字段，因此适合日志或序列化。

仓库验证器会检查 `pyproject.toml` 中的 public-safe 提示词模式，但贡献者仍须在发布前检查示例、截图、发布说明和 Issue 内容。
