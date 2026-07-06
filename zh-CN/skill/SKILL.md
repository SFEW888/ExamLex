---
name: english-exam-ai-tutor
description: 用于支持四级、六级和考研英语备考，包括能力诊断、每日计划、错误归因、词汇/听力/阅读/翻译/写作练习、作文评分与版本管理，以及 public-safe/full-local 提示词模式选择。
---

# 英语考试 AI 助教 Skill

使用本 Skill 运行一个可移植的英语考试助教工作区，服务四级、六级和考研英语学习者。工作流必须基于证据：校验学习者档案，生成受约束计划，记录练习和错误标签，更新能力画像，再根据观察数据调整下一次计划。

## 模式选择

- Public-safe 模式：只使用八个助教的占位符和公开描述。不要发布完整私有或原始提示词。
- Full-local 模式：如果用户在公开仓库之外有本地私有提示词资产，可以在本机使用。运行时也不能改写原始八个助教提示词。
- 不确定时，默认使用 public-safe 模式；在读取或使用本地私有提示词资产前先确认。

发布、打包或同步 Skill 之前，阅读 [references/prompt-modes.md](references/prompt-modes.md)。选择助教角色时，阅读 [references/assistant-roster.md](references/assistant-roster.md)。

## 运行流程

可以从 Skill 目录运行脚本，也可以从项目根目录按路径引用。

1. 校验输入：
   `python -m skills.english_exam_ai_tutor validate-profile --profile learner-profile.json`
2. 生成每日计划：
   `python -m skills.english_exam_ai_tutor daily-plan --profile learner-profile.json --ability ability-profile.json --errors error-summary.json --output daily-plan.json`
3. 记录练习并标记错误：
   `python -m skills.english_exam_ai_tutor tag-error --module writing --text "..."`
   `python -m skills.english_exam_ai_tutor record-practice --ledger practice-ledger.json --date 2026-07-05 --exam-type CET4 --module writing --task-id writing-article-drill --duration-minutes 20 --total-items 10 --correct-items 7 --error-tags WRITING_ARTICLE_OMISSION`
4. 统计错误：
   `python -m skills.english_exam_ai_tutor summarize-errors --ledger practice-ledger.json --output error-summary.json`
5. 更新能力并分析趋势：
   `python -m skills.english_exam_ai_tutor update-ability --ability ability-profile.json --ledger practice-ledger.json`
   `python -m skills.english_exam_ai_tutor analyze-trends --ledger practice-ledger.json --history ability-history.json --output trend-analysis.json`
6. 管理作文草稿并估算作文质量：
   `python -m skills.english_exam_ai_tutor writing-version --file writing-versions.json --writing-id essay-001 --text "..."`
   `python -m skills.english_exam_ai_tutor score-writing --text-file essay.txt --exam-type CET4 --output writing-score.json`

学习闭环见 [references/workflow.md](references/workflow.md)，文件结构见 [references/data-model.md](references/data-model.md)。

## 多源持续学习

从任意来源提取备考策略并写入 `strategy-library.json`。五种蒸馏方式全部内置，无需外部 Skill。

### 蒸馏管线

1. **提取**: `tutor extract --input <url|file|name>` — 下载/解析原始材料
2. **蒸馏**: Agent 按方法论指南执行推理 → 写入 `distilled.json`
3. **校验**: `tutor validate --artifacts-dir <path>` — 格式检查 + Darwin 6维评分
4. **评估**: Agent 运行测试 prompt 评分效果维度 → 写入 `evaluation.json`
5. **提交**: `tutor commit --artifacts-dir <path> --library strategy-library.json` — 棘轮检查 + 原子写入

### 蒸馏方式

| 方法 | 输入类型 | 说明 |
|------|---------|------|
| `direct` | 文本/Markdown | 直接读取提取 |
| `book` | PDF/EPUB/DOCX | 结构化提取→章节+术语表+模式库 |
| `video` | B站/YouTube URL | yt-dlp下载→ASR→RIA-TV++蒸馏 |
| `person` | 教师/专家姓名 | 六路调研→五层认知提取 |
| `manual` | 对话笔记 | Agent识别可操作方法 |

### Darwin 评分

每条策略自动进行 9 维评分（满分 100）。低于 70 分自动触发爬山优化（最多 3 轮）。高分策略在生成每日计划时优先引用。详见 [references/darwin-rubric.md](../skill/references/darwin-rubric.md)。

```bash
tutor check-deps      # 查看依赖状态
tutor ops-check       # 13项运维检查
```

## 约束

- 不要在 full-local 模式中改写原始八个助教提示词。
- 公开发布必须使用 public-safe 占位符，不能包含完整私有或原始提示词。
- 作文评分是确定性评分参考，不是官方考试评分。
- 练习记录必须使用 `total_items` 和 `correct_items`，不要使用 `total` 或 `correct`。
- 即使模板使用 YAML 或 Markdown，持久数据也要保持 JSON 兼容。
- 面向学习者的建议必须绑定四级、六级或考研英语目标区间，以及学习者诊断出的基础水平。

## 参考资料和模板

- [references/assistant-roster.md](references/assistant-roster.md)：八个助教、角色边界和 public-safe 占位符。
- [references/error-taxonomy.md](references/error-taxonomy.md)：模块/维度树和有效错误标签。
- [references/exam-profiles.md](references/exam-profiles.md)：支持的考试类型、基础水平和目标区间。
- [references/prompt-modes.md](references/prompt-modes.md)：public-safe 与 full-local 的发布规则。
- [references/workflow.md](references/workflow.md)：从诊断到下一阶段计划的闭环。
- [references/data-model.md](references/data-model.md)：学习者档案、能力画像、练习记录、作文版本和统计摘要。
