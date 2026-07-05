# Architecture

The repository is a local-first tutoring toolkit. Agents provide tutoring behavior through the Skill, while scripts provide deterministic state transitions.

```mermaid
flowchart TD
    User["Learner or tutor operator"] --> Agent["Agent platform: Claude Code, Codex, Cursor"]
    Agent --> Skill["Portable Skill: skills/english-exam-ai-tutor"]
    Skill --> References["References: roster, workflow, data model, exam profiles, taxonomy, prompt modes"]
    Skill --> Templates["Templates and schemas"]
    Agent --> Scripts["Automation scripts"]
    Scripts --> Profile["Learner profile"]
    Scripts --> Ability["Ability profile"]
    Scripts --> Ledger["Practice ledger"]
    Scripts --> Errors["Error summary"]
    Scripts --> Writing["Writing versions and rubric estimates"]
    Installers["Install scripts"] --> Claude["Claude Code"]
    Installers --> Codex["Codex CLI or App"]
    Installers --> Cursor["Cursor"]
```

## Learning Closed Loop

```mermaid
flowchart LR
    Intake["1. Validate learner profile"] --> Plan["2. Generate constrained daily plan"]
    Plan --> Practice["3. Practice vocabulary, listening, reading, translation, writing"]
    Practice --> Record["4. Record practice and tag errors"]
    Record --> Summary["5. Summarize repeated errors"]
    Summary --> Ability["6. Update ability profile"]
    Ability --> Review["7. Weekly review or trend analysis"]
    Review --> Plan
```

## Main Components

- `skills/english-exam-ai-tutor/SKILL.md`: portable Skill entry point.
- `skills/english-exam-ai-tutor/references/`: public-safe policy, workflow, data model, exam profiles, assistant roster, and error taxonomy.
- `skills/english-exam-ai-tutor/assets/`: templates and JSON schemas.
- `skills/english-exam-ai-tutor/scripts/`: portable script entry points.
- `skills/english_exam_ai_tutor/scripts/`: importable script mirror validated by hash.
- `scripts/`: repository validator and platform installers.
- `integrations/`: platform-specific installation and usage notes.

## Data Flow

Durable learner state is JSON-compatible. YAML templates are authoring conveniences; script inputs and outputs should keep the same field names. Practice accuracy uses `total_items` and `correct_items` to avoid ambiguous calculations.

Prompt state is separate from learner state. Public files use placeholders and role descriptions. Full-local prompt assets, when used, stay outside the public Skill package.
