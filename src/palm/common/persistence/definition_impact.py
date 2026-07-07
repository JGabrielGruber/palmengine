"""Definition revision impact analysis — instances behind catalog latest."""

from __future__ import annotations

from typing import Any

from palm.common.exceptions import DefinitionNotFoundError
from palm.common.persistence.definition_migration import (
    MigrationContext,
    resolve_migration_rule,
)
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.instances import ProcessInstance


def analyze_definition_impact(
    repository: DefinitionRepository,
    instances: list[ProcessInstance],
    *,
    flow_id: str,
    target_revision: int | None = None,
) -> dict[str, Any]:
    """Report instances pinned behind ``target_revision`` (latest by default)."""
    flow = repository.get_flow(flow_id)
    resolved_id = flow.definition_id
    latest = repository.get_latest_revision(resolved_id)
    if latest is None:
        latest = flow.revision or 1
    target = target_revision if target_revision is not None else latest

    matching = [
        instance
        for instance in instances
        if _instance_flow_id(instance) in {resolved_id, flow.name, flow_id}
    ]
    behind_rows: list[dict[str, Any]] = []
    summary = {
        "total": len(matching),
        "behind_latest": 0,
        "compatible": 0,
        "snapshot_only": 0,
        "blocked": 0,
    }

    for instance in matching:
        current = _instance_revision(instance)
        if current >= target:
            continue
        summary["behind_latest"] += 1
        row = _compatibility_row(
            instance,
            flow_id=resolved_id,
            current_revision=current,
            target_revision=target,
        )
        behind_rows.append(row)
        compatibility = str(row["compatibility"])
        if compatibility in summary:
            summary[compatibility] += 1

    return {
        "flow_id": resolved_id,
        "latest_revision": latest,
        "target_revision": target,
        "instances": behind_rows,
        "summary": summary,
    }


def _instance_flow_id(instance: ProcessInstance) -> str | None:
    return instance.flow_id or instance.flow_name


def _instance_revision(instance: ProcessInstance) -> int:
    if instance.flow_revision is not None:
        return instance.flow_revision
    revision = instance.flow_definition.get("revision")
    if revision is not None:
        return int(revision)
    return 1


def _compatibility_row(
    instance: ProcessInstance,
    *,
    flow_id: str,
    current_revision: int,
    target_revision: int,
) -> dict[str, Any]:
    rule = resolve_migration_rule(flow_id, current_revision, target_revision)
    if rule is None:
        return {
            "instance_id": instance.instance_id,
            "current_revision": current_revision,
            "target_revision": target_revision,
            "compatibility": "snapshot_only",
            "compatible": False,
            "blockers": [],
        }

    ctx = MigrationContext(
        flow_id=flow_id,
        from_revision=current_revision,
        to_revision=target_revision,
        instance_id=instance.instance_id,
        state=dict(instance.state_snapshot),
    )
    ok, blockers = rule.can_migrate(ctx)
    if ok:
        return {
            "instance_id": instance.instance_id,
            "current_revision": current_revision,
            "target_revision": target_revision,
            "compatibility": "compatible",
            "compatible": True,
            "blockers": [],
        }
    return {
        "instance_id": instance.instance_id,
        "current_revision": current_revision,
        "target_revision": target_revision,
        "compatibility": "blocked",
        "compatible": False,
        "blockers": list(blockers),
    }


def analyze_definition_impact_or_raise(
    repository: DefinitionRepository,
    instances: list[ProcessInstance],
    *,
    flow_id: str,
    target_revision: int | None = None,
) -> dict[str, Any]:
    """Like :func:`analyze_definition_impact` but raises when ``flow_id`` is unknown."""
    try:
        return analyze_definition_impact(
            repository,
            instances,
            flow_id=flow_id,
            target_revision=target_revision,
        )
    except DefinitionNotFoundError as exc:
        raise exc


__all__ = [
    "analyze_definition_impact",
    "analyze_definition_impact_or_raise",
]