from cdk_diff_summary.diff import parse_diff
from cdk_diff_summary.render import format_changed_fields, render_summary


def test_changed_field_truncation() -> None:
    fields = ("A", "B", "C")

    assert format_changed_fields(fields, max_changed_fields=2) == "`A`, `B`, `...`"


def test_render_full_markdown_summary(messy_diff: dict) -> None:
    markdown = render_summary(
        parse_diff(messy_diff),
        title="CDK diff summary",
        max_changed_fields=2,
    )

    assert "## CDK diff summary" in markdown
    assert "| Stack changes | 1 |" in markdown
    assert "| Resource changes | 8 |" in markdown
    assert "### Replacements" in markdown
    assert "### Removes" in markdown
    assert "### Adds" in markdown
    assert "### Modifies" in markdown
    assert "oldValue" not in markdown
    assert "newValue" not in markdown
