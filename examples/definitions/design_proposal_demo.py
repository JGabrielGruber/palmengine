"""
Design Service demo — propose, validate, impact, commit with auto-migrate.

Demonstrates the Design Service (0.25) revision loop and post-commit instance
migration on top of definition revisioning (0.24).

**Script (library / CI):**

    uv run python examples/definitions/design_proposal_demo.py

**Operator meta-flow (when example definitions are loaded):**

    # 1. Start a session pinned to revision 1
    palm flow start design-demo-flow

    # 2. Note instance_id from ``palm instance list``

    # 3. Operator wizard: confirm → preview or commit via DesignService
    palm flow start design-proposal-demo

**MCP equivalent (in-process ``palm-mcp``):**

    palm_design_propose_flow(body=..., base_flow_id="design-demo-flow")
    palm_design_validate(proposal_id=...)
    palm_design_impact(proposal_id=...)
    palm_design_commit(proposal_id=...)

Registers:

- ``design-demo-flow`` at revision 1 (source wizard)
- Migration rule ``1 → 2`` (sets ``migrated: true`` in state)
- ``design-proposal-demo`` wizard (preview or commit through DesignService)
"""

from __future__ import annotations

from typing import Any

from palm.app import ApplicationHost, DeploymentProfile
from palm.app.settings import PalmSettings
from palm.common.exceptions import DefinitionNotFoundError
from palm.common.persistence.definition_migration import (
    CallableMigrationRule,
    register_migration_rule,
)
from palm.definitions import FlowDefinition, ProcessDefinition
from palm.instances import ProcessInstance
from palm.patterns.wizard.bindings.compensation.handler import (
    CommitContext,
    CommitResult,
    default_commit_registry,
)

FLOW_ID = "design-demo-flow"
_HOST_BY_STORAGE_ID: dict[int, ApplicationHost] = {}


def attach_design_host(host: ApplicationHost) -> None:
    """Bind a running host to shared storage for meta-flow commit handlers."""
    _HOST_BY_STORAGE_ID[id(host.storage)] = host


def _resolve_design_host(repository: object) -> ApplicationHost | None:
    storage = getattr(repository, "_storage", None)
    if storage is None:
        return None
    attached = _HOST_BY_STORAGE_ID.get(id(storage))
    if attached is not None:
        return attached
    return _host_for_repository(repository)

DESIGN_DEMO_SOURCE_V1 = FlowDefinition(
    name=FLOW_ID,
    pattern="wizard",
    options={
        "steps": [
            {
                "slug": "note",
                "title": "Note (revision 1)",
                "prompt": "Enter a note for this revision-1 session",
                "validation": [{"rule": "not_empty"}],
            },
        ],
    },
)

DESIGN_DEMO_SOURCE_V2 = FlowDefinition(
    name=FLOW_ID,
    pattern="wizard",
    options={
        "steps": [
            {
                "slug": "note",
                "title": "Note (revision 2)",
                "prompt": "Enter a note for this revision-2 session",
                "validation": [{"rule": "not_empty"}],
            },
            {
                "slug": "extra",
                "title": "Extra",
                "prompt": "Optional extra step added in revision 2",
            },
        ],
    },
)

DESIGN_PROPOSAL_DEMO_FLOW = FlowDefinition(
    name="design-proposal-demo",
    pattern="wizard",
    options={
        "include_summary": True,
        "include_commit": True,
        "commit_hook": "apply_design_proposal",
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "instance_id",
                "title": "Instance ID",
                "prompt": "Enter the instance id pinned to revision 1",
                "validation": [{"rule": "not_empty"}],
            },
            {
                "slug": "confirm",
                "title": "Confirm",
                "prompt": "Propose revision 2 for design-demo-flow via DesignService?",
                "field_type": "choice",
                "choices": ["yes", "no"],
            },
            {
                "slug": "action",
                "title": "Action",
                "prompt": "Preview (validate + impact) or commit the proposal?",
                "field_type": "choice",
                "choices": ["preview", "commit"],
            },
        ],
    },
)

DESIGN_PROPOSAL_DEMO_PROCESS = ProcessDefinition(
    name="design-proposal-demo",
    flows=[DESIGN_PROPOSAL_DEMO_FLOW],
    metadata={
        "example": True,
        "description": "Operator wizard for Design Service propose → commit (0.25.6)",
    },
)


def register_migration_demo_rule() -> None:
    """Register the demo migration rule (idempotent at registry level)."""
    register_migration_rule(
        CallableMigrationRule(
            flow_id=FLOW_ID,
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (True, []),
            _migrate_state=lambda ctx: {**ctx.state, "migrated": True},
        ),
    )


def run_design_proposal_pipeline(
    host: ApplicationHost,
    *,
    instance_id: str,
    preview_only: bool = False,
) -> dict[str, Any]:
    """
    End-to-end DesignService loop for ``design-demo-flow`` revision 2.

    Returns a structured result with proposal, validation, impact, and optional commit payload.
    """
    register_migration_demo_rule()

    instance = host.instance_manager.get(instance_id)
    if instance.flow_revision not in (None, 1):
        raise ValueError(f"instance {instance_id!r} must be pinned to revision 1")

    proposed = host.design.propose_flow(
        DESIGN_DEMO_SOURCE_V2.to_dict(),
        base_flow_id=FLOW_ID,
    )
    proposal_id = str(proposed["proposal"]["proposal_id"])
    validation = host.design.validate_proposal(proposal_id)
    impact = host.design.analyze_proposal_impact(proposal_id)

    result: dict[str, Any] = {
        "proposal_id": proposal_id,
        "validation": validation,
        "impact": impact,
        "phase": "preview" if preview_only else "commit",
    }

    if preview_only:
        return result

    committed = host.design.commit_proposal(proposal_id)
    result["committed"] = committed

    updated = host.instance_manager.get(instance_id)
    result["instance"] = {
        "instance_id": instance_id,
        "flow_revision": updated.flow_revision,
        "migrated": updated.state_snapshot.get("migrated"),
    }
    return result


def _host_for_repository(repository: object) -> ApplicationHost | None:
    storage = getattr(repository, "_storage", None)
    if storage is None or not getattr(storage, "is_initialized", False):
        return None
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one(), storage=storage)
    host.start()
    return host


def _make_apply_design_proposal_handler(repository: object):
    def _apply_design_proposal(ctx: CommitContext) -> CommitResult:
        if ctx.answers.get("confirm") != "yes":
            return CommitResult.failure("Design proposal cancelled")

        instance_id = str(ctx.answers.get("instance_id") or "").strip()
        if not instance_id:
            return CommitResult.failure("instance_id is required")

        action = str(ctx.answers.get("action") or "preview").strip()
        preview_only = action != "commit"

        host = _resolve_design_host(repository)
        if host is None:
            return CommitResult.failure(
                "Storage not initialized; run examples/definitions/design_proposal_demo.py "
                "or use palm_design_* MCP tools"
            )

        ephemeral = host is not _HOST_BY_STORAGE_ID.get(id(getattr(repository, "_storage", None)))
        try:
            payload = run_design_proposal_pipeline(
                host,
                instance_id=instance_id,
                preview_only=preview_only,
            )
        except Exception as exc:
            return CommitResult.failure(str(exc))
        finally:
            if ephemeral:
                host.shutdown()

        return CommitResult.success(payload)

    return _apply_design_proposal


def _flow_exists(repository: object, flow_name: str) -> bool:
    has_flow = getattr(repository, "has_flow", None)
    if callable(has_flow):
        return bool(has_flow(flow_name, by_id=False))
    get_flow = getattr(repository, "get_flow", None)
    if not callable(get_flow):
        return False
    try:
        get_flow(flow_name)
    except DefinitionNotFoundError:
        return False
    return True


def _publish_flow_if_missing(repository: object, flow: FlowDefinition) -> None:
    if _flow_exists(repository, flow.name):
        return
    publish = getattr(repository, "publish_flow_revision", None)
    register_flow = getattr(repository, "register_flow", None)
    save_flow = getattr(repository, "save_flow", None)
    if callable(publish):
        publish(flow)
    elif callable(register_flow):
        register_flow(flow)
    elif callable(save_flow):
        save_flow(flow)


def register_definitions(repository: object) -> None:
    """Register demo flows, migration rule, and meta-flow commit handler."""
    register_migration_demo_rule()
    default_commit_registry().register(
        "apply_design_proposal",
        _make_apply_design_proposal_handler(repository),
    )

    _publish_flow_if_missing(repository, DESIGN_DEMO_SOURCE_V1)
    _publish_flow_if_missing(repository, DESIGN_PROPOSAL_DEMO_FLOW)

    register_process = getattr(repository, "register_process", None)
    save_process = getattr(repository, "save_process", None)
    get_process = getattr(repository, "get_process", None)
    process_exists = False
    if callable(get_process):
        try:
            get_process("design-proposal-demo")
            process_exists = True
        except DefinitionNotFoundError:
            process_exists = False

    if not process_exists:
        if callable(register_process):
            register_process(DESIGN_PROPOSAL_DEMO_PROCESS)
        elif callable(save_process):
            save_process(DESIGN_PROPOSAL_DEMO_PROCESS)


def _seed_revision_one_instance(host: ApplicationHost, *, instance_id: str) -> None:
    register_migration_demo_rule()
    if not host.definitions._repository.has_flow(FLOW_ID, by_id=False):
        host.definitions.create_flow(DESIGN_DEMO_SOURCE_V1.to_dict())
    flow_v1 = host.definitions.get_flow(FLOW_ID, revision=1)
    host.instance_manager.save(
        ProcessInstance(
            instance_id=instance_id,
            job_id="job-design-demo",
            status="WAITING_FOR_INPUT",
            state_snapshot={"answers": {}},
            flow_definition=flow_v1,
            pattern="wizard",
            flow_id=FLOW_ID,
            flow_revision=1,
        )
    )


def main() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    host.start()
    attach_design_host(host)

    instance_id = "inst-design-demo"
    _seed_revision_one_instance(host, instance_id=instance_id)

    result = run_design_proposal_pipeline(host, instance_id=instance_id, preview_only=False)
    print("proposal_id:", result["proposal_id"])
    print("valid:", result["validation"]["valid"])
    print("compatible:", result["impact"]["summary"].get("compatible"))
    print("revision:", result["committed"]["revision"])
    print("migrations:", result["committed"]["migrations"])
    print("instance:", result["instance"])

    assert result["validation"]["valid"] is True
    assert result["committed"]["revision"] == 2
    assert result["committed"]["migrations"]["succeeded"] == 1
    assert result["instance"]["flow_revision"] == 2
    assert result["instance"]["migrated"] is True

    host.shutdown()


if __name__ == "__main__":
    main()