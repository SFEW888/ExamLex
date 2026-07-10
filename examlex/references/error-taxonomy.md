# Error Taxonomy

Use these tags for deterministic error attribution. Practice records store tags in `error_tags`, and scripts map tags to ability modules and dimensions.

## Module Tree

| Module | Dimensions |
| --- | --- |
| `vocabulary` | meaning recognition, spelling, audio recognition, context use |
| `listening` | keyword capture, linking/weak forms, numbers/dates/times, main idea inference |
| `reading` | reading speed, locating information, long sentences, inference, paraphrase recognition |
| `translation` | grammar accuracy, word choice, Chinese-English transfer, sentence variety |
| `writing` | task completion, structure/logic, language accuracy, expression richness |

## Tags

| Tag | Module | Dimension |
| --- | --- | --- |
| `VOCAB_MEANING_RECOGNITION_FAIL` | vocabulary | meaning recognition |
| `VOCAB_SPELLING_FAIL` | vocabulary | spelling |
| `VOCAB_AUDIO_RECOGNITION_FAIL` | vocabulary | audio recognition |
| `VOCAB_CONTEXT_MISUSE` | vocabulary | context use |
| `LISTENING_KEYWORD_MISS` | listening | keyword capture |
| `LISTENING_LINKING_WEAK_FORM_FAIL` | listening | linking/weak forms |
| `LISTENING_NUMBER_DATE_FAIL` | listening | numbers/dates/times |
| `LISTENING_MAIN_IDEA_FAIL` | listening | main idea inference |
| `READING_SPEED_LOW` | reading | reading speed |
| `READING_LOCATION_FAIL` | reading | locating information |
| `READING_LONG_SENTENCE_FAIL` | reading | long sentences |
| `READING_INFERENCE_FAIL` | reading | inference |
| `READING_PARAPHRASE_FAIL` | reading | locating information / paraphrase recognition |
| `TRANSLATION_GRAMMAR_FAIL` | translation | grammar accuracy |
| `TRANSLATION_WORD_CHOICE_FAIL` | translation | word choice |
| `TRANSLATION_CHINESE_ENGLISH` | translation | Chinese-English transfer |
| `TRANSLATION_SENTENCE_VARIETY_LOW` | translation | sentence variety |
| `WRITING_TASK_RESPONSE_WEAK` | writing | task completion |
| `WRITING_STRUCTURE_LOGIC_WEAK` | writing | structure/logic |
| `WRITING_LANGUAGE_ACCURACY_FAIL` | writing | language accuracy |
| `WRITING_EXPRESSION_LIMITED` | writing | expression richness |
| `WRITING_ARTICLE_OMISSION` | writing | language accuracy |

## Attribution Rules

- Prefer the most specific observed cause over a broad module label.
- Use `WRITING_ARTICLE_OMISSION` for missing or incorrect articles in writing; it maps to `writing` / `language accuracy`.
- If a task has multiple independent issues, attach multiple tags.
- Do not add ad hoc tags to practice records unless `scripts/common.py` and related tests/scripts have been updated to validate them.
