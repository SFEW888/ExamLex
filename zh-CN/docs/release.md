# 发布说明

本仓库当前处于 1.0 之前阶段；当公开 CLI 与 Skill 契约稳定后，采用语义化版本。

正式仓库：[SFEW888/ExamLex](https://github.com/SFEW888/ExamLex)。

## 版本规则

使用 `X.Y.Z`：

- `X`：不兼容的公开契约变更；
- `Y`：向后兼容的新功能；
- `Z`：向后兼容的问题修复。

## 发布检查表

在仓库根目录运行：

```powershell
$repoRoot = (Resolve-Path .).Path
$releasePaths = @('build', 'dist', 'examlex.egg-info') | ForEach-Object { Join-Path $repoRoot $_ }
if ($releasePaths | Where-Object { -not $_.StartsWith($repoRoot + '\') }) { throw 'Unsafe release cleanup target.' }
Remove-Item -LiteralPath $releasePaths -Recurse -Force -ErrorAction SilentlyContinue

python -m pip install ".[quality,security,release]"
python scripts\validate_repo.py --root . --json
python skills\examlex\scripts\sync_mirror.py --check
python -m ruff check .
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
python -m bandit -q -r skills/examlex/scripts scripts -ll
python -m pip_audit .
python -m coverage run -m unittest discover -s tests -q
python -m coverage report
python -m build
python scripts\smoke_test_wheel.py dist
git diff --check
```

清理命令只应在仓库根目录运行；它会先确认 `build`、`dist` 与
`examlex.egg-info` 都位于当前仓库内，再删除旧的构建产物。隔离 wheel
冒烟测试可以在打标签前发现陈旧构建缓存、缺失的规范资源、重复打包资源和
遗漏的公开 CLI 命令。

创建标签前还应确认：

- 已更新 `CHANGELOG.md`；
- README 的快速开始命令可运行；
- 平台适配说明仍然准确；
- `.env`、学习记录和私有提示词未被跟踪；
- `pyproject.toml` 仍处于 `public-safe` 模式。

## GitHub 发布说明应包含

- 新增功能；
- 已修复问题；
- 行为变化；
- 破坏性变更；
- 升级说明；
- 已知限制；
- 贡献者。
