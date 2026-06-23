# AGENTS.md

## Project Overview

This repository contains `cdk-diff-summary`, a composite GitHub Action that
reads AWS CDK diff JSON and writes a compact Markdown summary to the GitHub
Step Summary.

The action is intentionally small:

- The composite action metadata lives in `action.yml`.
- The action entrypoint is `scripts/cdk_diff_summary.py`.
- Runtime modules live in `src/cdk_diff_summary/`.
- Tests live in `tests/`.
- Example CDK diff fixtures live in `example_cdk_diff_json/`.
- CI workflows live in `.github/workflows/`.

## Core Behavior

- Read CDK diff JSON from `DIFF_JSON_PATH`.
- Parse stack and resource changes from CDK diff JSON, tolerating reasonable
  shape differences across CDK versions.
- Render counts for stack changes, resource changes, adds, modifies, removes,
  replacements, and changes shown below.
- Group visible resource changes into replacements, removes, adds, modifies,
  and other changes.
- Render changed field paths only, not before/after values.
- Cap changed fields per resource using `MAX_CHANGED_FIELDS`, appending `...`
  when truncated.
- Collapse noisy IAM policy document paths when enabled.
- Collapse or suppress common CDK asset/hash churn when enabled.
- Append Markdown to `$GITHUB_STEP_SUMMARY`.
- Also append the same Markdown to `SUMMARY_OUTPUT_PATH` when provided.
- Write the summary before exiting non-zero for `FAIL_ON_REMOVE` or
  `FAIL_ON_REPLACE`.
- Keep Python runtime dependency-free and standard-library only.

## Action Inputs

Keep `action.yml` inputs aligned with environment variables read by the Python
script:

- `diff-json-path` -> `DIFF_JSON_PATH`
- `summary-title` -> `SUMMARY_TITLE`
- `max-changed-fields` -> `MAX_CHANGED_FIELDS`
- `collapse-iam-policies` -> `COLLAPSE_IAM_POLICIES`
- `collapse-assets` -> `COLLAPSE_ASSETS`
- `fail-on-remove` -> `FAIL_ON_REMOVE`
- `fail-on-replace` -> `FAIL_ON_REPLACE`
- `summary-output-path` -> `SUMMARY_OUTPUT_PATH`

The composite action should continue to call:

```bash
python "$GITHUB_ACTION_PATH/scripts/cdk_diff_summary.py"
```

Do not inline Python logic in `action.yml`.

## Development Commands

Install dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest
```

Run lint checks:

```bash
ruff check .
```

Before completing code changes, run both validation commands. If either command
cannot be run, say so explicitly and explain why.

## Coding Guidelines

- Keep changes small, explicit, and task-scoped.
- Prefer existing function names and patterns unless there is a clear reason to
  change them.
- Preserve backward compatibility for existing action inputs where practical.
- Do not add runtime dependencies.
- Use standard-library Python for action behavior.
- Show changed field paths, never CDK or CloudFormation before/after values.
- Avoid broad refactors unless they directly support the requested change.
- Update README examples and input docs when action behavior changes.
- Keep default noise reduction conservative. Do not hide removals or
  replacements.

## Testing Guidelines

- Add or update pytest coverage for meaningful behavior changes.
- Cover rendered Markdown and lower-level helper behavior when changing parser,
  collapse, fail-gate, or rendering logic.
- Keep tests synthetic or sanitized. Do not use secrets, tokens, account
  credentials, certificates, or unsanitized production CDK output.
- Use fixtures in `example_cdk_diff_json/` when broader parser coverage or
  smoke-style behavior is useful.
- CI should test both Python logic and the real local composite action via
  `uses: ./`.

## GitHub Actions Guidelines

- CI should run `python -m pytest`.
- CI should run `ruff check .`.
- CI should build the PyPI package with `python -m build`.
- CI should run `twine check dist/*`.
- CI should smoke test the real composite action with `uses: ./`.
- CI should include at least one larger example fixture smoke test so the
  generated Markdown report can be inspected.
- Actionlint is useful when practical.
- Tagging and release workflow changes should be conservative and avoid
  rewriting existing tags.

## Security and Privacy

- Treat CDK diff JSON as potentially sensitive infrastructure data.
- Do not add output that prints resource values from old/new, before/after,
  or equivalent fields.
- Do not expand large IAM policy documents into the summary.
- Do not include secrets or realistic production identifiers in new tests,
  docs, or examples.
- Ask before adding dependencies, network calls, destructive git commands, or
  infrastructure commands.

## Review Priorities

When reviewing changes, focus on:

- IAM policy document collapse accidentally hiding material policy changes.
- CDK asset/hash collapse accidentally hiding material resource changes.
- Removals and replacements staying visible even when collapse options are
  enabled.
- `fail-on-remove` and `fail-on-replace` writing summaries before exiting
  non-zero.
- Changed field truncation appending `...` without printing values.
- Leaking old/new, before/after, or otherwise sensitive values into summaries.
- Broken action input wiring between `action.yml` and environment variables.
- README examples staying aligned with implemented behavior.
- Missing tests for new parsing, collapse, fail-gate, or rendering behavior.
- Parser changes becoming too tightly coupled to one CDK diff JSON shape.
