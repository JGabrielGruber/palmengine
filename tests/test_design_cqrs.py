"""Tests for design service CQRS transport bindings (0.25.7)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, DeploymentProfile
from palm.app.settings import PalmSettings
from palm.common.cqrs.schemas import build_schema_registry
from palm.definitions import FlowDefinition
from palm.services.design.bindings.cqrs.commands import (
    CommitDesignProposalCommand,
    ProposeFlowDefinitionCommand,
)
from palm.services.design.bindings.cqrs.queries import (
    AnalyzeDesignProposalImpactQuery,
    ListDesignProposalsQuery,
    ValidateDesignProposalQuery,
)
from palm.services.design.registry import clear_design_contributors


@pytest.fixture
def design_host() -> Iterator[ApplicationHost]:
    clear_design_contributors()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    host.start()
    yield host
    host.shutdown()


def _flow_body(name: str = "cqrs-design-flow") -> dict:
    return FlowDefinition(
        name=name,
        pattern="wizard",
        options={"steps": [{"slug": "note", "title": "Note", "prompt": "Note?"}]},
    ).to_dict()


def test_design_cqrs_schemas_registered() -> None:
    registry = build_schema_registry()
    assert ProposeFlowDefinitionCommand in registry.command_types()
    assert ValidateDesignProposalQuery in registry.query_types()
    assert AnalyzeDesignProposalImpactQuery in registry.query_types()


def test_propose_and_validate_via_command_bus(design_host: ApplicationHost) -> None:
    proposed = design_host.execute(
        ProposeFlowDefinitionCommand(body=_flow_body()),
    )
    proposal_id = proposed["proposal"]["proposal_id"]

    validation = design_host.ask(
        ValidateDesignProposalQuery(proposal_id=proposal_id),
    )
    assert validation["valid"] is True

    listed = design_host.ask(ListDesignProposalsQuery())
    assert any(row["proposal_id"] == proposal_id for row in listed)


def test_analyze_and_commit_via_cqrs_bus(design_host: ApplicationHost) -> None:
    proposed = design_host.execute(
        ProposeFlowDefinitionCommand(body=_flow_body("cqrs-commit-flow")),
    )
    proposal_id = proposed["proposal"]["proposal_id"]

    impact = design_host.ask(
        AnalyzeDesignProposalImpactQuery(proposal_id=proposal_id),
    )
    assert impact["target_revision"] == 1

    committed = design_host.execute(
        CommitDesignProposalCommand(proposal_id=proposal_id),
    )
    assert committed["revision"] == 1
    assert committed["flow_id"] == "cqrs-commit-flow"