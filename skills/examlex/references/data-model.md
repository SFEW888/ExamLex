# Data Model

Use JSON-compatible data for all durable learner state. YAML and Markdown templates are authoring conveniences; keep field names compatible with the scripts.

## Learner Profile

Template: `assets/templates/learner-profile.json` or `assets/templates/learner-profile.yaml`

Required fields:

- `learner_id`: stable learner identifier.
- `exam_type`: `CET4`, `CET6`, or `POSTGRADUATE_ENGLISH`.
- `foundation_level`: one of the supported foundation levels in `exam-profiles.md`.
- `target_band`: target score band valid for the exam type.
- `daily_time_budget_minutes`: positive integer.

Optional:

- `exam_date`: target date or empty string when unknown.

## Ability Profile

Template: `assets/templates/ability-profile.yaml`

Expected shape:

```json
{
  "learner_id": "learner-id",
  "exam_type": "CET4",
  "modules": {
    "reading": [
      {
        "node": "long sentences",
        "level": 2,
        "status": "needs_work",
        "stats": {
          "total_items": 20,
          "correct_items": 13,
          "error_count": 2,
          "accuracy": 0.65
        }
      }
    ]
  },
  "priority_errors": []
}
```

`level` and `status` are updated from practice accuracy and error counts. Lower levels and `priority` status should receive more planning weight.

## Practice Ledger

Template: `assets/templates/exercise-record.json` or `assets/templates/exercise-record.yaml`

The ledger is a JSON list of records. Each record should include:

- `date`
- `exam_type`
- `module`
- `task_id`
- `duration_minutes`
- `total_items`
- `correct_items`
- `error_tags`

Use `total_items` and `correct_items`. Do not use `total` or `correct`; scripts reject those names to prevent ambiguous accuracy calculations.

When a daily plan assigns an approved strategy, store its immutable reference in `strategy_revisions`. Each item has a `strategy_id` and the revision's `revision_sha256`; `plan_id` records which plan assigned the work. `analyze_trends.py` uses these references to report strategy-level outcomes without attributing later practice to a rewritten method.

## Error Summary

Produced by `scripts/summarize_errors.py`.

Expected top-level fields:

- `total_records`
- `by_tag`
- `by_module`
- `by_dimension`

Use this file as an input to daily planning and weekly review.

## Writing Versions

Template: `assets/templates/writing-version-record.yaml`

The writing versions file is a JSON list of records:

- `writing_id`
- `version`: `V1`, `V2`, `V3`, and so on.
- `source_version`: optional parent version.
- `text`
- `changes`: list of revision notes.

Use `manage_writing_versions.py` to append rather than overwrite drafts.

## Writing Score

Produced by `scripts/score_writing_rubric.py`.

Fields include:

- `label`: `rubric_estimate`
- `exam_type`
- `total_score`
- `max_score`
- `normalized_score`
- `signals`
- `dimensions`

The score is deterministic and useful for revision guidance. It is not official exam scoring.

## Strategy Library

Produced by `scripts/ingest_strategy.py`. Path: `strategy-library.json`.

Required fields per strategy entry:

- `strategy_id`: unique identifier (`{exam}-{module}-{digest}-{seq}`)
- `title`: strategy name
- `source_file`: originating file name
- `source_type`: one of `text`, `book`, `video`, `podcast`, `person`, `course`, `conversation`
- `distillation_method`: one of `direct`, `book`, `video`, `person`, `manual`
- `added_at`: ISO 8601 date
- `exam_types`: list of applicable exam type identifiers
- `modules`: list of ability module identifiers
- `content`: core method description (min 20 chars, max 5000)

Optional fields:

- `source_provenance`: captured source filename, optional URL, raw-source SHA-256, and UTC capture time.
- `revisions`: immutable content-addressed snapshots (`version`, `sha256`, `strategy`). Practice records refer to the revision hash.
- `approval_evidence`: SHA-256 values of the validation and evaluation reports plus the UTC approval time.

- `lifecycle_status`: `draft`, `approved`, or `deprecated`; only `approved` strategies are eligible for daily plans.
- `source_url`: original source URL (video link, book ISBN, person profile)
- `ability_nodes`: list of specific ability nodes this strategy targets
- `steps`: ordered list of executable steps extracted from content
- `tags`: arbitrary string labels for categorization and search
- `ria_structure`: RIA++ distillation output — r_reading, i_interpretation, a1_past, a2_trigger, e_execution, b_boundary
- `mental_model`: cognitive extraction output — name, one_liner, evidence, application, limitations
- `heuristic`: cognitive extraction output — name, rule, scenario, example

The strategy library is global — one file serves all learner profiles. Pass to `generate_daily_plan.py` via `--strategies` to attach relevant methods to planned tasks. See [multi-source-distillation.md](multi-source-distillation.md) for the ingestion workflow.
