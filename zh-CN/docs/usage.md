# 使用流程

以下流程默认在项目根目录中使用 PowerShell。

## 1. 校验仓库

```powershell
python scripts\validate_repo.py --root . --json
```

## 2. 校验学习者档案

可以从 `examples\sample-learner-profile.yaml` 或 `skills\examlex\assets\templates\learner-profile.json` 开始。

```powershell
python -m examlex validate-profile --profile examples\sample-learner-profile.yaml
```

如果有校验错误，先修正档案，再生成计划。

## 3. 生成每日计划

```powershell
python -m examlex daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --strategies strategy-library.json --output daily-plan.json
```

如果暂时没有错误统计，第一次计划可以省略 `--errors`。

当 `summarize-errors` 生成 `error-summary.json` 后，把它输入下一次计划：

```powershell
python -m examlex daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --strategies strategy-library.json --errors error-summary.json --output daily-plan.next.json
```

## 4. 每日闭环

记录每次练习结果，必须写清题目总数、正确数和错误标签：

```powershell
python -m examlex record-practice --ledger practice-ledger.json --date 2026-07-05 --exam-type CET6 --module reading --task-id reading-long-sentence-01 --duration-minutes 25 --total-items 12 --correct-items 8 --error-tags READING_LONG_SENTENCE_FAIL READING_PARAPHRASE_FAIL --print-record
```

如需把练习结果归因到日计划中的策略修订版本，使用日计划文件和任务索引：

```powershell
python -m examlex record-practice --ledger practice-ledger.json --plan daily-plan.next.json --plan-task-index 0 --date 2026-07-05 --exam-type CET6 --module reading --task-id reading-long-sentence-01 --duration-minutes 25 --total-items 12 --correct-items 8
```

统计练习记录中的错误：

```powershell
python -m examlex summarize-errors --ledger practice-ledger.json --output error-summary.json
```

更新能力画像：

```powershell
python -m examlex update-ability --ability examples\sample-ability-profile.yaml --ledger practice-ledger.json --output ability-profile.next.json
```

用更新后的证据生成明天计划：

```powershell
python -m examlex daily-plan --profile examples\sample-learner-profile.yaml --ability ability-profile.next.json --strategies strategy-library.json --errors error-summary.json --output daily-plan.next.json
```

## 5. 作文闭环

追加作文版本，不要覆盖旧稿：

```powershell
python -m examlex writing-version --file writing-versions.json --writing-id essay-001 --text "First draft text"
```

用确定性评分规则给作文一个修改参考：

```powershell
python -m examlex score-writing --text "I will compare two views and explain why consistent practice matters for postgraduate English preparation." --exam-type POSTGRADUATE_ENGLISH --output writing-score.json
```

这个分数只用于指导修改，不能当作官方考试评分。

## 6. 周复盘

每周结束时统计错误和趋势：

```powershell
python -m examlex summarize-errors --ledger practice-ledger.json --output weekly-error-summary.json
python -m examlex analyze-trends --ledger practice-ledger.json --history ability-history.json --output weekly-trends.json
```

## 备份与恢复

创建备份后，保存命令输出中的 `checksum_sha256` 到备份目录之外。恢复时必须提供该值，避免被同时篡改的归档与内部清单通过校验：

```powershell
python -m examlex backup --data-dir .\data --output backup.tar.gz
python -m examlex restore --data-dir .\data --input backup.tar.gz --expected-checksum <创建时返回的checksum_sha256>
```

可以使用 `skills\examlex\assets\templates\weekly-review.md` 编写面向学习者的复盘。复盘应基于已完成任务、重复错误标签和能力变化。

## 可选：安装短命令

如果想使用最短命令名：

```powershell
python -m pip install -e .
examlex validate-profile --profile examples\sample-learner-profile.yaml
examlex daily-plan --profile examples\sample-learner-profile.yaml --ability examples\sample-ability-profile.yaml --strategies strategy-library.json --output daily-plan.json
```
