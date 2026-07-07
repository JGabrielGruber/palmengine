"""Tests for Design Service (0.25)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.common.persistence.definition_migration import (
    CallableMigrationRule,
    migration_registry,
    register_migration_rule,
)
from palm.common.services.errors import DesignCommitRejectedServiceError
from palm.core import StorageEngine
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance
from palm.services.design.factory import create_proposal_repository
from palm.services.design.proposal import DesignProposalRepository
from palm.services.design.registry import DesignContributor, clear_design_contributors, register_design_contributor
from palm.services.design.storage_proposal_repository import StorageDesignProposalRepository


@pytest.fixture
def design_settings() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


@pytest.fixture
def design_host(design_settings: PalmSettings) -> Iterator[ApplicationHost]:
    host = ApplicationHost(settings=design_settings, profile=HostProfile.all_in_one())
    host.start()
    yield host
    host.shutdown()


def setup_function() -> None:
    clear_design_contributors()
    migration_registry.clear()


def _quick_flow_body(name: str = "design-test-flow") -> dict:
    return FlowDefinition(
        name=name,
        pattern="wizard",
        options={"steps": [{"slug": "note", "title": "Note", "prompt": "Note?"}]},
    ).to_dict()


def test_application_host_exposes_design(design_host: ApplicationHost) -> None:
    assert design_host.design is not None
    assert design_host.design.definitions is design_host.definitions


def test_propose_and_commit_new_flow(design_host: ApplicationHost) -> None:
    result = design_host.design.propose_flow(_quick_flow_body())
    proposal_id = result["proposal"]["proposal_id"]
    assert result["validation"]["valid"] is True

    impact = design_host.design.analyze_proposal_impact(proposal_id)
    assert impact["target_revision"] == 1

    committed = design_host.design.commit_proposal(proposal_id)
    assert committed["revision"] == 1
    assert committed["flow_id"] == "design-test-flow"

    flows = design_host.definitions.list_flows()
    assert any(row.get("name") == "design-test-flow" for row in flows)


def test_propose_revision_for_existing_flow(design_host: ApplicationHost) -> None:
    design_host.definitions.create_flow(_quick_flow_body("rev-flow"))
    body = _quick_flow_body("rev-flow")
    body["options"]["steps"].append(
        {"slug": "extra", "title": "Extra", "prompt": "Extra step?"},
    )
    result = design_host.design.propose_flow(body, base_flow_id="rev-flow")
    proposal_id = result["proposal"]["proposal_id"]

    impact = design_host.design.analyze_proposal_impact(proposal_id)
    assert impact["target_revision"] == 2

    committed = design_host.design.commit_proposal(proposal_id)
    assert committed["revision"] == 2


def test_commit_rejected_when_contributor_blocks(design_host: ApplicationHost) -> None:
    register_design_contributor(
        DesignContributor(
            contributor_id="test-blocker",
            validate=lambda _body, _ctx: (False, ["blocked by test"]),
        ),
    )
    result = design_host.design.propose_flow(_quick_flow_body("blocked-flow"))
    proposal_id = result["proposal"]["proposal_id"]
    with pytest.raises(DesignCommitRejectedServiceError):
        design_host.design.commit_proposal(proposal_id)


def test_discard_proposal(design_host: ApplicationHost) -> None:
    result = design_host.design.propose_flow(_quick_flow_body("discard-flow"))
    proposal_id = result["proposal"]["proposal_id"]
    discarded = design_host.design.discard_proposal(proposal_id)
    assert discarded["discarded"] is True
    assert design_host.design.list_proposals() == []


def test_list_proposals_filters_by_flow_id() -> None:
    repo = DesignProposalRepository()
    repo.create(_quick_flow_body("alpha"), flow_id="alpha")
    repo.create(_quick_flow_body("beta"), flow_id="beta")
    rows = repo.list_proposals(flow_id="alpha")
    assert len(rows) == 1
    assert rows[0].flow_id == "alpha"


def test_storage_proposal_repository_persists_across_instances() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo_a = StorageDesignProposalRepository(storage)
    created = repo_a.create(_quick_flow_body("persist-flow"), flow_id="persist-flow")
    repo_b = StorageDesignProposalRepository(storage)
    loaded = repo_b.get(created.proposal_id)
    assert loaded.flow_id == "persist-flow"


def test_host_uses_storage_backed_proposals_when_storage_ready(design_host: ApplicationHost) -> None:
    repo = create_proposal_repository(design_host.storage)
    assert isinstance(repo, (StorageDesignProposalRepository, DesignProposalRepository))


def test_commit_auto_migrates_compatible_instances(design_host: ApplicationHost) -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="migrate-design-flow",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (True, []),
            _migrate_state=lambda ctx: {**ctx.state, "migrated": True},
        ),
    )
    design_host.definitions.create_flow(_quick_flow_body("migrate-design-flow"))
    flow_v1 = design_host.definitions.get_flow("migrate-design-flow", revision=1)
    design_host.instance_manager.save(
        ProcessInstance(
            instance_id="inst-migrate-design",
            job_id="job-migrate-design",
            status="WAITING_FOR_INPUT",
            state_snapshot={"answers": {}},
            flow_definition=flow_v1,
            pattern="wizard",
            flow_id="migrate-design-flow",
            flow_revision=1,
        )
    )

    body = _quick_flow_body("migrate-design-flow")
    body["options"]["steps"].append({"slug": "extra", "title": "Extra", "prompt": "More?"})
    result = design_host.design.propose_flow(body, base_flow_id="migrate-design-flow")
    proposal_id = result["proposal"]["proposal_id"]
    design_host.design.analyze_proposal_impact(proposal_id)

    committed = design_host.design.commit_proposal(proposal_id)
    assert committed["revision"] == 2
    assert committed["migrations"]["succeeded"] == 1
    assert committed["migrations"]["attempted"] == 1

    updated = design_host.instance_manager.get("inst-migrate-design")
    assert updated.flow_revision == 2
    assert updated.state_snapshot.get("migrated") is True


def test_commit_requires_token_when_strict_mode(monkeypatch: pytest.MonkeyPatch, design_host: ApplicationHost) -> None:
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "1")
    result = design_host.design.propose_flow(_quick_flow_body("strict-flow"))
    proposal_id = result["proposal"]["proposal_id"]
    design_host.design.validate_proposal(proposal_id)
    with pytest.raises(DesignCommitRejectedServiceError):
        design_host.design.commit_proposal(proposal_id)

    validation = design_host.design.validate_proposal(proposal_id)
    token = validation["mutation"]["commit_token"]
    committed = design_host.design.commit_proposal(proposal_id, commit_token=token)
    assert committed["revision"] == 1


def test_commit_reanalyzes_impact_before_auto_migrate(design_host: ApplicationHost) -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="fresh-impact-flow",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (True, []),
            _migrate_state=lambda ctx: {**ctx.state, "migrated": True},
        ),
    )
    design_host.definitions.create_flow(_quick_flow_body("fresh-impact-flow"))
    flow_v1 = design_host.definitions.get_flow("fresh-impact-flow", revision=1)

    design_host.instance_manager.save(
        ProcessInstance(
            instance_id="inst-fresh-a",
            job_id="job-fresh-a",
            status="WAITING_FOR_INPUT",
            state_snapshot={"answers": {}},
            flow_definition=flow_v1,
            pattern="wizard",
            flow_id="fresh-impact-flow",
            flow_revision=1,
        )
    )

    body = _quick_flow_body("fresh-impact-flow")
    body["options"]["steps"].append({"slug": "extra", "title": "Extra", "prompt": "More?"})
    result = design_host.design.propose_flow(body, base_flow_id="fresh-impact-flow")
    proposal_id = result["proposal"]["proposal_id"]

    stale_impact = design_host.design.analyze_proposal_impact(proposal_id)
    assert stale_impact["summary"]["compatible"] == 1

    design_host.instance_manager.save(
        ProcessInstance(
            instance_id="inst-fresh-b",
            job_id="job-fresh-b",
            status="WAITING_FOR_INPUT",
            state_snapshot={"answers": {}},
            flow_definition=flow_v1,
            pattern="wizard",
            flow_id="fresh-impact-flow",
            flow_revision=1,
        )
    )

    committed = design_host.design.commit_proposal(proposal_id)
    assert committed["migrations"]["succeeded"] == 2
    assert committed["migrations"]["attempted"] == 2

    for instance_id in ("inst-fresh-a", "inst-fresh-b"):
        updated = design_host.instance_manager.get(instance_id)
        assert updated.flow_revision == 2
        assert updated.state_snapshot.get("migrated") is True


def test_definition_service_next_revision_for_flow(design_host: ApplicationHost) -> None:
    assert design_host.definitions.next_revision_for_flow("missing-flow") == 1
    design_host.definitions.create_flow(_quick_flow_body("next-rev-flow"))
    assert design_host.definitions.get_latest_revision("next-rev-flow") == 1
    assert design_host.definitions.next_revision_for_flow("next-rev-flow") == 2


def test_design_dispatch_via_service(design_host: ApplicationHost) -> None:
    body = _quick_flow_body("dispatch-flow")
    proposed = design_host.design.dispatch(["design", "propose"], {"body": body})
    proposal_id = proposed["proposal"]["proposal_id"]
    listed = design_host.design.dispatch(["design", "proposals"])
    assert any(row["proposal_id"] == proposal_id for row in listed["proposals"])