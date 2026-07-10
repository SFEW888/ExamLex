# 工作流

四级、六级和考研英语助教会话使用这个闭环。

## 1. 诊断

收集或加载学习者档案：

- `learner_id`
- `exam_type`
- `foundation_level`
- `target_band`
- `daily_time_budget_minutes`
- 可选 `exam_date`

用 `validate-profile` 校验。如果校验失败，先修正档案再规划。

## 2. 计划

根据学习者档案、能力画像和可选错误统计生成每日计划：

```bash
python -m examlex daily-plan --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json
```

以生成任务为基线。可以调整面向学习者的文字表达，但模块、重点、分钟数和原因应保持一致，除非用户修改约束。

## 3. 练习

安排词汇、听力、阅读、翻译、写作任务。练习结果必须记录到 ledger，并使用 `total_items` 和 `correct_items`。

当学习者提供错误描述时，可用 `tag-error` 进行确定性初步归因。观察问题明确时，也可以从 `references/error-taxonomy.md` 手动添加标签。

## 4. 错误归因

用 `record-practice` 追加练习记录，再统计重复错误：

```bash
python -m examlex summarize-errors --ledger practice-ledger.json --output error-summary.json
```

错误统计是下一次计划的证据，不是对学习者的最终判断。

## 5. 能力更新

根据练习记录更新能力画像：

```bash
python -m examlex update-ability --ability ability-profile.json --ledger practice-ledger.json
```

当练习记录或能力历史有足够数据点时，分析趋势：

```bash
python -m examlex analyze-trends --ledger practice-ledger.json --history ability-history.json --output trend-analysis.json
```

## 6. 作文闭环

写作任务使用 `writing-version` 创建有版本的草稿。需要确定性评分参考时，使用 `score-writing`。

必须说明评分只是规则估算，不是官方评分。用版本元数据比较修改效果，不要覆盖旧稿。

## 7. 下一次计划

把更新后的能力画像和错误统计重新输入 `daily-plan`。优先处理重复出现的高影响错误和低状态能力节点，同时遵守学习者每日时间预算。
