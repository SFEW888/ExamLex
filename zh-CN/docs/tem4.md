# TEM-4（英语专业四级）考试说明

## 概述

TEM-4（Test for English Majors — Band 4）是全国高校英语专业四级考试，面向英语专业二年级本科生。

## 考试结构

| 模块 | 时间（分钟） | 权重 | 说明 |
|------|:---------:|:----:|------|
| 听写 (Dictation) | 15 | 15% | 全文听写（约80-100词） |
| 听力理解 (Listening) | 20 | 15% | 对话和短文 |
| 语言知识 (Language Knowledge) | 10 | 20% | 语法和词汇选择题 |
| 完形填空 (Cloze) | 10 | 10% | 20空完形填空 |
| 阅读理解 (Reading) | 25 | 20% | 阅读选择题 |
| 写作 (Writing) | 35 | 20% | 命题作文（约200词） |

## 目标分数段

| 区间 | 分数范围 | 等级 |
|------|:------:|------|
| 60~69 | 60-69 | 合格 |
| 70~79 | 70-79 | 良好 |
| 80+ | 80-100 | 优秀 |

## 能力树专属模块

除 CET 通用模块外，TEM-4 新增：

- **language-knowledge（语言知识）**：语法选择、词汇辨析
- **dictation（听写）**：听写准确率、拼写速度

## 错误标签

| 错误标签 | 模块 | 能力节点 |
|----------|------|----------|
| `LANG_GRAMMAR_SELECT_FAIL` | language-knowledge | 语法选择 |
| `LANG_VOCAB_DISCRIMINATE_FAIL` | language-knowledge | 词汇辨析 |
| `DICTATION_ACCURACY_LOW` | dictation | 听写准确率 |
| `DICTATION_SPELLING_SPEED_LOW` | dictation | 拼写速度 |

## 使用示例

```bash
# 验证 TEM-4 学习者档案
tutor check tem4-learner-profile.json

# 生成 TEM-4 每日计划
tutor plan tem4-learner-profile.json \
  --ability tem4-ability-profile.json \
  --vocab-pool skills/english-exam-ai-tutor/assets/data/vocabulary/tem4-core-2000.json \
  --output daily-plan.json
```
