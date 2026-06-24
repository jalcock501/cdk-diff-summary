from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "example_cdk_changesets_json"
if not EXAMPLE_DIR.exists():
    EXAMPLE_DIR = ROOT.parent / "example_cdk_changesets_json"


@pytest.fixture
def small_change_set() -> dict:
    return load_fixture("small-webstack-cdk-diff.json")


@pytest.fixture
def medium_change_set() -> dict:
    return load_fixture("medium-apistack-cdk-diff.json")


@pytest.fixture
def large_change_set() -> dict:
    return load_fixture("large-prod-multistack-cdk-diff.json")


def load_fixture(name: str) -> dict:
    with (EXAMPLE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)
