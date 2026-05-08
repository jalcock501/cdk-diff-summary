from __future__ import annotations

import json
from pathlib import Path

from cdk_diff_summary import cli


def write_diff(path: Path, *, action: str = "modify", replacement: bool = False) -> None:
    path.write_text(
        json.dumps(
            {
                "stacks": [
                    {
                        "stackName": "Stack",
                        "resources": [
                            {
                                "logicalId": "Thing",
                                "resourceType": "Custom::Thing",
                                "action": action,
                                "replacement": replacement,
                                "propertyChanges": [{"path": "Name"}],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_appends_to_github_step_summary(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    summary_path = tmp_path / "summary.md"
    write_diff(diff_path)
    monkeypatch.setenv("DIFF_JSON_PATH", str(diff_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))

    assert cli.main() == 0
    assert "## CDK diff summary" in summary_path.read_text(encoding="utf-8")


def test_optional_summary_output_path(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    step_summary_path = tmp_path / "step.md"
    output_path = tmp_path / "out.md"
    write_diff(diff_path)
    monkeypatch.setenv("DIFF_JSON_PATH", str(diff_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(step_summary_path))
    monkeypatch.setenv("SUMMARY_OUTPUT_PATH", str(output_path))

    assert cli.main() == 0
    assert output_path.read_text(encoding="utf-8") == step_summary_path.read_text(encoding="utf-8")


def test_fail_on_remove_writes_summary_then_fails(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    summary_path = tmp_path / "summary.md"
    write_diff(diff_path, action="delete")
    monkeypatch.setenv("DIFF_JSON_PATH", str(diff_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("FAIL_ON_REMOVE", "true")

    assert cli.main() == 2
    assert "### Removes" in summary_path.read_text(encoding="utf-8")


def test_fail_on_replace_writes_summary_then_fails(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    summary_path = tmp_path / "summary.md"
    write_diff(diff_path, replacement=True)
    monkeypatch.setenv("DIFF_JSON_PATH", str(diff_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("FAIL_ON_REPLACE", "true")

    assert cli.main() == 3
    assert "### Replacements" in summary_path.read_text(encoding="utf-8")


def test_invalid_max_changed_fields(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    summary_path = tmp_path / "summary.md"
    write_diff(diff_path)
    monkeypatch.setenv("DIFF_JSON_PATH", str(diff_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("MAX_CHANGED_FIELDS", "0")

    assert cli.main() == 1
    assert not summary_path.exists()
