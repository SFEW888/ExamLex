# 发布说明

本仓库当前处于 1.0 之前。在公开 CLI 与 Skill 契约稳定后采用语义化版本。

正式仓库：[SFEW888/ExamLex](https://github.com/SFEW888/ExamLex)。

## 版本规则

版本号使用 `X.Y.Z`：

- `X`：不兼容的公开契约变化；
- `Y`：向后兼容的新功能；
- `Z`：向后兼容的问题修复。

## 发布检查表

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
git diff --check
```

创建标签前：

- 更新 `CHANGELOG.md`；
- 验证 README 快速开始命令；
- 验证平台适配说明；
- 确认 `.env`、学习者记录和私有提示词未被跟踪；
- 确认 `pyproject.toml` 仍为 `public-safe` 模式。

## 发布说明内容

发布说明应包含：

- 新增功能；
- 已修复问题；
- 行为变化；
- 破坏性变化；
- 升级说明；
- 已知限制；
- 贡献者。
