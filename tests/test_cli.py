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


def test_prints_to_stdout_when_no_output_paths(monkeypatch, capsys, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    write_diff(diff_path)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("SUMMARY_OUTPUT_PATH", raising=False)

    assert cli.main([str(diff_path)]) == 0

    output = capsys.readouterr().out
    assert "## CDK diff summary" in output
    assert "Thing" in output


def test_appends_to_output_path(tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    output_path = tmp_path / "summary.md"
    write_diff(diff_path)

    assert cli.main([str(diff_path), "--output", str(output_path)]) == 0
    assert "## CDK diff summary" in output_path.read_text(encoding="utf-8")


def test_appends_to_github_step_summary(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    summary_path = tmp_path / "summary.md"
    write_diff(diff_path)
    monkeypatch.setenv("DIFF_JSON_PATH", str(diff_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))

    assert cli.main([]) == 0
    assert "## CDK diff summary" in summary_path.read_text(encoding="utf-8")


def test_optional_summary_output_path(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    step_summary_path = tmp_path / "step.md"
    output_path = tmp_path / "out.md"
    write_diff(diff_path)
    monkeypatch.setenv("DIFF_JSON_PATH", str(diff_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(step_summary_path))
    monkeypatch.setenv("SUMMARY_OUTPUT_PATH", str(output_path))

    assert cli.main([]) == 0
    assert output_path.read_text(encoding="utf-8") == step_summary_path.read_text(encoding="utf-8")


def test_cli_arguments_override_environment(monkeypatch, tmp_path: Path) -> None:
    env_diff_path = tmp_path / "env-diff.json"
    cli_diff_path = tmp_path / "cli-diff.json"
    output_path = tmp_path / "summary.md"
    write_diff(env_diff_path)
    write_diff(cli_diff_path, action="add")
    monkeypatch.setenv("DIFF_JSON_PATH", str(env_diff_path))

    assert cli.main([str(cli_diff_path), "--title", "CLI title", "--output", str(output_path)]) == 0

    output = output_path.read_text(encoding="utf-8")
    assert "## CLI title" in output
    assert "### Adds" in output


def test_fail_on_remove_writes_summary_then_fails(tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    output_path = tmp_path / "summary.md"
    write_diff(diff_path, action="delete")

    assert cli.main([str(diff_path), "--output", str(output_path), "--fail-on-remove"]) == 2
    assert "### Removes" in output_path.read_text(encoding="utf-8")


def test_no_fail_on_remove_overrides_environment(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    output_path = tmp_path / "summary.md"
    write_diff(diff_path, action="delete")
    monkeypatch.setenv("FAIL_ON_REMOVE", "true")

    assert cli.main([str(diff_path), "--output", str(output_path), "--no-fail-on-remove"]) == 0
    assert "### Removes" in output_path.read_text(encoding="utf-8")


def test_fail_on_replace_writes_summary_then_fails(tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    output_path = tmp_path / "summary.md"
    write_diff(diff_path, replacement=True)

    assert cli.main([str(diff_path), "--output", str(output_path), "--fail-on-replace"]) == 3
    assert "### Replacements" in output_path.read_text(encoding="utf-8")


def test_no_fail_on_replace_overrides_environment(monkeypatch, tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    output_path = tmp_path / "summary.md"
    write_diff(diff_path, replacement=True)
    monkeypatch.setenv("FAIL_ON_REPLACE", "true")

    assert cli.main([str(diff_path), "--output", str(output_path), "--no-fail-on-replace"]) == 0
    assert "### Replacements" in output_path.read_text(encoding="utf-8")


def test_invalid_max_changed_fields(tmp_path: Path) -> None:
    diff_path = tmp_path / "diff.json"
    output_path = tmp_path / "summary.md"
    write_diff(diff_path)

    assert (
        cli.main([str(diff_path), "--output", str(output_path), "--max-changed-fields", "0"])
        == 1
    )
    assert not output_path.exists()
