# 助教运行时

学习者通过主 Skill 或八个快捷 Skill 请求辅导时，使用以下流程。

## 快速收集需求

1. 根据第一条消息路由到一至三个角色。快捷 Skill 提供固定角色提示，主 Skill 使用中英文自动路由。
2. 复用请求或结构化会话上下文中已有的限制条件。
3. 只询问会实质影响答案的缺失信息，并在同一轮一次问完，最多两个问题。
4. 记录对应的 `asked_fields`，不得重复询问；学习者不回答时，明确说明合理假设并继续。
5. 已提供学习材料或具体任务时，立即给出有用结果，不重复进行需求收集。

`python run.py tutor-prepare --request "..." --json` 只执行公开安全的路由与澄清判断，不加载私有提示词，也不调用模型。

## 私有提供器边界

Python 宿主可以把实现了 `TutorProvider.generate()` 的受信提供器传给 `scripts.tutor_runtime` 中的 `run_tutor_turn()`。运行时随后会：

- 仍需澄清时在加载提示词前停止；
- 使用前校验全部八个外部提示词文件；
- 只在内存中组合最多三个选定角色；
- 仅把原始学习者请求作为提供器的 user message；
- 把结构化上下文放在明确的不可信数据边界内；
- 将提供器异常转换为固定安全错误，并阻断疑似提示词泄漏的输出。

不得通过 stdout、Shell 参数、临时文件、学习者可见消息或普通应用日志传递组合提示词。宿主没有受信提供器边界时，必须保持 public-safe，且不能声称已应用私有提示词。

本地提供器默认允许。远程提供器会接触私有提示词，调用方必须先获得明确授权，再设置 `allow_remote_provider=True`。ExamLex 无法保证第三方提供器的留存或日志策略。

宿主适配器应把模型调用保留在同一个受信进程内：

```python
from examlex.scripts.tutor_runtime import run_tutor_turn

class LocalTutorProvider:
    privacy_boundary = "local"

    def __init__(self, local_model):
        self.local_model = local_model

    def generate(self, *, system_prompt, user_message, metadata):
        return self.local_model.generate(system=system_prompt, user=user_message)

result = run_tutor_turn(
    LocalTutorProvider(local_model),
    learner_request,
    role_id="grammar-corrector",
    context={"register": "academic"},
    asked_fields=previously_asked_fields,
)
return result.answer
```

不得为 `system_prompt` 或提供器请求负载添加调试日志。

## 本地配置

在仓库外保存严格命名的八个 `<role-id>.md` 文件，然后进行校验并保存目录配置；命令输出不会显示目录或正文：

```powershell
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --save
```

目录解析优先级为显式库参数、`EXAMLEX_PRIVATE_PROMPT_DIR`、本机 `~/.examlex/prompt-config.json`。保存的配置只包含外部目录路径，绝不能提交。

## 快捷 Skill 固定映射

| 快捷 Skill | 运行时角色 |
|---|---|
| `learning-planner` | `study-planner` |
| `vocabulary-builder` | `vocabulary-expander` |
| `reading-navigator` | `reading-navigator` |
| `structure-planner` | `structure-planner` |
| `grammar-corrector` | `grammar-corrector` |
| `polish-wizard` | `polishing-editor` |
| `scenario-dialog` | `situational-dialogue` |
| `culture-guide` | `culture-guide` |
