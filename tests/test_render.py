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
    assert "### Security group changes" in markdown
    assert "| Security group changes | 2 |" in markdown
    assert "oldValue" not in markdown
    assert "newValue" not in markdown


def test_render_security_group_changes_without_before_after_values() -> None:
    document = {
        "stacks": [
            {
                "stackName": "NetworkStack",
                "securityGroupChanges": [
                    {
                        "securityGroup": "AppSecurityGroup",
                        "direction": "ingress",
                        "protocol": "tcp",
                        "port": 443,
                        "action": "add",
                        "old": None,
                        "new": "10.0.0.0/16",
                    },
                    {
                        "securityGroup": "DatabaseSecurityGroup",
                        "direction": "ingress",
                        "protocol": "tcp",
                        "port": 5432,
                        "action": "modify",
                        "old": "10.0.0.0/16",
                        "new": "10.1.0.0/16",
                    },
                    {
                        "securityGroup": "LegacySecurityGroup",
                        "direction": "egress",
                        "protocol": "tcp",
                        "port": 25,
                        "action": "delete",
                        "old": "0.0.0.0/0",
                        "new": None,
                    },
                ],
            }
        ]
    }

    markdown = render_summary(
        parse_diff(document),
        title="CDK diff summary",
        max_changed_fields=2,
    )

    assert "### Security group changes" in markdown
    assert "| NetworkStack | AppSecurityGroup | ingress | tcp | 443 | add |" in markdown
    assert "| NetworkStack | DatabaseSecurityGroup | ingress | tcp | 5432 | modify |" in markdown
    assert "| NetworkStack | LegacySecurityGroup | egress | tcp | 25 | remove |" in markdown
    assert "10.0.0.0/16" not in markdown
    assert "10.1.0.0/16" not in markdown
    assert "0.0.0.0/0" not in markdown
    assert "old" not in markdown
    assert "new" not in markdown
