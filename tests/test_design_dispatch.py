"""Tests for registry-driven design command dispatch (0.25.8)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.common.operator.path_match import match_command_path
from palm.services.design.dispatch import _DISPATCH_HANDLERS
from palm.services.design.grammar import resolve_design_command
from palm.services.design.registry import design_commands, resolve_design_mcp_alias
from palm.services.design.registry import clear_design_contributors


@pytest.fixture
def design_host() -> Iterator[ApplicationHost]:
    clear_design_contributors()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()
    yield host
    host.shutdown()


def test_match_command_path_captures_placeholders() -> None:
    capture = match_command_path(
        ("design", "proposals", "prop-1", "validate"),
        ("design", "proposals", "{proposal_id}", "validate"),
    )
    assert capture == {"proposal_id": "prop-1"}


def test_match_command_path_rejects_mismatch() -> None:
    assert match_command_path(("design", "propose"), ("design", "proposals")) is None
    assert (
        match_command_path(
            ("design", "proposals", "prop-1", "commit"),
            ("design", "proposals", "{proposal_id}", "validate"),
        )
        is None
    )


_CONCRETE_PATHS: dict[str, tuple[str, ...]] = {
    "propose_flow": ("design", "propose"),
    "list_proposals": ("design", "proposals"),
    "get_proposal": ("design", "proposals", "prop-1"),
    "validate_proposal": ("design", "proposals", "prop-1", "validate"),
    "analyze_impact": ("design", "proposals", "prop-1", "impact"),
    "commit_proposal": ("design", "proposals", "prop-1", "commit"),
    "discard_proposal": ("design", "proposals", "prop-1", "discard"),
}


def test_resolve_design_command_covers_registry() -> None:
    for spec in design_commands():
        path = _CONCRETE_PATHS[spec.command_id]
        resolved = resolve_design_command(path)
        assert resolved.spec.command_id == spec.command_id


def test_all_design_commands_have_dispatch_handlers() -> None:
    registered = {spec.command_id for spec in design_commands()}
    assert registered == set(_DISPATCH_HANDLERS)


def test_resolve_design_command_unknown_path() -> None:
    with pytest.raises(ValueError, match="unrecognized design dispatch path"):
        resolve_design_command(["design", "unknown"])


def test_mcp_alias_resolves_to_dispatchable_path() -> None:
    path = resolve_design_mcp_alias("design/impact", params={"proposal_id": "prop-99"})
    assert path is not None
    resolved = resolve_design_command(path)
    assert resolved.spec.command_id == "analyze_impact"
    assert resolved.capture["proposal_id"] == "prop-99"


def test_dispatch_all_registry_paths(design_host: ApplicationHost) -> None:
    body = {
        "name": "registry-dispatch-flow",
        "pattern": "wizard",
        "options": {"steps": [{"slug": "note", "title": "Note", "prompt": "Note?"}]},
    }
    proposed = design_host.design.dispatch(["design", "propose"], {"body": body})
    proposal_id = proposed["proposal"]["proposal_id"]

    listed = design_host.design.dispatch(["design", "proposals"])
    assert any(row["proposal_id"] == proposal_id for row in listed["proposals"])

    fetched = design_host.design.dispatch(["design", "proposals", proposal_id])
    assert fetched["proposal_id"] == proposal_id

    validated = design_host.design.dispatch(
        ["design", "proposals", proposal_id, "validate"],
    )
    assert validated["valid"] is True

    impact = design_host.design.dispatch(
        ["design", "proposals", proposal_id, "impact"],
    )
    assert impact["target_revision"] == 1

    committed = design_host.design.dispatch(
        ["design", "proposals", proposal_id, "commit"],
    )
    assert committed["revision"] == 1

    body2 = {
        "name": "registry-dispatch-flow-2",
        "pattern": "wizard",
        "options": {"steps": [{"slug": "note", "title": "Note", "prompt": "Note?"}]},
    }
    proposed2 = design_host.design.dispatch(["design", "propose"], {"body": body2})
    proposal_id2 = proposed2["proposal"]["proposal_id"]
    discarded = design_host.design.dispatch(
        ["design", "proposals", proposal_id2, "discard"],
    )
    assert discarded["discarded"] is True