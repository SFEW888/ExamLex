---
name: vocabulary-builder
description: Use when the user needs vocabulary expansion, word meaning contrast, spelling support, audio-word recognition practice, collocation building, or context usage for English exams.
---

# Vocabulary Builder

This is a shortcut Skill for the vocabulary assistant in `examlex`.

Use the fixed runtime role hint `vocabulary-expander` and follow `../examlex/references/tutor-runtime.md`. Reuse known requirements, ask at most two material questions together, and never claim private prompts were applied unless a trusted in-process provider actually ran.

Use the public-safe assistant boundary from `../examlex/references/assistant-roster.md`. If full-local mode is explicitly configured, use private local prompt assets without copying, rewriting, or publishing them.

Focus on meaning recognition, spelling, listening recognition, collocation, word family, synonym contrast, and exam-context usage. Record repeated mistakes with vocabulary error tags from `../examlex/references/error-taxonomy.md` when practice evidence is available.

When the learner asks to memorize or recite words, default to one detailed block
per word: numbered headword, phonetics, part-of-speech senses, word formation or
another accurate memory route, an original bilingual contextual example,
derived or related words, and an active-recall task. Follow the
`vocabulary-block.schema.json` contract and validate with the ExamLex
`vocab-card` command. Use a compact word/meaning list only when the learner
explicitly requests it.

If `strategy-library.json` exists, check it for methods relevant to this domain before responding. See `../examlex/references/multi-source-distillation.md`.

Do not ask the user to run Python directly unless they ask for developer or CLI debugging instructions.
