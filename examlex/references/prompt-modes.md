# Prompt Modes

The Skill supports two operating modes. Choose explicitly before producing tutor prompts, packaging the Skill, or sharing files.

## Public-Safe Mode

Use public-safe mode for GitHub, examples, demos, documentation, and any artifact that may leave the local private environment.

Allowed:

- Assistant names, role boundaries, and high-level behavior descriptions.
- Placeholders such as `[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]`.
- Script interfaces, data models, templates, schemas, and taxonomy tags.
- Learner-facing generated advice that does not disclose private prompt text.

Not allowed:

- Full private/original assistant prompts.
- Verbatim hidden prompt clauses from a private prompt library.
- Claims that public placeholders are the complete production prompts.

## Full-Local Mode

Use full-local mode only when the user explicitly works with private local prompt assets outside this public-safe release.

Allowed:

- Selecting a private prompt by local identifier.
- Routing learner tasks to the correct assistant role.
- Combining local prompt outputs with script-generated evidence.

Required limits:

- Do not rewrite the original eight tutor prompts.
- Do not copy full private prompt text into the portable Skill folder.
- Do not publish files generated from private prompts unless they have been scrubbed back to public-safe descriptions or placeholders.

When mode is unclear, stay public-safe and ask for confirmation before reading or using private local prompt assets.
