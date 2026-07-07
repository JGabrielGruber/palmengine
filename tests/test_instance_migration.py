"""Tests for instance definition migration execution (0.24.3)."""

from __future__ import annotations

from palm.common.exceptions import InstanceMigrationError, InstanceNotFoundError
from palm.common.managers.instance_manager import InstanceManager
from palm.common.persistence.definition_migration import (
    CallableMigrationRule,
    migration_registry,
    register_migration_rule,
)
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.common.persistence.instance_migration import migrate_instance, request_instance_migration
from palm.common.persistence.instance_repository import InstanceRepository
from palm.core import StorageEngine
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance


def setup_function() -> None:
    migration_registry.clear()


def _repos() -> tuple[DefinitionRepository, InstanceManager]:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    definition_repo = DefinitionRepository(storage)
    instance_repo = InstanceRepository(storage)
    manager = InstanceManager(instance_repo)
    manager.initialize(reconcile_on_startup=False)
    return definition_repo, manager


def _repo_with_revisions() -> DefinitionRepository:
    repo = DefinitionRepository()
    repo.publish_flow_revision(
        FlowDefinition(name="onboard", pattern="wizard", options={"step_count": 1}),
    )
    repo.publish_flow_revision(
        FlowDefinition(name="onboard", pattern="wizard", options={"step_count": 2}),
    )
    return repo


def _instance_at_revision(repo: DefinitionRepository, revision: int) -> ProcessInstance:
    flow = repo.get_flow_by_id("onboard", revision=revision)
    return ProcessInstance(
        instance_id="inst-1",
        job_id="job-1",
        status="WAITING_FOR_INPUT",
        state_snapshot={"answers": {"name": "Ada"}},
        flow_definition=flow.to_dict(),
        pattern="wizard",
        flow_id="onboard",
        flow_revision=revision,
    )


def test_migrate_instance_dry_run_returns_preview() -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="onboard",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (True, []),
            _migrate_state=lambda ctx: {**ctx.state, "migrated": True},
        ),
    )
    definition_repo = _repo_with_revisions()
    instance_repo = InstanceRepository()
    manager = InstanceManager(instance_repo)
    manager.initialize(reconcile_on_startup=False)
    manager.save(_instance_at_revision(definition_repo, 1))

    result = migrate_instance(
        definition_repo,
        manager,
        instance_id="inst-1",
        target_revision=2,
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["applied"] is False
    assert result["preview_state"] == {"answers": {"name": "Ada"}, "migrated": True}
    saved = manager.get("inst-1")
    assert saved.flow_revision == 1
    assert "migrated" not in saved.state_snapshot


def test_migrate_instance_applies_rule_and_bumps_revision() -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="onboard",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (True, []),
            _migrate_state=lambda ctx: {**ctx.state, "migrated": True},
        ),
    )
    definition_repo = _repo_with_revisions()
    instance_repo = InstanceRepository()
    manager = InstanceManager(instance_repo)
    manager.initialize(reconcile_on_startup=False)
    manager.save(_instance_at_revision(definition_repo, 1))

    result = migrate_instance(
        definition_repo,
        manager,
        instance_id="inst-1",
        target_revision=2,
        dry_run=False,
    )

    assert result["applied"] is True
    assert result["migration_status"] == "succeeded"
    saved = manager.get("inst-1")
    assert saved.flow_revision == 2
    assert saved.state_snapshot["migrated"] is True
    assert saved.flow_definition["revision"] == 2
    assert "migration_status" not in saved.metadata


def test_migrate_instance_records_failed_metadata_when_blocked() -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="onboard",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (False, ["unsupported answers"]),
            _migrate_state=lambda ctx: ctx.state,
        ),
    )
    definition_repo = _repo_with_revisions()
    instance_repo = InstanceRepository()
    manager = InstanceManager(instance_repo)
    manager.initialize(reconcile_on_startup=False)
    manager.save(_instance_at_revision(definition_repo, 1))

    result = migrate_instance(
        definition_repo,
        manager,
        instance_id="inst-1",
        target_revision=2,
        dry_run=False,
    )

    assert result["applied"] is False
    assert result["migration_status"] == "failed"
    assert result["blockers"] == ["unsupported answers"]
    saved = manager.get("inst-1")
    assert saved.metadata["migration_status"] == "failed"
    assert saved.metadata["migration_target_revision"] == 2
    assert saved.metadata["migration_from_revision"] == 1
    assert saved.metadata["migration_blockers"] == ["unsupported answers"]
    assert saved.flow_revision == 1


def test_migrate_instance_fails_without_rule() -> None:
    definition_repo = _repo_with_revisions()
    instance_repo = InstanceRepository()
    manager = InstanceManager(instance_repo)
    manager.initialize(reconcile_on_startup=False)
    manager.save(_instance_at_revision(definition_repo, 1))

    result = migrate_instance(
        definition_repo,
        manager,
        instance_id="inst-1",
        target_revision=2,
        dry_run=False,
    )

    assert result["blockers"] == ["no migration rule registered"]
    saved = manager.get("inst-1")
    assert saved.metadata["migration_status"] == "failed"


def test_migrate_instance_raises_when_instance_missing() -> None:
    definition_repo = _repo_with_revisions()
    _, manager = _repos()
    try:
        migrate_instance(
            definition_repo,
            manager,
            instance_id="missing",
            target_revision=2,
        )
    except InstanceNotFoundError as exc:
        assert exc.instance_id == "missing"
    else:
        raise AssertionError("expected InstanceNotFoundError")


def test_request_instance_migration_sets_pending_metadata() -> None:
    definition_repo = _repo_with_revisions()
    instance = _instance_at_revision(definition_repo, 1)
    request_instance_migration(instance, 2)
    assert instance.metadata["migration_status"] == "pending"
    assert instance.metadata["migration_target_revision"] == 2
    assert instance.metadata["migration_from_revision"] == 1


def test_request_instance_migration_rejects_non_forward_target() -> None:
    definition_repo = _repo_with_revisions()
    instance = _instance_at_revision(definition_repo, 2)
    try:
        request_instance_migration(instance, 2)
    except InstanceMigrationError:
        return
    raise AssertionError("expected InstanceMigrationError")