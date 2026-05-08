from cdk_diff_summary.diff import parse_diff


def test_parse_representative_cdk_diff_json(tiny_diff: dict) -> None:
    summary = parse_diff(tiny_diff)

    assert summary.stack_changes == 1
    assert len(summary.resources) == 2
    assert summary.adds == 1
    assert summary.modifies == 1
    assert summary.removes == 0
    assert summary.replacements == 0


def test_grouping_adds_modifies_removes_replacements(messy_diff: dict) -> None:
    summary = parse_diff(messy_diff)

    assert summary.adds == 2
    assert summary.modifies == 2
    assert summary.removes == 1
    assert summary.replacements == 3


def test_changed_field_paths_do_not_include_values(tiny_diff: dict) -> None:
    summary = parse_diff(tiny_diff)
    log_group = next(
        resource for resource in summary.resources if resource.logical_id == "AppLogGroup"
    )

    assert log_group.changed_fields == ("RetentionInDays", "Tags[environment]")
    assert "30" not in log_group.changed_fields


def test_iam_policy_collapse_in_resource() -> None:
    document = {
        "stacks": [
            {
                "stackName": "Stack",
                "resources": [
                    {
                        "logicalId": "Policy",
                        "resourceType": "AWS::IAM::Policy",
                        "action": "modify",
                        "propertyChanges": [
                            {"path": "PolicyDocument.Statement[0].Action[0]"},
                            {"path": "PolicyDocument.Statement[0].Resource"},
                        ],
                    }
                ],
            }
        ]
    }

    summary = parse_diff(document, collapse_iam_policies=True)

    assert summary.resources[0].changed_fields == ("PolicyDocument",)


def test_asset_collapse_in_resource() -> None:
    document = {
        "stacks": [
            {
                "stackName": "Stack",
                "resources": [
                    {
                        "logicalId": "Function",
                        "resourceType": "AWS::Lambda::Function",
                        "action": "modify",
                        "propertyChanges": [
                            {"path": "Code.S3Key"},
                            {"path": "SourceHash"},
                            {"path": "Runtime"},
                        ],
                    }
                ],
            }
        ]
    }

    summary = parse_diff(document, collapse_assets=True)

    assert summary.resources[0].changed_fields == ("Code.S3Key", "Asset.Hash", "Runtime")
