# Exam Profiles

The Skill supports three exam tracks and a small set of foundation levels and target bands.

## Exam Types

| Value | Use |
| --- | --- |
| `CET4` | College English Test Band 4 preparation. |
| `CET6` | College English Test Band 6 preparation. |
| `POSTGRADUATE_ENGLISH` | Chinese postgraduate entrance English preparation. |

## Foundation Levels

| Level | Operational meaning |
| --- | --- |
| `基础偏弱` | Needs high-frequency vocabulary, grammar repair, slow reading support, and guided output. |
| `中等基础` | Can complete routine tasks but needs accuracy, speed, and exam-strategy improvement. |
| `基础较好` | Needs advanced accuracy, timing, expression quality, and weak-point polishing. |

Use the exact local values expected by `validate_profile.py` when validating existing templates. If a file displays mojibake in a terminal, preserve UTF-8 bytes and inspect it with a UTF-8-aware editor before changing labels.

## Target Bands

| Exam type | Supported target bands |
| --- | --- |
| `CET4` | `425~499`, `500~550`, `550+`, `600+` |
| `CET6` | `425~499`, `500~550`, `550+`, `600+` |
| `POSTGRADUATE_ENGLISH` | `50+`, `70~80`, `80+`, `90+` |

## Planning Guidance

- For `基础偏弱`, favor shorter focused tasks, error repair, and high-frequency review.
- For `中等基础`, balance new practice with targeted correction and timed drills.
- For `基础较好`, prioritize high-value recurring errors, writing/translation quality, and exam timing.
- Target bands should shape intensity and expected output quality, but the generated daily plan must still respect `daily_time_budget_minutes`.
