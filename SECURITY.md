# Security Policy

## Supported Versions

Security fixes target the current `main` or `master` branch until formal releases are introduced.

## Reporting a Vulnerability

Do not open a public issue for suspected secret leakage, prompt leakage, or executable script vulnerabilities.

Report privately to the repository maintainer. If no private channel is configured yet, open a minimal public issue that says a private security report is needed, without including exploit details, private prompts, tokens, or local file paths containing secrets.

## Scope

Relevant security concerns include:

- private prompt bodies or learner data accidentally committed,
- install scripts writing outside intended Skill locations,
- command-line behavior that overwrites files without explicit user intent,
- schema or ledger handling that can corrupt learner records,
- dependency or CI changes that introduce unsafe execution paths.

## Prompt Safety

The public repository must remain in `public-safe` mode. Full-local prompt assets belong outside this repository and must not be included in issues, examples, tests, screenshots, or release artifacts.
