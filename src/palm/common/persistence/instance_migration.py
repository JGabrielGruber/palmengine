"""Instance definition migration — apply revision rules to durable instances."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.exceptions import DefinitionNotFoundError, InstanceMigrationError, InstanceNotFoundError
from palm.common.persistence.definition_migration import MigrationContext, resolve_migration_rule
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.common.persistence.instance_migration_metadata import MIGRATION_METADATA_KEYS
from palm.instances import ProcessInstance

if TYPE_CHECKING:
    from palm.common.managers.instance_manager import InstanceManager


def request_instance_migration(instance: ProcessInstance, target_revision: int) -> None:
    """Record pending migration intent on instance metadata."""
    current = _instance_revision(instance)
    if target_revision <= current:
        raise InstanceMigrationError(
            instance.instance_id,
            f"target revision {target_revision} is not ahead of current {current}",
        )
    instance.metadata["migration_status"] = "pending"
    instance.metadata["migration_target_revision"] = target_revision
    instance.metadata["migration_from_revision"] = current
    instance.metadata["migration_blockers"] = []


def migrate_instance(
    repository: DefinitionRepository,
    instance_manager: InstanceManager,
    *,
    instance_id: str,
    target_revision: int,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Dry-run or apply a definition migration for a durable instance."""
    try:
        instance = instance_manager.get(instance_id)
    except InstanceNotFoundError as exc:
        raise exc

    flow_id = _instance_flow_id(instance)
    if not flow_id:
        raise InstanceMigrationError(instance_id, "instance has no flow_id")

    from_revision = _instance_revision(instance)
    if target_revision <= from_revision:
        raise InstanceMigrationError(
            instance_id,
            f"target revision {target_revision} is not ahead of current {from_revision}",
        )

    try:
        target_flow = repository.get_flow(flow_id, revision=target_revision)
    except DefinitionNotFoundError as exc:
        raise InstanceMigrationError(
            instance_id,
            f"target revision {target_revision} not found for flow {flow_id!r}",
        ) from exc

    rule = resolve_migration_rule(flow_id, from_revision, target_revision)
    if rule is None:
        result = _migration_result(
            instance_id=instance_id,
            flow_id=flow_id,
            from_revision=from_revision,
            target_revision=target_revision,
            dry_run=dry_run,
            applied=False,
            migration_status="failed",
            blockers=["no migration rule registered"],
        )
        if not dry_run:
            _set_failed_metadata(instance, target_revision, from_revision, result["blockers"])
            instance_manager.save(instance)
        return result

    ctx = MigrationContext(
        flow_id=flow_id,
        from_revision=from_revision,
        to_revision=target_revision,
        instance_id=instance_id,
        state=dict(instance.state_snapshot),
    )
    ok, blockers = rule.can_migrate(ctx)
    if not ok:
        result = _migration_result(
            instance_id=instance_id,
            flow_id=flow_id,
            from_revision=from_revision,
            target_revision=target_revision,
            dry_run=dry_run,
            applied=False,
            migration_status="failed",
            blockers=list(blockers),
        )
        if not dry_run:
            _set_failed_metadata(instance, target_revision, from_revision, result["blockers"])
            instance_manager.save(instance)
        return result

    migrated_state = rule.migrate_state(ctx)
    if dry_run:
        return _migration_result(
            instance_id=instance_id,
            flow_id=flow_id,
            from_revision=from_revision,
            target_revision=target_revision,
            dry_run=True,
            applied=False,
            migration_status="pending",
            blockers=[],
            preview_state=migrated_state,
        )

    request_instance_migration(instance, target_revision)
    instance.metadata["migration_status"] = "running"
    instance_manager.save(instance)

    instance.state_snapshot = dict(migrated_state)
    instance.flow_revision = target_revision
    instance.flow_definition = target_flow.to_dict()
    _clear_migration_metadata(instance)
    saved = instance_manager.save(instance)

    return _migration_result(
        instance_id=saved.instance_id,
        flow_id=flow_id,
        from_revision=from_revision,
        target_revision=target_revision,
        dry_run=False,
        applied=True,
        migration_status="succeeded",
        blockers=[],
        state_snapshot=dict(saved.state_snapshot),
    )


def _set_failed_metadata(
    instance: ProcessInstance,
    target_revision: int,
    from_revision: int,
    blockers: list[str],
) -> None:
    instance.metadata["migration_status"] = "failed"
    instance.metadata["migration_target_revision"] = target_revision
    instance.metadata["migration_from_revision"] = from_revision
    instance.metadata["migration_blockers"] = list(blockers)


def _clear_migration_metadata(instance: ProcessInstance) -> None:
    for key in MIGRATION_METADATA_KEYS:
        instance.metadata.pop(key, None)


def _instance_flow_id(instance: ProcessInstance) -> str | None:
    return instance.flow_id or instance.flow_name


def _instance_revision(instance: ProcessInstance) -> int:
    if instance.flow_revision is not None:
        return instance.flow_revision
    revision = instance.flow_definition.get("revision")
    if revision is not None:
        return int(revision)
    return 1


def _migration_result(
    *,
    instance_id: str,
    flow_id: str,
    from_revision: int,
    target_revision: int,
    dry_run: bool,
    applied: bool,
    migration_status: str,
    blockers: list[str],
    preview_state: dict[str, Any] | None = None,
    state_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "instance_id": instance_id,
        "flow_id": flow_id,
        "from_revision": from_revision,
        "target_revision": target_revision,
        "dry_run": dry_run,
        "applied": applied,
        "migration_status": migration_status,
        "blockers": blockers,
    }
    if preview_state is not None:
        payload["preview_state"] = preview_state
    if state_snapshot is not None:
        payload["state_snapshot"] = state_snapshot
    return payload


__all__ = [
    "MIGRATION_METADATA_KEYS",
    "migrate_instance",
    "request_instance_migration",
]