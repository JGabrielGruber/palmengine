"""Design Service demo — propose, validate, impact, commit with auto-migrate."""

from __future__ import annotations

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.common.managers.instance_manager import InstanceManager
from palm.common.persistence.definition_migration import (
    CallableMigrationRule,
    register_migration_rule,
)
from palm.common.persistence.instance_repository import InstanceRepository
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance


def _flow(revision_label: str) -> dict:
    return FlowDefinition(
        name="design-demo-flow",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "note",
                    "title": f"Note ({revision_label})",
                    "prompt": "Note?",
                }
            ]
        },
    ).to_dict()


def main() -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="design-demo-flow",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (True, []),
            _migrate_state=lambda ctx: {**ctx.state, "migrated": True},
        ),
    )

    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    host.definitions.create_flow(_flow("v1"))
    flow_v1 = host.definitions.get_flow("design-demo-flow", revision=1)
    instance_repo = InstanceRepository(host.storage)
    manager = InstanceManager(instance_repo)
    manager.initialize(reconcile_on_startup=False)
    manager.save(
        ProcessInstance(
            instance_id="inst-design-demo",
            job_id="job-design-demo",
            status="WAITING_FOR_INPUT",
            state_snapshot={"answers": {}},
            flow_definition=flow_v1,
            pattern="wizard",
            flow_id="design-demo-flow",
            flow_revision=1,
        )
    )

    proposed = host.design.propose_flow(_flow("v2"), base_flow_id="design-demo-flow")
    proposal_id = proposed["proposal"]["proposal_id"]
    print("proposed:", proposal_id)

    validation = host.design.validate_proposal(proposal_id)
    print("valid:", validation["valid"])

    impact = host.design.analyze_proposal_impact(proposal_id)
    print("compatible instances:", impact["summary"].get("compatible"))

    committed = host.design.commit_proposal(proposal_id)
    print("revision:", committed["revision"])
    print("migrations:", committed["migrations"])

    host.shutdown()


if __name__ == "__main__":
    main()