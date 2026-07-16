"""Design service resource proposals (0.27.2)."""

from __future__ import annotations

import pytest

from palm.app import ApplicationHost, DeploymentProfile, PalmSettings
from palm.definitions import FlowDefinition


@pytest.fixture
def design_host():
    settings = PalmSettings()
    with ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one()) as host:
        yield host


def test_propose_resource_validate_commit(design_host) -> None:
    body = {
        "name": "design-test-ledger",
        "provider": "rest",
        "action": "fetch",
        "resource_id": "ledger/{{ state.player_name }}",
        "params": {"player_name": "{{ state.player_name }}"},
    }
    proposed = design_host.design.propose_resource(body)
    proposal_id = proposed["proposal"]["proposal_id"]
    assert proposed["proposal"]["kind"] == "resource"
    assert proposed["validation"]["valid"] is True

    impact = design_host.design.analyze_proposal_impact(proposal_id)
    assert impact["kind"] == "resource"
    assert impact["resource_ref"] == "design-test-ledger"

    committed = design_host.design.commit_proposal(proposal_id)
    assert committed["kind"] == "resource"
    assert committed["resource_ref"] == "design-test-ledger"
    assert committed["resource"]["name"] == "design-test-ledger"


def test_resource_impact_lists_referencing_flows(design_host) -> None:
    design_host.definitions.create_flow(
        FlowDefinition(
            name="resource-ref-demo",
            pattern="wizard",
            options={
                "steps": [
                    {
                        "slug": "load",
                        "step_kind": "resource",
                        "resource_ref": "fetch-customer",
                        "title": "Load",
                    }
                ]
            },
        ).to_dict()
    )
    body = {
        "name": "fetch-customer",
        "provider": "rest",
        "action": "fetch",
        "resource_id": "customers/{customer_id}",
    }
    proposed = design_host.design.propose_resource(body, base_resource_id="fetch-customer")
    impact = design_host.design.analyze_proposal_impact(proposed["proposal"]["proposal_id"])
    refs = impact.get("referencing_flows") or []
    assert any(row.get("flow_id") == "resource-ref-demo" for row in refs)