# Configuration

The public repository runs without secrets. Configuration is optional and mainly exists for local experiments or downstream integrations.

## Environment File

Copy `.env.example` to `.env` only when a local wrapper needs environment variables.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `ENGLISH_EXAM_TUTOR_PROMPT_MODE` | No | `public-safe` | Public-safe mode keeps private prompt bodies out of generated artifacts. |
| `ENGLISH_EXAM_TUTOR_DATA_DIR` | No | `./local/data` | Suggested location for learner records and generated plans. |
| `ENGLISH_EXAM_TUTOR_PRIVATE_PROMPT_DIR` | No | empty | Optional local-only directory for full-local private prompt assets. |
| `ENGLISH_EXAM_TUTOR_DEFAULT_EXAM` | No | `CET4` | Default exam type for local wrappers. |
| `ENGLISH_EXAM_TUTOR_DEFAULT_TARGET` | No | `550+` | Default target band for local wrappers. |

## Secret Handling

Never commit `.env`, private prompt files, learner-identifying records, tokens, passwords, or local database credentials.

The repository validation script enforces the public-safe prompt mode in `pyproject.toml`, but contributors are still responsible for reviewing examples, screenshots, release notes, and issues before publishing.
