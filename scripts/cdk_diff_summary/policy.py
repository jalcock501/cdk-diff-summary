"""Noise reduction helpers for changed field paths."""

from __future__ import annotations

import re

IAM_POLICY_ROOTS = (
    "PolicyDocument",
    "AssumeRolePolicyDocument",
    "Policies[].PolicyDocument",
)

ASSET_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"assetparameters.*artifacthash",
        r"assethash",
        r"sourcehash",
        r"codehash",
        r"imageuri",
        r"imageasset",
        r"docker.*asset",
        r"s3(object)?key",
        r"sourceobjectkey",
        r"metadata.*aws:cdk:path",
        r"metadata.*asset",
        r"code\.s3key",
        r"code\.zipfile",
    )
)


def normalize_path(path: str) -> str:
    normalized = path.replace("/", ".")
    normalized = re.sub(r"\[[0-9]+\]", "[]", normalized)
    normalized = re.sub(r"\.+", ".", normalized)
    return normalized.strip(".")


def collapse_iam_policy_path(path: str) -> str:
    normalized = normalize_path(path)
    if normalized.startswith("PolicyDocument."):
        return "PolicyDocument"
    if normalized == "PolicyDocument":
        return "PolicyDocument"
    if normalized.startswith("AssumeRolePolicyDocument."):
        return "AssumeRolePolicyDocument"
    if normalized == "AssumeRolePolicyDocument":
        return "AssumeRolePolicyDocument"
    if ".PolicyDocument." in normalized:
        return normalized.split(".PolicyDocument.", maxsplit=1)[0] + ".PolicyDocument"
    return path


def collapse_asset_path(path: str) -> str | None:
    normalized = normalize_path(path)
    compact = re.sub(r"[^a-z0-9:]", "", normalized.lower())
    for pattern in ASSET_PATTERNS:
        if pattern.search(compact) or pattern.search(normalized):
            return asset_bucket(normalized)
    return path


def asset_bucket(path: str) -> str | None:
    lowered = path.lower()
    if "metadata" in lowered:
        return "Metadata.Asset"
    if "s3" in lowered or "objectkey" in lowered:
        return "Code.S3Key"
    if "image" in lowered or "docker" in lowered:
        return "Image.Asset"
    if "hash" in lowered or "assetparameters" in lowered:
        return "Asset.Hash"
    if "zipfile" in lowered:
        return "Code.ZipFile"
    return None


def collapse_paths(
    paths: list[str],
    *,
    collapse_iam_policies: bool,
    collapse_assets: bool,
) -> list[str]:
    collapsed: list[str] = []
    seen: set[str] = set()
    for path in paths:
        next_path = path
        if collapse_iam_policies:
            next_path = collapse_iam_policy_path(next_path)
        if collapse_assets:
            asset_path = collapse_asset_path(next_path)
            if asset_path is None:
                continue
            next_path = asset_path
        if next_path not in seen:
            seen.add(next_path)
            collapsed.append(next_path)
    return collapsed
