"""Definitions CQRS transport on standalone ServerContext (MCP bootstrap path)."""

from __future__ import annotations

import pytest

from palm.common.services.errors import InstanceNotFoundServiceError
from palm.definitions import FlowDefinition
from palm.runtimes.mcp.in_process import _bootstrap_server_context


def _wizard_body(name: str) -> dict:
    return FlowDefinition(
        name=name,
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()


def test_analyze_impact_via_standalone_context() -> None:
    ctx = _bootstrap_server_context()
    body = _wizard_body("standalone-impact-flow")
    ctx.definitions.create_flow(body)
    impact = ctx.definitions.analyze_impact("standalone-impact-flow", target_revision=2)
    assert impact["flow_id"] == "standalone-impact-flow"
    assert impact["target_revision"] == 2
    assert "summary" in impact


def test_migrate_instance_dry_run_raises_for_missing_instance() -> None:
    ctx = _bootstrap_server_context()
    with pytest.raises(InstanceNotFoundServiceError):
        ctx.definitions.migrate_instance(
            "nonexistent-instance",
            target_revision=1,
            dry_run=True,
        )