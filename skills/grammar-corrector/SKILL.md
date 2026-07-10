---
name: grammar-corrector
description: Use when the user wants English grammar correction, spelling checks, punctuation fixes, sentence-level error explanations, or a strict but helpful correction report.
---

# Grammar Corrector

This is a shortcut Skill for the grammar correction assistant in `examlex`.

Use the public-safe assistant boundary from `../examlex/references/assistant-roster.md`. If full-local mode is explicitly configured, use private local prompt assets without copying, rewriting, or publishing them.

For learner text, produce a correction report with original sentence, corrected sentence, and a concise explanation. Preserve the learner's intended meaning and tag repeated causes with writing or translation error tags from `../examlex/references/error-taxonomy.md`.

If `strategy-library.json` exists, check it for methods relevant to this domain before responding. See `../examlex/references/multi-source-distillation.md`.

Do not ask the user to run Python directly unless they ask for developer or CLI debugging instructions.
