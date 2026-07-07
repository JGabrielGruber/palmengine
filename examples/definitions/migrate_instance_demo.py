"""
Migrate instance demo — revision upgrade wizard for durable instances.

Demonstrates definition revisioning (0.24.1), migration rules (0.24.2), and
instance migration execution (0.24.3).

Workflow::

    # 1. Start a session on revision 1 of the demo flow
    palm flow start migrate-demo-source

    # 2. Run the operator wizard to dry-run then apply migration to revision 2
    palm flow start migrate-instance-demo

Registers:
- ``migrate-demo-source`` flow at revisions 1 and 2
- Migration rule ``1 → 2`` (adds ``schema_version`` to state snapshot)
- ``migrate-instance-demo`` wizard (confirm → dry-run → apply → summary)

REST equivalent::

    GET  /v1/api/definitions/flows/migrate-demo-source/impact
    POST /v1/api/definitions/instances/{instance_id}/migrate
         {"target_revision": 2, "dry_run": true}
"""

from __future__ import annotations

from typing import Any

from palm.common.managers.instance_manager import InstanceManager
from palm.common.persistence.definition_migration import CallableMigrationRule, register_migration_rule
from palm.common.persistence.instance_migration import migrate_instance
from palm.common.persistence.instance_repository import InstanceRepository
from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.bindings.compensation.handler import CommitResult, default_commit_registry

MIGRATE_DEMO_SOURCE_V1 = FlowDefinition(
    id="flow-migrate-demo-source",
    name="migrate-demo-source",
    pattern="wizard",
    options={
        "steps": [
            {
                "slug": "note",
                "title": "Note",
                "prompt": "Enter a note for this revision-1 session",
                "validation": [{"rule": "not_empty"}],
            },
        ],
    },
)

MIGRATE_DEMO_SOURCE_V2 = FlowDefinition(
    id="flow-migrate-demo-source",
    name="migrate-demo-source",
    pattern="wizard",
    options={
        "steps": [
            {
                "slug": "note",
                "title": "Note",
                "prompt": "Enter a note (revision 2)",
                "validation": [{"rule": "not_empty"}],
            },
            {
                "slug": "priority",
                "title": "Priority",
                "prompt": "Select priority",
                "field_type": "choice",
                "choices": ["low", "high"],
            },
        ],
    },
)

MIGRATE_INSTANCE_DEMO_FLOW = FlowDefinition(
    id="flow-migrate-instance-demo",
    name="migrate-instance-demo",
    pattern="wizard",
    options={
        "include_summary": True,
        "include_commit": True,
        "commit_hook": "apply_instance_migration",
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "instance_id",
                "title": "Instance ID",
                "prompt": "Enter the instance id to migrate",
                "validation": [{"rule": "not_empty"}],
            },
            {
                "slug": "target_revision",
                "title": "Target revision",
                "prompt": "Enter the target flow revision (e.g. 2)",
                "validation": [{"rule": "not_empty"}],
            },
            {
                "slug": "confirm",
                "title": "Confirm",
                "prompt": "Proceed with migration planning?",
                "field_type": "choice",
                "choices": ["yes", "no"],
            },
            {
                "slug": "action",
                "title": "Action",
                "prompt": "Dry-run the migration rule or apply it?",
                "field_type": "choice",
                "choices": ["dry_run", "apply"],
            },
        ],
    },
)

MIGRATE_INSTANCE_DEMO_PROCESS = ProcessDefinition(
    id="proc-migrate-instance-demo",
    name="migrate-instance-demo",
    flows=[MIGRATE_INSTANCE_DEMO_FLOW],
    metadata={
        "example": True,
        "description": "Operator wizard for instance definition migration (0.24.3)",
    },
)


def _migration_services(repository: object) -> tuple[Any, InstanceManager] | tuple[None, None]:
    storage = getattr(repository, "_storage", None)
    if storage is None or not getattr(storage, "is_initialized", False):
        return None, None
    instance_manager = InstanceManager(InstanceRepository(storage))
    instance_manager.initialize(reconcile_on_startup=False)
    return repository, instance_manager


def _make_apply_handler(repository: object):
    def _apply_instance_migration(ctx: Any) -> CommitResult:
        return _run_migration_commit(ctx, repository)

    return _apply_instance_migration


def _run_migration_commit(ctx: Any, repository: object) -> CommitResult:
    if ctx.answers.get("confirm") != "yes":
        return CommitResult.failure("Migration cancelled")

    instance_id = str(ctx.answers.get("instance_id") or "").strip()
    if not instance_id:
        return CommitResult.failure("instance_id is required")

    try:
        target_revision = int(str(ctx.answers.get("target_revision") or "").strip())
    except ValueError:
        return CommitResult.failure("target_revision must be an integer")

    action = str(ctx.answers.get("action") or "dry_run").strip()
    dry_run = action != "apply"

    definition_repo, instance_manager = _migration_services(repository)
    if definition_repo is None or instance_manager is None:
        return CommitResult.failure(
            "Storage not initialized; use REST POST /v1/api/definitions/instances/"
            f"{instance_id}/migrate"
        )

    try:
        dry_result = migrate_instance(
            definition_repo,
            instance_manager,
            instance_id=instance_id,
            target_revision=target_revision,
            dry_run=True,
        )
    except Exception as exc:
        return CommitResult.failure(str(exc))

    if dry_run:
        return CommitResult.success(
            {
                "phase": "dry_run",
                "dry_run": dry_result,
            }
        )

    if not dry_result.get("blockers"):
        try:
            applied = migrate_instance(
                definition_repo,
                instance_manager,
                instance_id=instance_id,
                target_revision=target_revision,
                dry_run=False,
            )
        except Exception as exc:
            return CommitResult.failure(str(exc))
        return CommitResult.success(
            {
                "phase": "apply",
                "dry_run": dry_result,
                "applied": applied,
            }
        )

    return CommitResult.failure(
        "Migration blocked: " + ", ".join(str(item) for item in dry_result.get("blockers") or []),
    )


def register_definitions(repository: object) -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="migrate-demo-source",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda ctx: (
                bool(ctx.state.get("answers", {}).get("note")),
                ["note answer required before migration"],
            ),
            _migrate_state=lambda ctx: {
                **ctx.state,
                "schema_version": 2,
                "answers": {
                    **dict(ctx.state.get("answers") or {}),
                    "priority": "low",
                },
            },
        ),
    )
    default_commit_registry().register(
        "apply_instance_migration",
        _make_apply_handler(repository),
    )

    publish = getattr(repository, "publish_flow_revision", None)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)

    if callable(publish):
        publish(MIGRATE_DEMO_SOURCE_V1)
        publish(MIGRATE_DEMO_SOURCE_V2)
        publish(MIGRATE_INSTANCE_DEMO_FLOW)
    elif callable(save_flow):
        save_flow(MIGRATE_DEMO_SOURCE_V1)
        save_flow(MIGRATE_DEMO_SOURCE_V2)
        save_flow(MIGRATE_INSTANCE_DEMO_FLOW)

    if callable(save_process):
        save_process(MIGRATE_INSTANCE_DEMO_PROCESS)