from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "example_cdk_diff_json"
if not EXAMPLE_DIR.exists():
    EXAMPLE_DIR = ROOT.parent / "example_cdk_diff_json"


@pytest.fixture
def tiny_diff() -> dict:
    return load_fixture("cdk-diff-json-tiny.json")


@pytest.fixture
def messy_diff() -> dict:
    return load_fixture("cdk-diff-json-messy-edge-cases.json")


def load_fixture(name: str) -> dict:
    with (EXAMPLE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)
