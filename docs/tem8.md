# TEM-8 (英语专业八级) Exam Profile

## Overview

TEM-8 (Test for English Majors — Band 8) is the highest-level national English proficiency exam for fourth-year English majors in China.

## Exam Structure

| Module | Time (min) | Weight | Description |
|--------|-----------|--------|-------------|
| Listening | 25 | 20% | Mini-lecture + interview |
| Reading | 30 | 20% | Reading comprehension |
| Language Knowledge | 15 | 15% | Language usage (if present) |
| Translation | 25 | 20% | English-Chinese + Chinese-English |
| Writing | 45 | 20% | Essay writing (~300 words) |
| Proofreading | 15 | 5% | Error correction in a passage |

## Target Bands

| Band | Score Range | Description |
|------|------------|-------------|
| 60~69 | 60-69 | Pass |
| 70~79 | 70-79 | Good |
| 80+ | 80-100 | Excellent |

## Ability Tree Modules

In addition to CET modules, TEM-8 includes:

- **proofreading**: Article errors, collocation errors, logic errors

## Error Tags

| Error Tag | Module | Node |
|-----------|--------|------|
| `PROOFREAD_ARTICLE_MISS` | proofreading | 冠词错误 |
| `PROOFREAD_COLLOCATION_FAIL` | proofreading | 搭配错误 |
| `PROOFREAD_LOGIC_INCOHERENT` | proofreading | 逻辑错误 |

## Usage Examples

```powershell
# Validate a TEM-8 learner profile
examlex check tem8-learner-profile.json

# Generate a TEM-8 daily plan with timed-practice evidence
examlex plan tem8-learner-profile.json `
  --ability tem8-ability-profile.json `
  --vocab-pool skills/examlex/assets/data/vocabulary/tem8-core-100.json `
  --output daily-plan.json

# Record timed TEM-8 proofreading practice
examlex log practice-ledger.json `
  --date 2026-07-06 --exam-type TEM8 --module proofreading `
  --task-id proofread-001 --duration 15 --total 10 --correct 7 `
  --timed --time-limit 15 `
  --error-tags PROOFREAD_COLLOCATION_FAIL
```
