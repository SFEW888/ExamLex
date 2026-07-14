# 工作流

四级、六级、专四、专八和考研英语助教会话使用这个闭环。

## 0. 知识摄入（可选，多来源）

在诊断前或任意后续阶段，均可把新方法加入策略库：

1. `python run.py extract --input <url|file|name> --type <video|book|text|person>` 提取原始素材。
2. Agent 按来源选择 RIA++、认知提取或直接摄入方法，写入会话产物。
3. `python run.py validate --artifacts-dir <path>` 执行格式和 Darwin 结构校验。
4. 为每条策略生成效果评估证据。
5. `python run.py commit --artifacts-dir <path> --library strategy-library.json` 原子提交获批策略。

仅 `approved` 策略可进入每日计划；摄入失败或没有策略库时，普通学习闭环仍可继续。

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
python run.py daily-plan --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --strategies strategy-library.json --output daily-plan.json
```

以生成任务为基线。可以调整面向学习者的文字表达，但模块、重点、分钟数和原因应保持一致，除非用户修改约束。

## 3. 练习

按目标考试安排词汇、听力、阅读、翻译、写作、完形、语言知识、改错和听写任务。
练习结果必须记录到 ledger，并使用 `total_items` 和 `correct_items`。

当学习者提供错误描述时，可用 `tag-error` 进行确定性初步归因。观察问题明确时，也可以从 `references/error-taxonomy.md` 手动添加标签。

## 4. 解析与复盘

所有模拟卷、答案复盘和错题讲解都必须执行
[全面答案解析标准](answer-explanation-standard.md)。所有学习者默认使用完整的
`detailed` 详细档。每道客观题独立给出答案、题干和全部选项翻译、准确证据定位、证据
范围与证据翻译、推理、同义替换或语言点、全部干扰项分析、适用错误标签和重做动作。
完整阅读与听力复盘还要提供全文/原稿翻译和核心词汇。

写作必须判断文体、读者、目的和话题，提供至少三个可写角度、段落提纲、原创范文与
对齐译文、话题词汇、可替换槽位模板、常见错误和量表训练建议。翻译必须给出句意分析、
分句结构、关键词推敲、成句步骤、对齐参考译文与替代表达。按标准中的四六级 Section
A/B/C 与考研英语专项规则执行。题目存在歧义时，先修题再记录练习结果。

## 5. 错误归因

用 `record-practice` 追加练习记录，再统计重复错误：

```bash
python run.py summarize-errors --ledger practice-ledger.json --output error-summary.json
```

错误统计是下一次计划的证据，不是对学习者的最终判断。

## 6. 能力更新

根据练习记录更新能力画像：

```bash
python run.py update-ability --ability ability-profile.json --ledger practice-ledger.json
```

当练习记录或能力历史有足够数据点时，分析趋势：

```bash
python run.py analyze-trends --ledger practice-ledger.json --history ability-history.json --output trend-analysis.json
```

## 7. 作文闭环

写作任务使用 `writing-version` 创建有版本的草稿。需要确定性评分参考时，使用 `score-writing`。

必须说明评分只是规则估算，不是官方评分。用版本元数据比较修改效果，不要覆盖旧稿。

## 8. 下一次计划

把更新后的能力画像和错误统计重新输入 `daily-plan`。优先处理重复出现的高影响错误和低状态能力节点，同时遵守学习者每日时间预算。
