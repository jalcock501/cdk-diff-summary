"""Runtime configuration for the cdk-diff-summary action."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ

DEFAULT_TITLE = "CDK diff summary"
TRUE_VALUES = {"1", "true", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "no", "n", "off", ""}


@dataclass(frozen=True)
class Config:
    diff_json_path: str
    summary_title: str
    max_changed_fields: int
    collapse_iam_policies: bool
    collapse_assets: bool
    fail_on_remove: bool
    fail_on_replace: bool
    summary_output_path: str
    github_step_summary: str


def parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"expected a boolean value, got {value!r}")


def parse_max_changed_fields(value: str | None) -> int:
    raw_value = "8" if value is None or value.strip() == "" else value.strip()
    try:
        parsed = int(raw_value)
    except ValueError as exc:
        message = "MAX_CHANGED_FIELDS must be an integer greater than or equal to 1"
        raise ValueError(message) from exc
    if parsed < 1:
        raise ValueError("MAX_CHANGED_FIELDS must be greater than or equal to 1")
    return parsed


def load_config() -> Config:
    diff_json_path = environ.get("DIFF_JSON_PATH", "").strip()
    if not diff_json_path:
        raise ValueError("DIFF_JSON_PATH is required")

    return Config(
        diff_json_path=diff_json_path,
        summary_title=(
            DEFAULT_TITLE if environ.get("SUMMARY_TITLE") is None else environ["SUMMARY_TITLE"]
        ),
        max_changed_fields=parse_max_changed_fields(environ.get("MAX_CHANGED_FIELDS")),
        collapse_iam_policies=parse_bool(environ.get("COLLAPSE_IAM_POLICIES"), default=True),
        collapse_assets=parse_bool(environ.get("COLLAPSE_ASSETS"), default=True),
        fail_on_remove=parse_bool(environ.get("FAIL_ON_REMOVE"), default=False),
        fail_on_replace=parse_bool(environ.get("FAIL_ON_REPLACE"), default=False),
        summary_output_path=environ.get("SUMMARY_OUTPUT_PATH", "").strip(),
        github_step_summary="",
    )
