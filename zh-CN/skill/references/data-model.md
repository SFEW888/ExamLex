# 数据模型

所有持久化学习者状态都使用 JSON 兼容数据。YAML 和 Markdown 模板只是便于编辑，字段名必须和脚本兼容。

## 学习者档案

模板：`assets/templates/learner-profile.json` 或 `assets/templates/learner-profile.yaml`

必填字段：

- `learner_id`：稳定的学习者标识。
- `exam_type`：`CET4`、`CET6` 或 `POSTGRADUATE_ENGLISH`。
- `foundation_level`：`exam-profiles.md` 中支持的基础水平。
- `target_band`：对该考试类型有效的目标区间。
- `daily_time_budget_minutes`：正整数。

可选字段：

- `exam_date`：考试目标日期；未知时可以为空字符串。

## 能力画像

模板：`assets/templates/ability-profile.yaml`

期望结构：

```json
{
  "learner_id": "learner-id",
  "exam_type": "CET4",
  "modules": {
    "reading": [
      {
        "node": "long sentences",
        "level": 2,
        "status": "needs_work",
        "stats": {
          "total_items": 20,
          "correct_items": 13,
          "error_count": 2,
          "accuracy": 0.65
        }
      }
    ]
  },
  "priority_errors": []
}
```

`level` 和 `status` 会根据练习正确率和错误数量更新。较低 level 和 `priority` 状态应获得更高计划权重。

## 练习记录

模板：`assets/templates/exercise-record.json` 或 `assets/templates/exercise-record.yaml`

ledger 是一个 JSON 列表。每条记录应包含：

- `date`
- `exam_type`
- `module`
- `task_id`
- `duration_minutes`
- `total_items`
- `correct_items`
- `error_tags`

必须使用 `total_items` 和 `correct_items`。不要使用 `total` 或 `correct`，脚本会拒绝这些名称，避免正确率计算歧义。

## 错误统计

由 `summarize-errors` 生成。

顶层字段：

- `total_records`
- `total_error_tags`
- `by_tag`
- `by_module`
- `by_dimension`

这个文件可作为每日计划和周复盘输入。

## 作文版本

模板：`assets/templates/writing-version-record.yaml`

作文版本文件是一个 JSON 列表，每条记录包含：

- `writing_id`
- `version`：`V1`、`V2`、`V3` 等。
- `source_version`：可选的父版本。
- `text`
- `changes`：修改说明列表。

用 `writing-version` 追加草稿，不要覆盖旧稿。

## 作文评分

由 `score-writing` 生成。

字段包括：

- `label`：`rubric_estimate`
- `exam_type`
- `total_score`
- `max_score`
- `normalized_score`
- `signals`
- `dimensions`

分数是确定性的修改参考，不是官方考试评分。
