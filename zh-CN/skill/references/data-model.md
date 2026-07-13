# 数据模型

所有持久化学习者状态都使用 JSON 兼容数据。YAML 和 Markdown 模板只是便于编辑，字段名必须和脚本兼容。

## 学习者档案

模板：`assets/templates/learner-profile.json` 或 `assets/templates/learner-profile.yaml`

必填字段：

- `learner_id`：稳定的学习者标识。
- `exam_type`：`CET4`、`CET6`、`POSTGRADUATE_ENGLISH`、`TEM4` 或 `TEM8`。
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

## 策略库

由 `scripts/ingest_strategy.py` 或 `examlex commit` 生成，默认文件为 `strategy-library.json`。

每条策略的必填字段：

- `strategy_id`：唯一标识（`{exam}-{module}-{digest}-{seq}`）
- `title`：策略名称
- `source_file`：来源文件名
- `source_type`：`text`、`book`、`video`、`podcast`、`person`、`course`、`conversation` 之一
- `distillation_method`：`direct`、`book`、`video`、`person`、`manual` 之一
- `added_at`：ISO 8601 日期
- `exam_types`：适用考试类型标识列表
- `modules`：关联能力模块列表
- `content`：核心方法说明（20–5000 字符）

可选和审计字段：

- `source_provenance`：来源文件名、可选 URL、原始来源 SHA-256 和 UTC 采集时间
- `revisions`：不可变的内容寻址快照（`version`、`sha256`、`strategy`）；练习记录引用修订哈希
- `approval_evidence`：规范化策略内容的 `strategy_sha256`、校验报告与评估报告的 SHA-256，以及 UTC 批准时间；当前蒸馏内容与证据摘要不一致时提交会被拒绝
- `lifecycle_status`：`draft`、`approved` 或 `deprecated`；仅 `approved` 策略可进入每日计划
- `source_url`：视频链接、书籍 ISBN 或人物主页等原始来源
- `ability_nodes`：策略针对的具体能力节点
- `steps`：从内容中提取的有序执行步骤
- `tags`：用于分类和搜索的标签
- `ria_structure`：RIA++ 六段结果 `r_reading`、`i_interpretation`、`a1_past`、`a2_trigger`、`e_execution`、`b_boundary`
- `mental_model`：认知提取结果，包括名称、摘要、证据、应用与限制
- `heuristic`：启发式结果，包括名称、规则、场景与示例

策略库是全局数据：一个文件可服务多个学习者档案。通过 `generate_daily_plan.py --strategies` 把获批策略关联到计划任务。完整摄入流程见 [多源蒸馏方法论](multi-source-distillation.md)。
