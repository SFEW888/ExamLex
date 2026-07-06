# Getting Started

Use this guide to install the Skills from a clean clone. For the shortest path, use the same one-line style as other agent-native Skill repositories.

## Requirements

- Python 3.10 or newer
- Git
- Node.js/npm for `npx skills add`, or Git plus PowerShell/POSIX shell for the clone installer
- Python 3.10 or newer for the clone installer internals

No third-party Python dependency is required for the current toolkit.

## One-Line Install

```bash
npx skills add your-org/english-exam-ai-tutor
```

This installs the main `english-exam-ai-tutor` Skill when the repository is published with a real GitHub owner. Restart the agent, run `/skills`, and invoke the Skill from chat.

## Clone Install With Shortcut Skills

Use this path when you want the main Skill plus all eight shortcut Skills.

macOS/Linux:

```bash
git clone https://github.com/your-org/english-exam-ai-tutor.git ~/.english-exam-ai-tutor
cd ~/.english-exam-ai-tutor
./install.sh codex
./install.sh claude
```

Windows PowerShell:

```powershell
git clone https://github.com/your-org/english-exam-ai-tutor.git
cd english-exam-ai-tutor
.\install.ps1 codex
.\install.ps1 claude
```

Use project-local installs when you only want the Skills in the current project:

```powershell
.\install.ps1 codex -Project
.\install.ps1 claude -Project
```

Preview targets first:

```bash
./install.sh codex --dry-run
./install.sh claude --dry-run
```

Verify in the Agent:

```text
/skills
/english-exam-ai-tutor 帮我为 CET4 550+ 制定一周计划
/learning-planner 帮我生成本周任务
/grammar-corrector 批改这段作文
```

## Shortcut Skill Names

Use these in Agent chat instead of long Python commands:

| Scenario | Slash call |
| --- | --- |
| Full tutor workflow | `/english-exam-ai-tutor` |
| Learning plan | `/learning-planner` |
| Vocabulary | `/vocabulary-builder` |
| Reading | `/reading-navigator` |
| Writing structure | `/structure-planner` |
| Grammar correction | `/grammar-corrector` |
| Polishing | `/polish-wizard` |
| Scenario dialogue | `/scenario-dialog` |
| Cultural context | `/culture-guide` |

## Run The Optional CLI

Use these wrappers when you want to run the deterministic tools directly from a terminal:

```bash
bin/tutor check examples/sample-learner-profile.yaml
bin/tutor plan examples/sample-learner-profile.yaml --ability examples/sample-ability-profile.yaml --output daily-plan.json
bin/tutor strategies --library strategy-library.json
```

PowerShell:

```powershell
.\bin\tutor.ps1 check examples/sample-learner-profile.yaml
.\bin\tutor.ps1 plan examples/sample-learner-profile.yaml --ability examples/sample-ability-profile.yaml --output daily-plan.json
```

The underlying Python module is for maintainers and debugging:

```powershell
python -m skills.english_exam_ai_tutor --help
```

See [../cli-reference.md](../cli-reference.md) for all short commands.

## Validate The Repository

Maintainers can still run the deterministic checks directly:

```powershell
python scripts\validate_repo.py --root . --json
python -m unittest discover -s tests
```

## Optional Editable Install

```powershell
python -m pip install -e .
english-exam-tutor --help
```

Generated local files such as `daily-plan.json`, `.env`, and learner records should stay untracked.
