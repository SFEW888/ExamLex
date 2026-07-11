# TEM-4 (英语专业四级) Exam Profile

## Overview

TEM-4 (Test for English Majors — Band 4) is a national English proficiency exam for second-year English majors in China.

## Exam Structure

| Module | Time (min) | Weight | Description |
|--------|-----------|--------|-------------|
| Dictation | 15 | 15% | Full dictation passage (~80-100 words) |
| Listening | 20 | 15% | Conversations and passages |
| Language Knowledge | 10 | 20% | Grammar and vocabulary multiple choice |
| Cloze | 10 | 10% | Cloze test with 20 blanks |
| Reading | 25 | 20% | Reading comprehension |
| Writing | 35 | 20% | Essay writing (~200 words) |

## Target Bands

| Band | Score Range | Description |
|------|------------|-------------|
| 60~69 | 60-69 | Pass |
| 70~79 | 70-79 | Good |
| 80+ | 80-100 | Excellent |

## Ability Tree Modules

In addition to CET modules, TEM-4 includes:

- **language-knowledge**: Grammar selection, vocabulary discrimination
- **dictation**: Dictation accuracy, spelling speed

## Error Tags

| Error Tag | Module | Node |
|-----------|--------|------|
| `LANG_GRAMMAR_SELECT_FAIL` | language-knowledge | 语法选择 |
| `LANG_VOCAB_DISCRIMINATE_FAIL` | language-knowledge | 词汇辨析 |
| `DICTATION_ACCURACY_LOW` | dictation | 听写准确率 |
| `DICTATION_SPELLING_SPEED_LOW` | dictation | 拼写速度 |

## Usage Examples

```powershell
# Validate a TEM-4 learner profile
examlex check tem4-learner-profile.json

# Generate a TEM-4 daily plan
examlex plan tem4-learner-profile.json `
  --ability tem4-ability-profile.json `
  --vocab-pool skills/examlex/assets/data/vocabulary/tem4-core-2000.json `
  --output daily-plan.json
```
