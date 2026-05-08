"""Command-line entrypoint for GitHub Actions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from cdk_diff_summary.config import Config, load_config
from cdk_diff_summary.diff import parse_diff
from cdk_diff_summary.render import render_summary


def main() -> int:
    try:
        config = load_config()
        diff_summary = parse_diff_from_config(config)
        markdown = render_summary(
            diff_summary,
            title=config.summary_title,
            max_changed_fields=config.max_changed_fields,
        )
        append_outputs(config, markdown)
        if config.fail_on_remove and diff_summary.removes > 0:
            print(
                "cdk-diff-summary: visible removes found and FAIL_ON_REMOVE is true",
                file=sys.stderr,
            )
            return 2
        if config.fail_on_replace and diff_summary.replacements > 0:
            print(
                "cdk-diff-summary: visible replacements found and FAIL_ON_REPLACE is true",
                file=sys.stderr,
            )
            return 3
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cdk-diff-summary: {exc}", file=sys.stderr)
        return 1
    return 0


def build_summary(config: Config) -> str:
    diff_summary = parse_diff_from_config(config)
    return render_summary(
        diff_summary,
        title=config.summary_title,
        max_changed_fields=config.max_changed_fields,
    )


def parse_diff_from_config(config: Config):
    with Path(config.diff_json_path).open(encoding="utf-8") as handle:
        document = json.load(handle)
    return parse_diff(
        document,
        collapse_iam_policies=config.collapse_iam_policies,
        collapse_assets=config.collapse_assets,
    )


def append_outputs(config: Config, markdown: str) -> None:
    if config.github_step_summary:
        append_file(Path(config.github_step_summary), markdown)
    else:
        sys.stdout.write(markdown)

    if config.summary_output_path:
        append_file(Path(config.summary_output_path), markdown)


def append_file(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        append_markdown(handle, markdown)


def append_markdown(handle: TextIO, markdown: str) -> None:
    handle.write(markdown)
    if not markdown.endswith("\n"):
        handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
