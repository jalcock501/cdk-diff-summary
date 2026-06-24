from cdk_diff_summary.diff import parse_diff


def test_parse_small_change_set_json(small_change_set: dict) -> None:
    summary = parse_diff(small_change_set)

    assert summary.stack_changes == 1
    assert len(summary.resources) == 3
    assert summary.adds == 1
    assert summary.modifies == 2
    assert summary.removes == 0
    assert summary.replacements == 0


def test_grouping_adds_modifies_removes_replacements(large_change_set: dict) -> None:
    summary = parse_diff(large_change_set)

    assert summary.stack_changes == 6
    assert len(summary.resources) == 20
    assert summary.adds == 7
    assert summary.modifies == 10
    assert summary.removes == 2
    assert summary.replacements == 1
    assert len(summary.security_group_changes) == 3


def test_changed_field_paths_are_derived_without_values(small_change_set: dict) -> None:
    summary = parse_diff(small_change_set)
    distribution = next(
        resource
        for resource in summary.resources
        if resource.logical_id == "WebDistributionCFDistributionA1D23A76"
    )

    assert distribution.changed_fields == (
        "DefaultCacheBehavior.DefaultTTL",
        "DefaultCacheBehavior.MaxTTL",
        "DefaultCacheBehavior.ResponseHeadersPolicyId",
    )
    assert "86400" not in distribution.changed_fields
    assert "31536000" not in distribution.changed_fields


def test_iam_policy_collapse_in_change_set(medium_change_set: dict) -> None:
    summary = parse_diff(medium_change_set, collapse_iam_policies=True)
    policy = next(
        resource
        for resource in summary.resources
        if resource.logical_id == "OrderApiFunctionServiceRoleDefaultPolicy6DAA92CE"
    )

    assert policy.changed_fields == ("PolicyDocument",)


def test_asset_fields_from_change_set_do_not_print_hash_values(medium_change_set: dict) -> None:
    summary = parse_diff(medium_change_set, collapse_assets=True)
    function = next(
        resource
        for resource in summary.resources
        if resource.logical_id == "OrderApiFunction7B9D343F"
    )

    assert function.changed_fields == (
        "Code.S3Key",
        "Environment",
        "MemorySize",
        "Runtime",
        "Timeout",
    )
    assert "asset.2b9a62d4.zip" not in function.changed_fields
    assert "asset.a77e4210.zip" not in function.changed_fields


def test_security_group_changes_are_inferred_from_change_set(large_change_set: dict) -> None:
    summary = parse_diff(large_change_set)

    assert [change.security_group for change in summary.security_group_changes] == [
        "AppSecurityGroupF3F49A23",
        "AlbSecurityGroupIngress80CBE42865",
        "DatabaseSecurityGroupIngress3D621F2E",
    ]
    assert [change.direction for change in summary.security_group_changes] == [
        "ingress",
        "ingress",
        "ingress",
    ]
    assert [change.action for change in summary.security_group_changes] == [
        "modify",
        "remove",
        "modify",
    ]
    assert summary.security_group_changes[1].protocol == "changed"
    assert summary.security_group_changes[1].port == "changed"


def test_parse_cloudformation_change_set_json() -> None:
    document = {
        "StackName": "PaymentsStack",
        "ChangeSetName": "cdk-diff-summary-smoke",
        "Changes": [
            {
                "Type": "Resource",
                "ResourceChange": {
                    "Action": "Add",
                    "LogicalResourceId": "Queue",
                    "ResourceType": "AWS::SQS::Queue",
                    "Replacement": "False",
                    "Details": [],
                },
            },
            {
                "Type": "Resource",
                "ResourceChange": {
                    "Action": "Modify",
                    "LogicalResourceId": "Worker",
                    "ResourceType": "AWS::Lambda::Function",
                    "Replacement": "Conditional",
                    "Details": [
                        {
                            "Target": {
                                "Attribute": "Properties",
                                "Name": "Runtime",
                                "RequiresRecreation": "Never",
                            },
                            "Evaluation": "Static",
                            "ChangeSource": "DirectModification",
                        },
                        {
                            "Target": {
                                "Attribute": "Properties",
                                "Name": "MemorySize",
                                "RequiresRecreation": "Conditionally",
                            },
                            "Evaluation": "Dynamic",
                            "ChangeSource": "DirectModification",
                        },
                    ],
                },
            },
            {
                "Type": "Resource",
                "ResourceChange": {
                    "Action": "Remove",
                    "LogicalResourceId": "OldTable",
                    "ResourceType": "AWS::DynamoDB::Table",
                    "Replacement": "False",
                    "Details": [],
                },
            },
        ],
    }

    summary = parse_diff(document)

    assert summary.stack_changes == 1
    assert summary.adds == 1
    assert summary.removes == 1
    assert summary.replacements == 1
    worker = next(resource for resource in summary.resources if resource.logical_id == "Worker")
    assert worker.stack == "PaymentsStack"
    assert worker.action == "replace"
    assert worker.resource_type == "AWS::Lambda::Function"
    assert worker.changed_fields == ("Runtime", "MemorySize")


def test_cloudformation_change_set_security_group_rules_are_summarized() -> None:
    document = {
        "StackName": "NetworkStack",
        "Changes": [
            {
                "Type": "Resource",
                "ResourceChange": {
                    "Action": "Modify",
                    "LogicalResourceId": "AppIngressFromAlb",
                    "ResourceType": "AWS::EC2::SecurityGroupIngress",
                    "Replacement": "False",
                    "Details": [
                        {"Target": {"Attribute": "Properties", "Name": "IpProtocol"}},
                        {"Target": {"Attribute": "Properties", "Name": "FromPort"}},
                        {"Target": {"Attribute": "Properties", "Name": "ToPort"}},
                        {"Target": {"Attribute": "Properties", "Name": "CidrIp"}},
                    ],
                },
            },
            {
                "Type": "Resource",
                "ResourceChange": {
                    "Action": "Remove",
                    "LogicalResourceId": "LegacySmtpEgress",
                    "ResourceType": "AWS::EC2::SecurityGroupEgress",
                    "Replacement": "False",
                    "Details": [],
                },
            },
        ],
    }

    summary = parse_diff(document)

    assert len(summary.security_group_changes) == 2
    assert summary.security_group_changes[0].stack == "NetworkStack"
    assert summary.security_group_changes[0].security_group == "AppIngressFromAlb"
    assert summary.security_group_changes[0].direction == "ingress"
    assert summary.security_group_changes[0].protocol == "changed"
    assert summary.security_group_changes[0].port == "changed"
    assert summary.security_group_changes[0].action == "modify"
    assert summary.security_group_changes[1].direction == "egress"
    assert summary.security_group_changes[1].action == "remove"
