# 开发说明

本项目优先采用确定性的 Python 标准库脚本，不依赖隐藏的本地配置。

## 源码结构

- `skills/examlex/`：可移植、公开安全的规范 Skill、实现与资源包。
- `examlex/`：历史 CLI 与导入路径的轻量兼容包。
- `scripts/`：仓库安装、同步和校验脚本。
- `tests/`：覆盖脚本、CLI、安装器和项目约束的单元测试。

项目不使用单独的 `src/` 目录，因为 `skills/` 下的规范 Agent Skill 本身就是可导入 Python 包。

## 本地检查

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
python -m pip install ".[quality,security]"
python -m ruff check .
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
python -m bandit -q -r skills/examlex/scripts scripts -ll
python -m pip_audit .
python -m coverage run -m unittest discover -s tests -q
python -m coverage report
git diff --check
```

修改 CLI 后还应运行：

```powershell
python -m examlex --help
```

## 修改规则

- 自动化脚本以 `skills/examlex/scripts/` 为唯一规范来源；修改后运行 `python skills\examlex\scripts\sync_mirror.py` 修复轻量兼容层，再用 `--check` 验证。
- 行为变化必须新增或更新测试。
- 可移植 Skill 目录不得混入仓库根级项目文档。
- 生成文件应放入 `local/`、`test-artifacts/` 或其他已忽略目录。
