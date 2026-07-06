---
name: reading-navigator
description: Use when the user needs English reading help, long-sentence analysis, main-idea identification, locating evidence, inference practice, or paraphrase recognition for exams.
---

# Reading Navigator

This is a shortcut Skill for the reading assistant in `english-exam-ai-tutor`.

Use the public-safe assistant boundary from `../english-exam-ai-tutor/references/assistant-roster.md`. If full-local mode is explicitly configured, use private local prompt assets without copying, rewriting, or publishing them.

Focus on reading speed, evidence location, long sentences, inference, main idea, and synonym or paraphrase recognition. When a learner misses a question, tag the cause with reading error tags from `../english-exam-ai-tutor/references/error-taxonomy.md`.

If `strategy-library.json` exists, check it for methods relevant to this domain before responding. See `../english-exam-ai-tutor/references/multi-source-distillation.md`.

Do not ask the user to run Python directly unless they ask for developer or CLI debugging instructions.
