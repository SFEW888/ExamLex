# 错误标签体系

使用这些标签进行确定性错误归因。练习记录把标签存入 `error_tags`，脚本会把标签映射到能力模块和维度。

## 模块树

| 模块 | 维度 |
| --- | --- |
| `vocabulary` | 词义识别、拼写、听音辨词、语境使用 |
| `listening` | 关键词捕捉、连读弱读、数字/日期/时间、主旨推断 |
| `reading` | 阅读速度、定位能力、长难句、推理判断、同义替换识别 |
| `translation` | 语法准确度、词汇选择、中式英语、句式多样性 |
| `writing` | 任务完成度、结构逻辑、语言准确性、表达丰富度 |

## 标签

| 标签 | 模块 | 维度 |
| --- | --- | --- |
| `VOCAB_MEANING_RECOGNITION_FAIL` | vocabulary | 词义识别 |
| `VOCAB_SPELLING_FAIL` | vocabulary | 拼写 |
| `VOCAB_AUDIO_RECOGNITION_FAIL` | vocabulary | 听音辨词 |
| `VOCAB_CONTEXT_MISUSE` | vocabulary | 语境使用 |
| `LISTENING_KEYWORD_MISS` | listening | 关键词捕捉 |
| `LISTENING_LINKING_WEAK_FORM_FAIL` | listening | 连读弱读 |
| `LISTENING_NUMBER_DATE_FAIL` | listening | 数字/日期/时间 |
| `LISTENING_MAIN_IDEA_FAIL` | listening | 主旨推断 |
| `READING_SPEED_LOW` | reading | 阅读速度 |
| `READING_LOCATION_FAIL` | reading | 定位能力 |
| `READING_LONG_SENTENCE_FAIL` | reading | 长难句 |
| `READING_INFERENCE_FAIL` | reading | 推理判断 |
| `READING_PARAPHRASE_FAIL` | reading | 定位能力 / 同义替换识别 |
| `TRANSLATION_GRAMMAR_FAIL` | translation | 语法准确度 |
| `TRANSLATION_WORD_CHOICE_FAIL` | translation | 词汇选择 |
| `TRANSLATION_CHINESE_ENGLISH` | translation | 中式英语 |
| `TRANSLATION_SENTENCE_VARIETY_LOW` | translation | 句式多样性 |
| `WRITING_TASK_RESPONSE_WEAK` | writing | 任务完成度 |
| `WRITING_STRUCTURE_LOGIC_WEAK` | writing | 结构逻辑 |
| `WRITING_LANGUAGE_ACCURACY_FAIL` | writing | 语言准确性 |
| `WRITING_EXPRESSION_LIMITED` | writing | 表达丰富度 |
| `WRITING_ARTICLE_OMISSION` | writing | 语言准确性 |

## 归因规则

- 优先使用最具体的已观察原因，而不是宽泛模块标签。
- 写作中冠词缺失或冠词错误使用 `WRITING_ARTICLE_OMISSION`，它映射到 `writing` / `language accuracy`。
- 如果一个任务有多个独立问题，可以附加多个标签。
- 不要随意给练习记录添加临时标签，除非已经同步更新 `scripts/common.py` 和相关测试/脚本。
