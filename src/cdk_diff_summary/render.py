"""Render compact Markdown summaries."""

from __future__ import annotations

from collections.abc import Iterable

from cdk_diff_summary.diff import DiffSummary, ResourceChange, SecurityGroupChange

GROUP_TITLES = (
    ("replacements", "Replacements"),
    ("removes", "Removes"),
    ("adds", "Adds"),
    ("modifies", "Modifies"),
    ("other", "Other changes"),
)


def render_summary(summary: DiffSummary, *, title: str, max_changed_fields: int) -> str:
    changes_shown = len(summary.resources) + len(summary.security_group_changes)
    lines = []
    if title.strip():
        lines.extend([f"## {escape_markdown(title)}", ""])

    lines.extend(
        [
            "| Metric | Count |",
            "| --- | ---: |",
            f"| Stack changes | {summary.stack_changes} |",
            f"| Resource changes | {len(summary.resources)} |",
            f"| Adds | {summary.adds} |",
            f"| Modifies | {summary.modifies} |",
            f"| Removes | {summary.removes} |",
            f"| Replacements | {summary.replacements} |",
            f"| Security group changes | {len(summary.security_group_changes)} |",
            f"| Changes shown below | {changes_shown} |",
            "",
        ]
    )

    for group, group_title in GROUP_TITLES:
        resources = [resource for resource in summary.resources if resource.group == group]
        if not resources:
            continue
        lines.extend(render_group(group_title, resources, max_changed_fields=max_changed_fields))
        lines.append("")

    if summary.security_group_changes:
        lines.extend(render_security_group_changes(summary.security_group_changes))
        lines.append("")

    if not summary.resources and not summary.security_group_changes:
        lines.append("No resource changes found in the input JSON.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_group(
    title: str,
    resources: Iterable[ResourceChange],
    *,
    max_changed_fields: int,
) -> list[str]:
    lines = [
        f"### {title}",
        "",
        "| Stack | Logical ID | Action | Resource type | Changed fields |",
        "| --- | --- | --- | --- | --- |",
    ]
    for resource in resources:
        fields = format_changed_fields(
            resource.changed_fields,
            max_changed_fields=max_changed_fields,
        )
        lines.append(
            "| "
            + " | ".join(
                escape_table_cell(value)
                for value in (
                    resource.stack,
                    resource.logical_id,
                    resource.action,
                    resource.resource_type,
                    fields,
                )
            )
            + " |"
        )
    return lines


def render_security_group_changes(
    changes: Iterable[SecurityGroupChange],
) -> list[str]:
    lines = [
        "### Security group changes",
        "",
        "| Stack | Security group | Direction | Protocol | Port | Action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for change in changes:
        lines.append(
            "| "
            + " | ".join(
                escape_table_cell(value)
                for value in (
                    change.stack,
                    change.security_group,
                    change.direction,
                    change.protocol,
                    change.port,
                    change.action,
                )
            )
            + " |"
        )
    return lines


def format_changed_fields(fields: tuple[str, ...], *, max_changed_fields: int) -> str:
    if not fields:
        return "_n/a_"
    visible = list(fields[:max_changed_fields])
    if len(fields) > max_changed_fields:
        visible.append("...")
    return "`" + "`, `".join(visible) + "`"


def escape_table_cell(value: str) -> str:
    return escape_markdown(value).replace("|", "\\|").replace("\n", "<br>")


def escape_markdown(value: str) -> str:
    return str(value).replace("\r", "")
