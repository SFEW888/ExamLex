# TEM-8（英语专业八级）考试说明

## 概述

TEM-8（Test for English Majors — Band 8）是全国高校英语专业最高级别的考试，面向英语专业四年级本科生。

## 考试结构

| 模块 | 时间（分钟） | 权重 | 说明 |
|------|:---------:|:----:|------|
| 听力理解 (Listening) | 25 | 20% | Mini-lecture + 访谈 |
| 阅读理解 (Reading) | 30 | 20% | 阅读选择题 |
| 语言知识 (Language Knowledge) | 15 | 15% | 语言运用（如有） |
| 翻译 (Translation) | 25 | 20% | 英译汉 + 汉译英 |
| 写作 (Writing) | 45 | 20% | 命题作文（约300词） |
| 改错 (Proofreading) | 15 | 5% | 短文改错 |

## 目标分数段

| 区间 | 分数范围 | 等级 |
|------|:------:|------|
| 60~69 | 60-69 | 合格 |
| 70~79 | 70-79 | 良好 |
| 80+ | 80-100 | 优秀 |

## 能力树专属模块

除 CET 通用模块外，TEM-8 新增：

- **proofreading（改错）**：冠词错误、搭配错误、逻辑错误

## 错误标签

| 错误标签 | 模块 | 能力节点 |
|----------|------|----------|
| `PROOFREAD_ARTICLE_MISS` | proofreading | 冠词错误 |
| `PROOFREAD_COLLOCATION_FAIL` | proofreading | 搭配错误 |
| `PROOFREAD_LOGIC_INCOHERENT` | proofreading | 逻辑错误 |

## 使用示例

```powershell
# 验证 TEM-8 学习者档案
examlex check tem8-learner-profile.json

# 生成 TEM-8 每日计划（含计时训练）
examlex plan tem8-learner-profile.json `
  --ability tem8-ability-profile.json `
  --vocab-pool skills/examlex/assets/data/vocabulary/tem8-core-2000.json `
  --output daily-plan.json

# 记录 TEM-8 计时改错练习
examlex log practice-ledger.json `
  --date 2026-07-06 --exam-type TEM8 --module proofreading `
  --task-id proofread-001 --duration 15 --total 10 --correct 7 `
  --timed --time-limit 15 `
  --error-tags PROOFREAD_COLLOCATION_FAIL
```
