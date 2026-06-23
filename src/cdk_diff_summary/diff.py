"""Parse CDK diff JSON into a small internal model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cdk_diff_summary.policy import collapse_paths

ADD_ACTIONS = {"add", "create", "+", "addition"}
REMOVE_ACTIONS = {"delete", "remove", "destroy", "-", "deletion"}
MODIFY_ACTIONS = {"modify", "update", "change", "~"}
REPLACE_ACTIONS = {"replace", "replacement", "+/-", "-/+"}


@dataclass(frozen=True)
class ResourceChange:
    stack: str
    logical_id: str
    action: str
    resource_type: str
    changed_fields: tuple[str, ...]
    replacement: bool = False

    @property
    def group(self) -> str:
        if self.replacement:
            return "replacements"
        normalized = normalize_action(self.action)
        if normalized == "remove":
            return "removes"
        if normalized == "add":
            return "adds"
        if normalized == "modify":
            return "modifies"
        return "other"


@dataclass(frozen=True)
class SecurityGroupChange:
    stack: str
    security_group: str
    direction: str
    protocol: str
    port: str
    action: str


@dataclass(frozen=True)
class DiffSummary:
    stack_changes: int
    resources: tuple[ResourceChange, ...]
    security_group_changes: tuple[SecurityGroupChange, ...] = ()

    @property
    def adds(self) -> int:
        return sum(1 for resource in self.resources if resource.group == "adds")

    @property
    def modifies(self) -> int:
        return sum(1 for resource in self.resources if resource.group == "modifies")

    @property
    def removes(self) -> int:
        return sum(1 for resource in self.resources if resource.group == "removes")

    @property
    def replacements(self) -> int:
        return sum(1 for resource in self.resources if resource.group == "replacements")


def parse_diff(
    document: Any,
    *,
    collapse_iam_policies: bool = True,
    collapse_assets: bool = True,
) -> DiffSummary:
    stacks = extract_stacks(document)
    resources: list[ResourceChange] = []
    security_group_changes: list[SecurityGroupChange] = []
    stack_changes = 0

    for stack in stacks:
        stack_name = str(first_present(stack, "stackName", "name", "id", "stack") or "Unknown")
        stack_resources = extract_resources(stack)
        stack_security_group_changes = extract_security_group_changes(stack)
        has_differences = bool(stack.get("hasDifferences")) if isinstance(stack, dict) else False
        if stack_resources or stack_security_group_changes or has_differences:
            stack_changes += 1
        for resource in stack_resources:
            resources.append(
                parse_resource(
                    resource,
                    stack_name=stack_name,
                    collapse_iam_policies=collapse_iam_policies,
                    collapse_assets=collapse_assets,
                )
            )
        for security_group_change in stack_security_group_changes:
            security_group_changes.append(
                parse_security_group_change(
                    security_group_change,
                    stack_name=stack_name,
                )
            )

    return DiffSummary(
        stack_changes=stack_changes,
        resources=tuple(resources),
        security_group_changes=tuple(security_group_changes),
    )


def extract_stacks(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, dict):
        stacks = first_present(document, "stacks", "Stacks", "stackDiffs", "differences")
        if isinstance(stacks, list):
            return [stack for stack in stacks if isinstance(stack, dict)]
        if isinstance(stacks, dict):
            return [
                dict({"stackName": name}, **value)
                for name, value in stacks.items()
                if isinstance(value, dict)
            ]
        if has_resource_collection(document):
            return [document]
    if isinstance(document, list):
        return [stack for stack in document if isinstance(stack, dict)]
    return []


def extract_resources(stack: dict[str, Any]) -> list[dict[str, Any]]:
    raw_resources = first_present(
        stack,
        "resources",
        "resourceChanges",
        "ResourceChanges",
        "changes",
    )
    if isinstance(raw_resources, list):
        return [resource for resource in raw_resources if isinstance(resource, dict)]
    if isinstance(raw_resources, dict):
        resources = []
        for logical_id, resource in raw_resources.items():
            if isinstance(resource, dict):
                resources.append(dict({"logicalId": logical_id}, **resource))
        return resources
    return []


def extract_security_group_changes(stack: dict[str, Any]) -> list[dict[str, Any]]:
    raw_changes = first_present(
        stack,
        "securityGroupChanges",
        "securityGroups",
        "SecurityGroupChanges",
    )
    if isinstance(raw_changes, list):
        return [change for change in raw_changes if isinstance(change, dict)]
    if isinstance(raw_changes, dict):
        changes = []
        for security_group, change in raw_changes.items():
            if isinstance(change, dict):
                changes.append(dict({"securityGroup": security_group}, **change))
        return changes
    return []


def parse_resource(
    resource: dict[str, Any],
    *,
    stack_name: str,
    collapse_iam_policies: bool,
    collapse_assets: bool,
) -> ResourceChange:
    logical_id = str(
        first_present(resource, "logicalId", "logicalResourceId", "id", "name") or "Unknown"
    )
    resource_type = str(first_present(resource, "resourceType", "type", "resourceTypeName") or "")
    action = normalize_action(
        str(first_present(resource, "action", "changeType", "operation") or "other")
    )
    changed_fields = extract_changed_fields(resource)
    replacement = is_replacement(resource, changed_fields)
    if replacement:
        action = "replace"
    collapsed_fields = collapse_paths(
        changed_fields,
        collapse_iam_policies=collapse_iam_policies,
        collapse_assets=collapse_assets,
    )

    return ResourceChange(
        stack=stack_name,
        logical_id=logical_id,
        action=action,
        resource_type=resource_type,
        changed_fields=tuple(collapsed_fields),
        replacement=replacement,
    )


def parse_security_group_change(
    change: dict[str, Any],
    *,
    stack_name: str,
) -> SecurityGroupChange:
    security_group = first_present(
        change,
        "securityGroup",
        "securityGroupId",
        "groupId",
        "groupName",
        "name",
    )
    direction = first_present(change, "direction", "ruleType", "type")
    protocol = first_present(change, "protocol", "ipProtocol")
    port = first_present(change, "port", "fromPort", "toPort", "ports")
    action = first_present(change, "action", "changeType", "operation")

    return SecurityGroupChange(
        stack=stack_name,
        security_group=str(security_group or "Unknown"),
        direction=str(direction or ""),
        protocol=str(protocol or ""),
        port=format_port(port),
        action=normalize_action(str(action or "other")),
    )


def extract_changed_fields(resource: dict[str, Any]) -> list[str]:
    raw_changes = first_present(
        resource,
        "propertyChanges",
        "propertyDiffs",
        "details",
        "changes",
        "changedFields",
    )
    fields: list[str] = []

    if isinstance(raw_changes, list):
        for change in raw_changes:
            if isinstance(change, str):
                fields.append(change)
            elif isinstance(change, dict):
                field = first_present(change, "path", "propertyPath", "name", "field", "target")
                if field:
                    fields.append(str(field))
    elif isinstance(raw_changes, dict):
        for key, value in raw_changes.items():
            if isinstance(value, dict):
                field = first_present(value, "path", "propertyPath", "name", "field")
                fields.append(str(field or key))
            else:
                fields.append(str(key))

    if not fields:
        field = first_present(resource, "path", "propertyPath")
        if field:
            fields.append(str(field))
    return dedupe(fields)


def is_replacement(resource: dict[str, Any], changed_fields: list[str]) -> bool:
    replacement = first_present(resource, "replacement", "requiresReplacement", "willReplace")
    if isinstance(replacement, bool) and replacement:
        return True
    action = str(first_present(resource, "action", "changeType", "operation") or "").strip().lower()
    if action in REPLACE_ACTIONS:
        return True

    raw_changes = first_present(resource, "propertyChanges", "propertyDiffs", "details", "changes")
    if isinstance(raw_changes, list):
        for change in raw_changes:
            if isinstance(change, dict) and change.get("requiresReplacement") is True:
                return True
    return any(field.lower() == "replacement" for field in changed_fields)


def normalize_action(action: str) -> str:
    normalized = action.strip().lower()
    if normalized in ADD_ACTIONS:
        return "add"
    if normalized in REMOVE_ACTIONS:
        return "remove"
    if normalized in MODIFY_ACTIONS:
        return "modify"
    if normalized in REPLACE_ACTIONS:
        return "replace"
    return normalized or "other"


def first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def format_port(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list | tuple):
        return ", ".join(str(item) for item in value)
    return str(value)


def has_resource_collection(document: dict[str, Any]) -> bool:
    return any(key in document for key in ("resources", "resourceChanges", "ResourceChanges"))


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
