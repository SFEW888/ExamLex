# Codex App 集成

为 Codex 安装 Skill：

```powershell
python scripts\install_codex.py --dry-run --json
python scripts\install_codex.py --force
```

`agents\openai.yaml` 中的可选适配配置记录了一个最小 public-safe Agent 入口。它不包含密钥，只应作为本地 Codex App 路由示例。

Codex App 中也使用同样的证据闭环：

```powershell
python scripts\validate_repo.py --root . --json
python -m examlex validate-profile --profile learner-profile.json
python -m examlex daily-plan --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json
```

不要把私有提示词正文复制进适配配置或共享对话记录。
