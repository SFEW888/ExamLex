# Changelog

ExamLex follows a human-written changelog.

## Unreleased

## 0.2.0 - 2026-07-16

- Make detailed answerbooks the default for every learner across CET-4, CET-6, Postgraduate English, TEM-4, and TEM-8, with exam-specific playbooks, bilingual options, local evidence, distractor rejection, full support translations, writing scaffolds, and translation deliberation.
- Add machine-readable paper and answerbook schemas, five-exam artifact profiles, a validator, regression tests, and TEM-4/TEM-8 writing anchors.
- Add a detailed vocabulary memorization block with phonetics, part-of-speech meanings, an accurate memory route, an original bilingual example, word family, and active recall.
- Replace misleading rounded vocabulary filenames with exact-count verified pools: CET-4 3,331, CET-6 3,650, and Postgraduate English 1,014; keep 100-entry curated starters for TEM-4 and TEM-8.
- Add transactional SQLite strategy storage, JSON import/export, review-only near-duplicate detection, and write-time duplicate warnings.
- Add a true background capacity monitor: regenerable session artifacts have time and byte hard limits, while strategy data only triggers durable warnings and duplicate candidates and is never automatically deleted.
- Remove the duplicated Python/resource mirror. `skills/examlex/` is now the canonical package and `examlex/` is a thin compatibility bridge, reducing tracked project growth as resources expand.
- Expand repository, packaging, public-safety, and regression validation for the new contracts.
