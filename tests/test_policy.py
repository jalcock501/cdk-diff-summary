from cdk_diff_summary.policy import collapse_paths


def test_iam_policy_document_collapses_to_single_field() -> None:
    fields = collapse_paths(
        [
            "PolicyDocument.Statement[0].Action[2]",
            "PolicyDocument.Statement[0].Action[3]",
            "PolicyDocument.Statement[0].Resource",
        ],
        collapse_iam_policies=True,
        collapse_assets=False,
    )

    assert fields == ["PolicyDocument"]


def test_asset_hash_fields_are_collapsed_or_suppressed() -> None:
    fields = collapse_paths(
        [
            "Code.S3Key",
            "Metadata.aws:cdk:path",
            "AssetParameters0deadbeefArtifactHash",
            "Runtime",
        ],
        collapse_iam_policies=False,
        collapse_assets=True,
    )

    assert fields == ["Code.S3Key", "Metadata.Asset", "Asset.Hash", "Runtime"]
