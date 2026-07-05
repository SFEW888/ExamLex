# CET-4 Guide

CET-4 learners often need a stable foundation loop: high-frequency vocabulary, sentence-level grammar repair, reading accuracy, and short writing or translation output.

Supported target bands:

- `425~499`: prioritize pass-line stability, common vocabulary, basic grammar accuracy, and controlled timing.
- `500~550`: add reading speed, paraphrase recognition, and structured writing.
- `550+`: focus on recurring weak points, listening detail capture, and higher-quality output.
- `600+`: prioritize precision, speed, and advanced revision work.

Example daily command:

```powershell
python skills\english-exam-ai-tutor\scripts\generate_daily_plan.py --profile learner-profile.cet4.json --ability ability-profile.json --errors error-summary.json --output cet4-daily-plan.json
```

Use deterministic writing scores as revision guidance only. They are not official CET-4 score guarantees.
