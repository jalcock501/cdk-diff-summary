from cdk_diff_summary.diff import parse_diff
from cdk_diff_summary.render import format_changed_fields, render_summary


def test_changed_field_truncation() -> None:
    fields = ("A", "B", "C")

    assert format_changed_fields(fields, max_changed_fields=2) == "`A`, `B`, `...`"


def test_render_full_markdown_summary(large_change_set: dict) -> None:
    markdown = render_summary(
        parse_diff(large_change_set),
        title="CDK diff summary",
        max_changed_fields=2,
    )

    assert "## CDK diff summary" in markdown
    assert "| Stack changes | 6 |" in markdown
    assert "| Resource changes | 20 |" in markdown
    assert "### Replacements" in markdown
    assert "### Removes" in markdown
    assert "### Adds" in markdown
    assert "### Modifies" in markdown
    assert "### Security group changes" in markdown
    assert "| Security group changes | 3 |" in markdown
    assert "0.0.0.0/0" not in markdown
    assert "arn:aws:acm" not in markdown


def test_render_security_group_changes_without_before_after_values(large_change_set: dict) -> None:
    markdown = render_summary(
        parse_diff(large_change_set),
        title="CDK diff summary",
        max_changed_fields=2,
    )

    assert "### Security group changes" in markdown
    assert (
        "| SampleApp-Prod-PlatformStack | AlbSecurityGroupIngress80CBE42865 | "
        "ingress | changed | changed | remove |"
    ) in markdown
    assert "0.0.0.0/0" not in markdown
    assert "10.0.4.0/24" not in markdown
