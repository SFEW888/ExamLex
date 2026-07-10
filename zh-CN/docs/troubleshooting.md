# 故障排除

## Python 无法导入 CLI

请从仓库根目录运行命令：

```powershell
cd examlex
python -m examlex --help
```

如果使用简短命令，请先以可编辑模式重新安装：

```powershell
python -m pip install -e .
```

## 在沙盒临时目录中测试失败

某些受限的 Windows 沙盒会阻止写入默认用户临时目录。请在普通 Shell 中重新运行相同的测试命令，或在运行测试前设置一个可写入的临时目录。

## 验证报告提示脚本镜像不匹配

将预期变更同步到以下两个目录之间：

- `skills/examlex/scripts/`
- `examlex/scripts/`

然后重新运行：

```powershell
python scripts\validate_repo.py --root . --json
```

## 提示词安全检查失败

请从公开文件中移除私密提示词正文。公开示例应使用占位符，例如 `[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]`。
