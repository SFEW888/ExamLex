# 配置

`examlex/scripts/config.py` 中的 `TutorConfig` 数据类是权威配置接口。

公开仓库无需密钥即可运行。配置项主要服务于本地实验或下游集成，均为可选。

## 配置优先级

配置按以下优先级从高到低解析：

1. 构造函数参数 / CLI 参数（最高）
2. `SILICONFLOW_API_KEY` 等环境变量
3. 代码默认值（最低）

ExamLex 不会自动加载 `.env`。私有助教运行时另行支持一个范围严格受限的用户主目录 JSON 文件，其中只保存外部提示词目录。

`examlex ops-check` 默认生成可分享的隐私安全报告：主机名、本地绝对路径、凭据、
服务商响应正文和原始异常文本均不会写入报告。学习者产物以及你手动追加的诊断
信息仍应视为私有数据。

私有提示词目录使用独立优先级：显式 `run_tutor_turn()` 或 CLI 参数、`EXAMLEX_PRIVATE_PROMPT_DIR`、`~/.examlex/prompt-config.json`。

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

`TutorConfig` 的对象表示不会包含 API 密钥，`to_dict()` 也会把它脱敏。云端
ASR 请求拒绝重定向，异常中不会包含服务商响应正文；只有显式选择
`asr_backend="siliconflow"` 后才上传音频。

视频下载默认匿名进行。设置 `EXAMLEX_YTDLP_COOKIES_FROM_BROWSER=1` 后，才会在
受支持的视频站点上使用 Chrome 浏览器 Cookie 重试。Cookie 可能包含账号访问
权限，建议使用独立浏览器配置、绝不公开 Cookie 文件，并在使用后关闭该开关。

### ASR（自动语音识别）默认值

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `asr_backend` | `"auto"` | ASR 后端：`auto` 仅在本地 Whisper 可用时启用，不会自动选择云服务；`siliconflow` 必须显式选择；`none` 完全关闭 ASR。 |
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
| `auto_cleanup` | `True` | 受管会话成功提交后自动执行保留策略 |
| `session_retention_hours` | `168.0` | 已完成会话的可再生成产物保留七天后自动清理 |
| `max_reproducible_artifact_bytes` | `4294967296`（4 GiB） | 已完成会话中的全文、音频、转录稿和章节提取物硬上限；超过时从最旧产物开始清理 |
| `strategy_library_path` | 与 `sessions_root` 同级的 `strategy-library.db` | 后台容量任务默认监控的事务型策略数据库 |
| `strategy_library_warning_bytes` | `104857600`（100 MiB） | 达到阈值时提醒并列出可能重复项供用户复核；不自动删除策略或不可变历史版本 |

4 GiB 上限只计算已完成会话的可再生成产物。提取过程中，活动会话的工作文件可能暂时
超过该值；管线状态、蒸馏策略、验证/评估报告和审计文件不在自动删除范围内。

Windows 可运行 `scripts/install_capacity_monitor.ps1` 注册当前用户计划任务，默认每
30 分钟执行一次。`examlex capacity-monitor` 是跨平台的单次执行形式，并始终写入
状态文件。

### 题源语料目录

`source-list` 不访问网络。`source-collect` 默认写入系统本地的
`ExamLex/source-corpus`，也可以用 `--output-dir` 指定目录。默认采用
`--content-mode metadata`、最多 20 条，并在请求之间等待 1 秒。
`source-fetch --kind media` 默认硬限制为 100 MiB，可用 `--max-media-mb`
调整，最大 1024 MiB。

题源语料使用 CLI 参数而不是秘密环境变量；采集器不会读取浏览器 Cookie 或
API 密钥。

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
    siliconflow_api_key="YOUR_SILICONFLOW_API_KEY",
    asr_backend="siliconflow",
)
```

### 环境变量

在当前 Shell 中导出变量。除非你的环境工具主动加载，否则 `.env.example` 仅用于说明。

```powershell
$env:SILICONFLOW_API_KEY = "YOUR_SILICONFLOW_API_KEY"
$env:EXAMLEX_PRIVATE_PROMPT_DIR = "D:\path\outside\the\ExamLex\repository"
```

### 私有助教运行时

校验并保存外部目录，且不在输出中显示路径或提示词正文：

```powershell
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --save
python run.py tutor-prepare --request "润色这封正式邮件：..." --json
```

保存文件只含 `schema_version` 和外部目录路径。它是本地状态，不属于 `TutorConfig`，绝不能提交。`tutor-prepare` 只是公开安全的预检；只有传给 `run_tutor_turn()` 的受信进程内提供器才能执行私有提示词。

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
