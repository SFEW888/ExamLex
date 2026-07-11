# 配置

`examlex/scripts/config.py` 中的 `TutorConfig` 数据类是权威配置接口。公共仓库无需密钥即可运行。

配置优先级为：构造参数或 CLI 参数、`SILICONFLOW_API_KEY`、代码默认值。ExamLex 不会自动加载 `.env` 或用户目录中的 JSON 配置文件。

## 外部工具路径

工具路径默认为 `None`，ExamLex 会通过系统 `PATH` 自动查找。也可以在 `TutorConfig` 中显式指定：

| 字段 | 默认值 | 用途 |
| --- | --- | --- |
| `yt_dlp_path` | `None`（自动查找） | 使用 `yt-dlp` 下载视频和读取元数据 |
| `ffmpeg_path` | `None`（自动查找） | 使用 `ffmpeg` 合并媒体流、转换媒体并抽取音频 |
| `whisper_path` | `None`（自动查找） | 使用本地 `whisper` 命令进行语音识别 |
| `pdftotext_path` | `None`（自动查找） | 使用 Poppler 的 `pdftotext` 提取 PDF 文本 |
| `calibre_ebook_convert` | `None`（自动查找） | 使用 Calibre 的 `ebook-convert` 转换电子书 |

视频完整处理链路是：`yt-dlp` 下载/读取元数据 → `ffmpeg` 合并或转换并抽取音频 → 本地 `whisper` 或配置 `SILICONFLOW_API_KEY` 调用云端语音识别。`ffmpeg` 不是可忽略的装饰依赖；完整的视频转写流程必须安装它。

## 环境变量

请在当前 Shell 中导出变量；除非你使用自己的环境加载工具，否则 `.env.example` 仅用于说明。

| 变量 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `SILICONFLOW_API_KEY` | 否 | 空 | SiliconFlow 云端语音识别密钥。 |
| `EXAMLEX_PYTHON` | 否 | `python` | 本地 ExamLex 封装脚本使用的 Python 解释器。 |

`sessions_root` 默认使用平台对应的 `ExamLex/sessions` 应用数据目录，也可以通过 `TutorConfig(sessions_root=...)` 显式覆盖。

## 依赖检查

运行 `bin/examlex check-deps`，或在 Python 中调用 `TutorConfig.check_all_dependencies()`，可检查 `yt-dlp`、`ffmpeg`、`whisper`、`pdftotext` 和 `ebook-convert`，并获得当前平台的安装提示。

## 密钥处理

切勿提交 `.env` 文件、私密提示词文件、可识别学习者的记录、令牌、密码或本地数据库凭据。

仓库验证脚本会强制 `pyproject.toml` 中的公开安全提示词模式，但贡献者仍需在发布前自行审查示例、截图、发布说明和议题。
