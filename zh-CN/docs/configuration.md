# 配置

`examlex/scripts/config.py` 中的 `TutorConfig` 数据类是权威配置接口。公共仓库无需密钥即可运行。

配置优先级为：构造参数或 CLI 参数、`SILICONFLOW_API_KEY`、代码默认值。ExamLex 不会自动加载 `.env` 或用户目录中的 JSON 配置文件。

## 环境变量

请在当前 Shell 中导出变量；除非你使用自己的环境加载工具，否则 `.env.example` 仅用于说明。

| 变量 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `SILICONFLOW_API_KEY` | 否 | 空 | SiliconFlow 云端语音识别密钥。 |
| `EXAMLEX_PYTHON` | 否 | `python` | 本地 ExamLex 封装脚本使用的 Python 解释器。 |

`sessions_root` 默认使用平台对应的 `ExamLex/sessions` 应用数据目录，也可以通过 `TutorConfig(sessions_root=...)` 显式覆盖。

## 密钥处理

切勿提交 `.env` 文件、私密提示词文件、可识别学习者的记录、令牌、密码或本地数据库凭据。

仓库验证脚本会强制 `pyproject.toml` 中的公开安全提示词模式，但贡献者仍需在发布前自行审查示例、截图、发布说明和议题。
