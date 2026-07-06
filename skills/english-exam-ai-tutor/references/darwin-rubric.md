# Darwin 9-Dimension Scoring Rubric

> Adapted from darwin-skill v2.0 — evaluates strategy quality on structure + effectiveness + meta-skill dimensions.

## Overview

Every strategy in the library is scored on 9 dimensions (100 points total):

| Category | Dimensions | Max Points |
|----------|-----------|------------|
| Structure (static, Python-scored) | dim1–dim6 | 59 |
| Effectiveness (requires Agent testing) | dim7–dim8 | 35 |
| Meta-skill (anti-patterns) | dim9 | 6 |

## Structure Dimensions (59 points) — Scored by `validators/darwin_structure.py`

| # | Dimension | Weight | What it checks |
|---|-----------|--------|----------------|
| 1 | Frontmatter quality | 7 | Exam types, modules, title completeness. No vague placeholders. |
| 2 | Workflow clarity | 12 | Steps are numbered, ordered, with clear sequence. RIA++ has execution steps. |
| 3 | Failure mode encoding | 12 | If-then fallback patterns. Explicit boundary/limitation section. |
| 4 | Checkpoint design | 6 | STOP/CHECKPOINT markers present. |
| 5 | Actionable specificity | 17 | Concrete numbers, examples. No vague "建议/可以考虑" phrases. |
| 6 | Resource integration | 4 | Source file/URL references. Tags for categorization. |

Each dimension scored 1–10, multiplied by weight, divided by 10.

## Effectiveness Dimensions (35 points) — Scored by Agent via `prompts/effect.py`

| # | Dimension | Weight | What it checks |
|---|-----------|--------|----------------|
| 7 | Overall architecture | 12 | Structure hierarchy, no redundancy, no AI-slop filler. |
| 8 | Performance | 23 | Test prompt execution: does strategy output meaningfully improve over baseline? |

## Meta-Skill Dimension (6 points) — Checked during optimization

| # | Dimension | Weight | What it checks |
|---|-----------|--------|----------------|
| 9 | Anti-patterns & blacklist | 6 | Strategy includes "what NOT to do". High-risk red-flag actions listed. |

## Pass Threshold

- **≥ 70/100**: Strategy passes and enters the library.
- **< 70/100**: Strategy enters optimization loop (hill-climbing, max 3 rounds).
- **Touch-top signal**: 2 consecutive rounds with Δ < 2 points → stop optimizing.

## Score History

Each strategy records its optimization history in `score_history`:

```json
{
  "version": 2,
  "score": 85.0,
  "dimensions": {"dim5_specificity": 12.0, ...},
  "changed_at": "2026-07-06",
  "delta": 5.0,
  "status": "improved"
}
```

## References

- [darwin-skill on GitHub](https://github.com/alchaincyf/darwin-skill)
- SkillLens paper: arXiv 2605.23899
- SkillOpt paper: arXiv 2605.23904
