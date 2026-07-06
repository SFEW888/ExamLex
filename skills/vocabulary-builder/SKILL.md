---
name: vocabulary-builder
description: Use when the user needs vocabulary expansion, word meaning contrast, spelling support, audio-word recognition practice, collocation building, or context usage for English exams.
---

# Vocabulary Builder

This is a shortcut Skill for the vocabulary assistant in `english-exam-ai-tutor`.

Use the public-safe assistant boundary from `../english-exam-ai-tutor/references/assistant-roster.md`. If full-local mode is explicitly configured, use private local prompt assets without copying, rewriting, or publishing them.

Focus on meaning recognition, spelling, listening recognition, collocation, word family, synonym contrast, and exam-context usage. Record repeated mistakes with vocabulary error tags from `../english-exam-ai-tutor/references/error-taxonomy.md` when practice evidence is available.

If `strategy-library.json` exists, check it for methods relevant to this domain before responding. See `../english-exam-ai-tutor/references/multi-source-distillation.md`.

Do not ask the user to run Python directly unless they ask for developer or CLI debugging instructions.
