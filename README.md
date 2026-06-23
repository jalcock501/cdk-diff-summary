# cdk-diff-summary

`cdk-diff-summary` reads AWS CDK diff JSON and renders a compact Markdown summary.

This repository is the source of truth for both:

- the GitHub Marketplace composite action `jalcock501/cdk-diff-summary`
- the PyPI package `cdk-diff-summary`

It is designed for pull requests and CI jobs where raw CDK or CloudFormation diffs are too noisy. The summary groups adds, modifies, removes, replacements, security group rule changes, and other changes while reducing common churn from IAM policy documents and CDK asset hashes.

The tool deliberately shows changed field paths only, not before/after values, to avoid exposing sensitive infrastructure values in summaries.

## GitHub Action Usage

```yaml
- name: Generate CDK diff JSON
  run: npx cdk diff --json > cdk-diff.json

- name: Summarize CDK diff
  uses: jalcock501/cdk-diff-summary@v1
  with:
    diff-json-path: cdk-diff.json
```

The composite action runs the local checked-out code from the action tag. It does not install `cdk-diff-summary` from PyPI at runtime.

## Action Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `diff-json-path` | yes | | Path to JSON produced by `cdk diff --json`. |
| `summary-title` | no | `CDK diff summary` | Markdown heading for the summary. |
| `max-changed-fields` | no | `8` | Maximum changed field paths shown per resource. |
| `collapse-iam-policies` | no | `true` | Collapse large IAM policy document diffs to a single path such as `PolicyDocument`. |
| `collapse-assets` | no | `true` | Suppress or collapse common CDK asset/hash churn such as asset hashes, S3 object keys, Lambda code hashes, Docker image asset hashes, and CDK metadata asset paths. |
| `fail-on-remove` | no | `false` | Write the summary, then fail the step if visible removes exist. |
| `fail-on-replace` | no | `false` | Write the summary, then fail the step if visible replacements exist. |
| `summary-output-path` | no | | Optional file path to also append the generated Markdown summary. |

## PyPI / CLI Usage

Install with `pipx`:

```bash
pipx install cdk-diff-summary
```

Generate CDK diff JSON:

```bash
npx cdk diff --json > cdk-diff.json
```

Render Markdown to stdout:

```bash
cdk-diff-summary cdk-diff.json
```

Append Markdown to a file:

```bash
cdk-diff-summary cdk-diff.json --output cdk-diff-summary.md
```

Use a custom title and field limit:

```bash
cdk-diff-summary cdk-diff.json \
  --title "Production CDK diff" \
  --max-changed-fields 5
```

Fail when visible removals or replacements exist:

```bash
cdk-diff-summary cdk-diff.json --fail-on-remove --fail-on-replace
```

## CLI Options

| Option | Description |
| --- | --- |
| `diff-json-path` | Path to JSON produced by `cdk diff --json`. May also be set with `DIFF_JSON_PATH`. |
| `--title` | Markdown heading for the summary. Defaults to `CDK diff summary`. |
| `--max-changed-fields` | Maximum changed field paths shown per resource. Defaults to `8`. |
| `--collapse-iam-policies` / `--no-collapse-iam-policies` | Collapse large IAM policy document diffs to compact paths. Enabled by default. |
| `--collapse-assets` / `--no-collapse-assets` | Collapse common CDK asset/hash churn. Enabled by default. |
| `--fail-on-remove` | Write the summary, then exit non-zero if visible resource removes exist. |
| `--fail-on-replace` | Write the summary, then exit non-zero if visible resource replacements exist. |
| `--output` | Optional path to append the generated Markdown summary. |
| `--github-step-summary` | Optional path to append GitHub Step Summary Markdown. Defaults to `$GITHUB_STEP_SUMMARY`. |

Environment variables compatible with the GitHub Action wrapper are also supported:

- `DIFF_JSON_PATH`
- `SUMMARY_TITLE`
- `MAX_CHANGED_FIELDS`
- `COLLAPSE_IAM_POLICIES`
- `COLLAPSE_ASSETS`
- `FAIL_ON_REMOVE`
- `FAIL_ON_REPLACE`
- `SUMMARY_OUTPUT_PATH`
- `GITHUB_STEP_SUMMARY`

CLI arguments take precedence over environment variables.

## Example Output

![Screenshot of a larger CDK diff summary in GitHub Step Summary](docs/assets/cdk-diff-summary-larger-example.png)

```markdown
## CDK diff summary

| Metric | Count |
| --- | ---: |
| Stack changes | 1 |
| Resource changes | 3 |
| Adds | 1 |
| Modifies | 1 |
| Removes | 0 |
| Replacements | 1 |
| Security group changes | 1 |
| Changes shown below | 4 |

### Replacements

| Stack | Logical ID | Action | Resource type | Changed fields |
| --- | --- | --- | --- | --- |
| PaymentsStack | Worker | replace | AWS::Lambda::Function | `Architectures[]`, `Layers[]` |

### Security group changes

| Stack | Security group | Direction | Protocol | Port | Action |
| --- | --- | --- | --- | --- | --- |
| PaymentsStack | AppSecurityGroup | ingress | tcp | 443 | add |
```

## Local Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
python -m build
twine check dist/*
```

Run the action wrapper directly:

```bash
DIFF_JSON_PATH=example_cdk_diff_json/cdk-diff-json-tiny.json \
GITHUB_STEP_SUMMARY=/tmp/cdk-summary.md \
python scripts/cdk_diff_summary.py
```

Run the installed CLI:

```bash
cdk-diff-summary example_cdk_diff_json/cdk-diff-json-tiny.json
```

CDK diff JSON shape can vary by CDK version. If parsing fails, please open an issue with a sanitized example of the JSON shape that failed.
