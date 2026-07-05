# 四级指南

四级学习者通常需要稳定的基础闭环：高频词汇、句子级语法修复、阅读准确率，以及短篇写作或翻译输出。

支持的目标区间：

- `425~499`：优先保证过线稳定性、常见词汇、基础语法准确和时间控制。
- `500~550`：增加阅读速度、同义替换识别和结构化写作。
- `550+`：聚焦反复薄弱点、听力细节捕捉和更高质量输出。
- `600+`：优先提升准确性、速度和高级修改能力。

示例每日计划命令：

```powershell
python -m skills.english_exam_ai_tutor daily-plan --profile learner-profile.cet4.json --ability ability-profile.json --errors error-summary.json --output cet4-daily-plan.json
```

确定性作文评分只能作为修改参考，不是官方四级成绩保证。
