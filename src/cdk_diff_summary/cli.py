"""Command-line interface for cdk-diff-summary."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from os import environ
from pathlib import Path
from typing import TextIO

from cdk_diff_summary.config import DEFAULT_TITLE, parse_bool, parse_max_changed_fields
from cdk_diff_summary.diff import DiffSummary, parse_diff
from cdk_diff_summary.render import render_summary


@dataclass(frozen=True)
class CliConfig:
    diff_json_path: str
    title: str
    max_changed_fields: int
    collapse_iam_policies: bool
    collapse_assets: bool
    fail_on_remove: bool
    fail_on_replace: bool
    output_path: str
    github_step_summary: str


def main(argv: list[str] | None = None) -> int:
    try:
        config = parse_args(argv)
        diff_summary = parse_diff_from_file(config)
        markdown = render_summary(
            diff_summary,
            title=config.title,
            max_changed_fields=config.max_changed_fields,
        )
        append_outputs(config, markdown)
        return fail_status(config, diff_summary)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cdk-diff-summary: {exc}", file=sys.stderr)
        return 1


def parse_args(argv: list[str] | None = None) -> CliConfig:
    parser = argparse.ArgumentParser(
        description="Render a compact Markdown summary from AWS CDK diff JSON.",
    )
    parser.add_argument(
        "diff_json_path",
        nargs="?",
        help="Path to JSON produced by cdk diff --json. Defaults to DIFF_JSON_PATH.",
    )
    parser.add_argument(
        "--title",
        default=environ.get("SUMMARY_TITLE", DEFAULT_TITLE) or DEFAULT_TITLE,
        help="Markdown heading for the summary.",
    )
    parser.add_argument(
        "--max-changed-fields",
        default=environ.get("MAX_CHANGED_FIELDS", "8"),
        help="Maximum changed field paths to show for each resource.",
    )
    parser.add_argument(
        "--collapse-iam-policies",
        action=argparse.BooleanOptionalAction,
        default=parse_bool(environ.get("COLLAPSE_IAM_POLICIES"), default=True),
        help="Collapse IAM policy document changes. Enabled by default.",
    )
    parser.add_argument(
        "--collapse-assets",
        action=argparse.BooleanOptionalAction,
        default=parse_bool(environ.get("COLLAPSE_ASSETS"), default=True),
        help="Collapse common CDK asset/hash churn. Enabled by default.",
    )
    parser.add_argument(
        "--fail-on-remove",
        action="store_true",
        default=parse_bool(environ.get("FAIL_ON_REMOVE"), default=False),
        help="Exit non-zero after writing the summary if visible removes exist.",
    )
    parser.add_argument(
        "--fail-on-replace",
        action="store_true",
        default=parse_bool(environ.get("FAIL_ON_REPLACE"), default=False),
        help="Exit non-zero after writing the summary if visible replacements exist.",
    )
    parser.add_argument(
        "--output",
        default=environ.get("SUMMARY_OUTPUT_PATH", "").strip(),
        help="Optional path to append the generated Markdown summary.",
    )
    parser.add_argument(
        "--github-step-summary",
        default=environ.get("GITHUB_STEP_SUMMARY", "").strip(),
        help="Optional path to append GitHub Step Summary Markdown.",
    )

    args = parser.parse_args(argv)
    diff_json_path = args.diff_json_path or environ.get("DIFF_JSON_PATH", "").strip()
    if not diff_json_path:
        raise ValueError("diff-json-path argument or DIFF_JSON_PATH is required")

    return CliConfig(
        diff_json_path=diff_json_path,
        title=args.title,
        max_changed_fields=parse_max_changed_fields(str(args.max_changed_fields)),
        collapse_iam_policies=args.collapse_iam_policies,
        collapse_assets=args.collapse_assets,
        fail_on_remove=args.fail_on_remove,
        fail_on_replace=args.fail_on_replace,
        output_path=args.output,
        github_step_summary=args.github_step_summary,
    )


def parse_diff_from_file(config: CliConfig) -> DiffSummary:
    with Path(config.diff_json_path).open(encoding="utf-8") as handle:
        document = json.load(handle)
    return parse_diff(
        document,
        collapse_iam_policies=config.collapse_iam_policies,
        collapse_assets=config.collapse_assets,
    )


def append_outputs(config: CliConfig, markdown: str) -> None:
    if config.github_step_summary:
        append_file(Path(config.github_step_summary), markdown)
    if config.output_path:
        append_file(Path(config.output_path), markdown)
    if not config.github_step_summary and not config.output_path:
        sys.stdout.write(markdown)


def append_file(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        append_markdown(handle, markdown)


def append_markdown(handle: TextIO, markdown: str) -> None:
    handle.write(markdown)
    if not markdown.endswith("\n"):
        handle.write("\n")


def fail_status(config: CliConfig, diff_summary: DiffSummary) -> int:
    if config.fail_on_remove and diff_summary.removes > 0:
        print(
            "cdk-diff-summary: visible removes found and --fail-on-remove is set",
            file=sys.stderr,
        )
        return 2
    if config.fail_on_replace and diff_summary.replacements > 0:
        print(
            "cdk-diff-summary: visible replacements found and --fail-on-replace is set",
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
