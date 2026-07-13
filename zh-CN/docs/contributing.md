# 贡献规范

贡献应保持项目公开安全、确定性、并且容易在 Windows 上校验。

## 校验

运行：

```powershell
python scripts\validate_repo.py --root . --json
python -m pip install ".[quality,security]"
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
python -m bandit -q -r skills/examlex/scripts scripts -ll
python -m pip_audit .
git diff --check
```

代码变更需要运行相关测试或完整测试：

```powershell
python -m unittest discover -s tests
```

## 提示词安全

不要加入完整私有提示词正文。公开文档只能包含角色描述、占位符、策略、工作流、模板、Schema 和脚本行为。

完成提示词相关工作前，应搜索已知私有提示词文本。任何私有提示词正文都不应留在被 Git 跟踪的项目文件中。

## 错误标签变更

新增或修改标签时：

- 更新 `skills/examlex/references/error-taxonomy.md`；
- 同步更新可移植脚本和可导入脚本镜像中的映射；
- 添加或调整聚焦测试；
- 练习计数字段继续使用 `total_items` 和 `correct_items`。

## 安装脚本安全

安装器应默认显示清晰目标路径，支持 `--dry-run`，并避免处理密钥。破坏性覆盖必须要求显式参数，例如 `--force`。

除非项目明确采用外部依赖，否则不要新增依赖。当前工具包只使用 Python 标准库。
