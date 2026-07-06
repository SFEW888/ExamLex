# 配置

> **注意：** 本文档描述的是早期设计中的环境变量；
> 当前的 `TutorConfig` 数据类（`scripts/config.py`）使用了一组不同的字段
>（`yt_dlp_path`、`ffmpeg_path`、`siliconflow_api_key`、`asr_backend` 等）。
> 下面列出的环境变量可能未被当前代码使用。
> 请参阅 `scripts/config.py` 获取权威的配置接口。

公共仓库无需密钥即可运行。配置是可选的，主要用于本地实验或下游集成。

## 环境文件

仅当本地封装需要环境变量时，才将 `.env.example` 复制为 `.env`。

| 变量 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `ENGLISH_EXAM_TUTOR_PROMPT_MODE` | 否 | `public-safe` | 公开安全模式，防止私密提示词出现在生成产物中。 |
| `ENGLISH_EXAM_TUTOR_DATA_DIR` | 否 | `./local/data` | 建议的学习记录和生成计划存放位置。 |
| `ENGLISH_EXAM_TUTOR_PRIVATE_PROMPT_DIR` | 否 | 空 | 本地私密提示词目录（仅全本地模式使用）。 |
| `ENGLISH_EXAM_TUTOR_DEFAULT_EXAM` | 否 | `CET4` | 本地封装的默认考试类型。 |
| `ENGLISH_EXAM_TUTOR_DEFAULT_TARGET` | 否 | `550+` | 本地封装的默认目标分段。 |

## 密钥处理

切勿提交 `.env` 文件、私密提示词文件、可识别学习者的记录、令牌、密码或本地数据库凭据。

仓库验证脚本会强制 `pyproject.toml` 中的公开安全提示词模式，但贡献者仍需在发布前自行审查示例、截图、发布说明和议题。
