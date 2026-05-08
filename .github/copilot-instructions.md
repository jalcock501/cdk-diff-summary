# Copilot Instructions

This repository is a composite GitHub Action named `cdk-diff-summary`.

## What Matters Most

- Keep the action dependency-free at runtime.
- Keep the action entrypoint in `scripts/cdk_diff_summary.py`.
- Keep implementation modules under `scripts/cdk_diff_summary/`.
- Do not inline Python logic in `action.yml`.
- Preserve backward compatibility for existing action inputs where practical.
- Never show CDK/CloudFormation before/after values in summaries; show changed
  field paths only.
- Treat CDK diff JSON as potentially sensitive infrastructure data.
- Keep default noise reduction conservative. Do not hide removals or
  replacements.

## Validation

Before proposing or completing code changes, run:

```bash
poetry run test
poetry run ruff check .
```

If either command cannot be run, say so explicitly and explain why.

## Review Focus

For Copilot reviews, pay special attention to:

- IAM policy document collapse accidentally hiding material policy changes.
- CDK asset/hash collapse accidentally hiding material resource changes.
- Removals and replacements staying visible even when collapse options are
  enabled.
- `fail-on-remove` and `fail-on-replace` writing the summary before exiting
  non-zero.
- Changed field truncation appending `...` without printing before/after
  values.
- Action inputs in `action.yml` matching environment variables read by the
  script.
- README examples staying aligned with implemented behavior.
- CI smoke tests exercising the real composite action with `uses: ./`,
  including at least one larger example fixture summary.
- Parser changes remaining tolerant of CDK diff JSON shape differences across
  CDK versions.
