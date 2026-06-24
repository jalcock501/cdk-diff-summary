# cdk-diff-summary

`cdk-diff-summary` reads CloudFormation change set JSON and renders a compact Markdown summary.

This repository is the source of truth for both:

- the GitHub Marketplace composite action `jalcock501/cdk-diff-summary`
- the PyPI package `cdk-diff-summary`

It is designed for pull requests and CI jobs where raw CDK or CloudFormation diffs are too noisy. The summary groups adds, modifies, removes, replacements, security group rule changes, and other changes while reducing common churn from IAM policy documents and CDK asset hashes.

The tool deliberately shows changed field paths only, not before/after values, to avoid exposing sensitive infrastructure values in summaries.

## GitHub Action Usage

```yaml
- name: Create CDK change set
  run: |
    npx cdk deploy \
      --method=prepare-change-set \
      --change-set-name pr-${{ github.event.pull_request.number || github.run_id }} \
      --require-approval never

- name: Describe CloudFormation change set
  run: |
    aws cloudformation describe-change-set \
      --stack-name MyStack \
      --change-set-name pr-${{ github.event.pull_request.number || github.run_id }} \
      --output json > change-set.json

- name: Summarize CDK diff
  uses: jalcock501/cdk-diff-summary@v1
  with:
    diff-json-path: change-set.json
```

The composite action runs the local checked-out code from the action tag. It does not install `cdk-diff-summary` from PyPI at runtime.

AWS CDK does not provide a stable `cdk diff --json` output. Use CloudFormation change sets, then pass the JSON from `aws cloudformation describe-change-set` to this action.

## Action Inputs

| Input                   | Required | Default            | Description                                                                                                                                                         |
| ----------------------- | -------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `diff-json-path`        | yes      |                    | Path to CDK or CloudFormation change set JSON.                                                                                                                      |
| `summary-title`         | no       | `CDK diff summary` | Markdown heading for the summary. Pass an empty string to suppress the heading.                                                                                      |
| `max-changed-fields`    | no       | `8`                | Maximum changed field paths shown per resource.                                                                                                                     |
| `collapse-iam-policies` | no       | `true`             | Collapse large IAM policy document diffs to a single path such as `PolicyDocument`.                                                                                 |
| `collapse-assets`       | no       | `true`             | Suppress or collapse common CDK asset/hash churn such as asset hashes, S3 object keys, Lambda code hashes, Docker image asset hashes, and CDK metadata asset paths. |
| `fail-on-remove`        | no       | `false`            | Write the summary, then fail the step if visible removes exist.                                                                                                     |
| `fail-on-replace`       | no       | `false`            | Write the summary, then fail the step if visible replacements exist.                                                                                                |
| `summary-output-path`   | no       |                    | Optional file path to also append the generated Markdown summary.                                                                                                   |

## PyPI / CLI Usage

Install with `pipx`:

```bash
pipx install cdk-diff-summary
```

Generate CloudFormation change set JSON:

```bash
aws cloudformation describe-change-set \
  --stack-name MyStack \
  --change-set-name MyChangeSet \
  --output json > change-set.json
```

Render Markdown to stdout:

```bash
cdk-diff-summary change-set.json
```

Append Markdown to a file:

```bash
cdk-diff-summary change-set.json --output cdk-diff-summary.md
```

Use a custom title and field limit:

```bash
cdk-diff-summary change-set.json \
  --title "Production CDK diff" \
  --max-changed-fields 5
```

Fail when visible removals or replacements exist:

```bash
cdk-diff-summary change-set.json --fail-on-remove --fail-on-replace
```

## CLI Options

| Option                                                   | Description                                                                                        |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `diff-json-path`                                         | Path to CDK or CloudFormation change set JSON. May also be set with `DIFF_JSON_PATH`.              |
| `--title`                                                | Markdown heading for the summary. Defaults to `CDK diff summary`; pass `""` to suppress it.        |
| `--max-changed-fields`                                   | Maximum changed field paths shown per resource. Defaults to `8`.                                   |
| `--collapse-iam-policies` / `--no-collapse-iam-policies` | Collapse large IAM policy document diffs to compact paths. Enabled by default.                     |
| `--collapse-assets` / `--no-collapse-assets`             | Collapse common CDK asset/hash churn. Enabled by default.                                          |
| `--fail-on-remove` / `--no-fail-on-remove`               | Write the summary, then exit non-zero if visible resource removes exist. Disabled by default.      |
| `--fail-on-replace` / `--no-fail-on-replace`             | Write the summary, then exit non-zero if visible resource replacements exist. Disabled by default. |
| `--output`                                               | Optional path to append the generated Markdown summary.                                            |
| `--github-step-summary`                                  | Optional explicit path to append GitHub Step Summary Markdown.                                     |

Environment variables compatible with the GitHub Action wrapper are also supported:

- `DIFF_JSON_PATH`
- `SUMMARY_TITLE`
- `MAX_CHANGED_FIELDS`
- `COLLAPSE_IAM_POLICIES`
- `COLLAPSE_ASSETS`
- `FAIL_ON_REMOVE`
- `FAIL_ON_REPLACE`
- `SUMMARY_OUTPUT_PATH`

CLI arguments take precedence over environment variables.

## Example Output

![Screenshot of a larger CDK diff summary in GitHub Step Summary](docs/assets/cdk-diff-summary-larger-example.png)

```markdown
## CDK diff summary

| Metric                 | Count |
| ---------------------- | ----: |
| Stack changes          |     1 |
| Resource changes       |     3 |
| Adds                   |     1 |
| Modifies               |     1 |
| Removes                |     0 |
| Replacements           |     1 |
| Security group changes |     1 |
| Changes shown below    |     4 |

### Replacements

| Stack         | Logical ID | Action  | Resource type         | Changed fields                |
| ------------- | ---------- | ------- | --------------------- | ----------------------------- |
| PaymentsStack | Worker     | replace | AWS::Lambda::Function | `Architectures[]`, `Layers[]` |

### Security group changes

| Stack         | Security group   | Direction | Protocol | Port | Action |
| ------------- | ---------------- | --------- | -------- | ---- | ------ |
| PaymentsStack | AppSecurityGroup | ingress   | tcp      | 443  | add    |
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
DIFF_JSON_PATH=example_cdk_changesets_json/small-webstack-cdk-diff.json \
python scripts/cdk_diff_summary.py --github-step-summary /tmp/cdk-summary.md
```

Run the installed CLI:

```bash
cdk-diff-summary example_cdk_changesets_json/small-webstack-cdk-diff.json
```

CloudFormation change set JSON can vary depending on resource type and change source. If parsing fails, please open an issue with a sanitized example of the JSON shape that failed.
