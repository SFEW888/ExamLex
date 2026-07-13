# Tutor Runtime

Use this workflow when a learner asks for tutoring through the main Skill or one of the eight shortcut Skills.

## Fast intake

1. Route the first message to one to three roles. A shortcut Skill supplies its fixed role hint; the main Skill uses automatic Chinese/English routing.
2. Reuse constraints already present in the request or structured session context.
3. Ask only for missing information that would materially change the answer. Ask at most two questions together in one turn.
4. Record the corresponding `asked_fields`. Do not ask those fields again; if the learner declines, state reasonable assumptions and continue.
5. When learner text or a concrete task is already present, provide useful work immediately instead of repeating intake questions.

`python run.py tutor-prepare --request "..." --json` performs the public-safe routing and clarification decision. It does not load a private prompt or call a model.

## Private provider boundary

The Python host may call `run_tutor_turn()` from `scripts.tutor_runtime` with a trusted provider implementing `TutorProvider.generate()`. The runtime then:

- stops before loading prompts when clarification is still required;
- validates all eight external prompt files before use;
- composes at most three selected roles in memory;
- sends the original learner request only as the provider's user message;
- places structured context inside an explicit untrusted-data boundary;
- converts provider failures to fixed safe errors and rejects prompt-like output.

Never pass a composed prompt through stdout, a shell argument, a temporary file, a learner-visible message, or ordinary application logs. If the host has no trusted provider boundary, remain in public-safe mode and do not claim that private prompts were applied.

Local providers are accepted by default. A remote provider receives the private prompt and therefore requires the caller to set `allow_remote_provider=True` after obtaining explicit authorization. ExamLex cannot guarantee a third-party provider's retention or logging behavior.

A host adapter keeps the model call inside the same trusted process:

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

Do not add debug logging around `system_prompt` or provider request payloads.

## Local configuration

Keep exactly eight `<role-id>.md` files outside the repository, then validate and save the directory without exposing its path or contents in command output:

```powershell
python run.py prompt-check --private-dir "D:\path\to\ExamLex-Private-Prompts" --save
```

Resolution order is an explicit library argument, `EXAMLEX_PRIVATE_PROMPT_DIR`, then the local `~/.examlex/prompt-config.json` setting. The saved file contains only the external directory path; never commit it.

## Fixed shortcut mapping

| Shortcut Skill | Runtime role |
|---|---|
| `learning-planner` | `study-planner` |
| `vocabulary-builder` | `vocabulary-expander` |
| `reading-navigator` | `reading-navigator` |
| `structure-planner` | `structure-planner` |
| `grammar-corrector` | `grammar-corrector` |
| `polish-wizard` | `polishing-editor` |
| `scenario-dialog` | `situational-dialogue` |
| `culture-guide` | `culture-guide` |
