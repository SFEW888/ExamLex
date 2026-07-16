# GitHub 项目质量

公开仓库 [SFEW888/ExamLex](https://github.com/SFEW888/ExamLex) 按开源项目质量标准维护，
而不只是一个本地 Skill 目录。

## 质量基线

- 首屏清晰：`README.md` 说明用途、支持的考试、快速开始、安装、提示词模式、结构、文档和验证方式。
- 社区健康文件：根目录包含 `CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`SUPPORT.md`、`LICENSE` 和 `CHANGELOG.md`。
- 贡献流程：包含 `.github/ISSUE_TEMPLATE/`、`.github/PULL_REQUEST_TEMPLATE.md` 和 `.github/workflows/ci.yml`。
- 确定性检查：`scripts/validate_repo.py`、detect-secrets、Bandit、pip-audit、针对规范实现统计的 65% 分支覆盖率下限、Ruff、单元测试、轻量兼容包校验、隔离 wheel 冒烟测试及 `git diff --check`。
- 高效 CI：所有受支持的 Python 与操作系统组合均运行测试；仓库校验、分发包构建和隔离 wheel 冒烟测试只执行一次。
- Skill 可移植性：`skills/examlex/` 仅保留所需的 Skill 文件和规范资源。
- 提示词安全：公开文件使用占位符，不包含私有提示词正文。

## 发布就绪检查表

发布或创建标签前，在仓库根目录运行：

```powershell
$repoRoot = (Resolve-Path .).Path
$releasePaths = @('build', 'dist', 'examlex.egg-info') | ForEach-Object { Join-Path $repoRoot $_ }
if ($releasePaths | Where-Object { -not $_.StartsWith($repoRoot + '\') }) { throw 'Unsafe release cleanup target.' }
Remove-Item -LiteralPath $releasePaths -Recurse -Force -ErrorAction SilentlyContinue

python scripts\validate_repo.py --root . --json
python skills\examlex\scripts\sync_mirror.py --check
python -m pip install ".[quality,security]"
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

同时确认：

- Issue 模板仍与当前支持分类一致；
- README 中的 Windows PowerShell 命令可运行；
- 平台适配说明覆盖 Claude Code、Codex CLI、Codex App 和 Cursor；
- 没有跟踪生成的测试产物或本地提示词文件；
- `pyproject.toml` 仍使用 `public-safe` 模式。
