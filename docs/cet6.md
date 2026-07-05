# CET-6 Guide

CET-6 preparation usually needs more attention to inference, paraphrase recognition, listening detail capture, word choice, and output quality.

Supported target bands:

- `425~499`: stabilize core vocabulary, long-sentence parsing, and basic writing task completion.
- `500~550`: improve reading speed, listening keyword capture, and translation accuracy.
- `550+`: reduce recurring high-impact errors and raise expression richness.
- `600+`: emphasize timing, precision, advanced vocabulary use, and polished writing or translation.

Example practice record:

```powershell
python skills\english-exam-ai-tutor\scripts\record_practice.py --ledger cet6-ledger.json --date 2026-07-05 --exam-type CET6 --module listening --task-id listening-keyword-01 --duration-minutes 20 --total-items 15 --correct-items 11 --error-tags LISTENING_KEYWORD_MISS --print-record
```

Treat all generated plans and writing scores as study guidance. The toolkit does not promise an official CET-6 score.
