"""Integration tests for palm-design-entry assist scenario (0.30.2)."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings


@pytest.fixture
def assist_host() -> Iterator[ApplicationHost]:
    settings = PalmSettings.for_tests(load_examples=True)
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()
    yield host
    host.shutdown()


def test_design_entry_module_does_not_import_design_service() -> None:
    """Enricher module must not import DesignService (boundary oracle)."""
    path = Path(__file__).resolve().parents[1] / "examples/definitions/design_entry.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {
        "palm.services.design.service",
        "palm.services.design",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden
                assert not alias.name.startswith("palm.services.design")
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module not in forbidden
            assert not node.module.startswith("palm.services.design")


def test_design_entry_listed_as_scenario(assist_host: ApplicationHost) -> None:
    rows = assist_host.assist.dispatch(["assist", "scenarios"])
    ids = {row["scenario_id"] for row in rows}
    assert "design-entry" in ids


def test_start_design_entry_does_not_create_proposals(
    assist_host: ApplicationHost,
) -> None:
    before = len(assist_host.design.list_proposals())
    started = assist_host.assist.start_scenario("design-entry", {})
    assert "session_id" in started
    assert started.get("scenario_id") == "design-entry"
    assert started.get("question")
    after = len(assist_host.design.list_proposals())
    assert after == before


def test_design_entry_intent_input_does_not_call_propose(
    assist_host: ApplicationHost,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def _spy(*args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        raise AssertionError("propose_flow must not be called from design-entry input")

    monkeypatch.setattr(assist_host.design, "propose_flow", _spy)
    started = assist_host.assist.start_scenario("design-entry", {})
    session_id = started["session_id"]
    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "create-flow"},
    )
    assert calls == []
    assert updated.get("session_id") == session_id
    # name_or_base step or waiting
    assert updated.get("status") in {"waiting", "complete"}


def test_design_entry_create_flow_has_design_actions(
    assist_host: ApplicationHost,
) -> None:
    started = assist_host.assist.start_scenario("design-entry", {})
    session_id = started["session_id"]
    # intent → name_or_base
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "create-flow"},
    )
    # name_or_base → summary
    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "my-new-flow"},
    )
    actions = updated.get("actions") or []
    tools = {a.get("tool") for a in actions if isinstance(a, dict)}
    aliases = {a.get("alias") for a in actions if isinstance(a, dict)}
    assert "palm_design_publish_flow" in tools
    hint = (updated.get("hint") or "").lower()
    assert "publish" in hint or "design" in hint


def test_design_entry_handoff_kind_design(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("design-entry", {})
    session_id = started["session_id"]
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "create-flow"},
    )
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "demo-flow"},
    )
    # confirm summary if needed
    ctx = assist_host.assist.dispatch(["assist", "session", session_id])
    if ctx.get("waiting_for_input") or ctx.get("status") == "waiting":
        assist_host.assist.dispatch(
            ["assist", "session", session_id, "input"],
            {"value": "yes"},
        )
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "design"
    assert handoff["handoff"]["design_action"] == "publish_flow"
    assert handoff["handoff"]["suggested_name"] == "demo-flow"
    assert "palm_design_publish_flow" in handoff["handoff"]["operator_hint"]


def test_design_entry_improve_handoff_base_flow_id(
    assist_host: ApplicationHost,
) -> None:
    started = assist_host.assist.start_scenario("design-entry", {})
    session_id = started["session_id"]
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "improve-flow"},
    )
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "todo-builder"},
    )
    ctx = assist_host.assist.dispatch(["assist", "session", session_id])
    if ctx.get("status") == "waiting":
        assist_host.assist.dispatch(
            ["assist", "session", session_id, "input"],
            {"value": "yes"},
        )
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "design"
    assert handoff["handoff"]["base_flow_id"] == "todo-builder"
    assert handoff["handoff"]["intent"] == "improve-flow"


def test_design_entry_start_alias_resolves(assist_host: ApplicationHost) -> None:
    from palm.services.assist.registry import resolve_mcp_alias

    path = resolve_mcp_alias("design-entry/start")
    assert path == ("assist", "scenarios", "design-entry", "start")
