"""Tests for Design Service (0.25)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.common.services.errors import DesignCommitRejectedServiceError
from palm.definitions import FlowDefinition
from palm.services.design.proposal import DesignProposalRepository
from palm.services.design.registry import DesignContributor, clear_design_contributors, register_design_contributor


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