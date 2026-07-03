"""Tests for mutation envelope on assistant and powertool views."""

from __future__ import annotations

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.flow_session_view import shape_flow_session_view
from palm.common.operator.view_registry import OperatorViewContext, clear_operator_view_builders
from palm.services.assist.views import build_assistant_view, ensure_assist_view_registration


def _setup_assistant_registry() -> None:
    clear_operator_view_builders()
    ensure_assist_view_registration()


def test_assistant_view_includes_mutation_block_on_waiting() -> None:
    _setup_assistant_registry()
    flat = {
        "instance_id": "inst-1",
        "status": "WAITING_FOR_INPUT",
        "current_step_slug": "intent",
        "prompt": {
            "text": "Choose",
            "field_type": "choice",
            "choices": ["a"],
            "step_kind": "input",
        },
    }
    ctx = OperatorViewContext(session_id="inst-1", flow_id="flow-x")
    payload = build_assistant_view(flat, context=ctx)
    assert payload["mutation"]["mutations_allowed"] is True
    assert payload["mutation"]["step_slug"] == "intent"


def test_powertool_compact_includes_mutation_block() -> None:
    flat = {
        "instance_id": "inst-1",
        "status": "SUCCEEDED",
        "current_step_slug": "summary",
        "prompt": {"step_kind": "summary"},
    }
    payload = compact_wizard_inspect(flat)
    assert payload["mutation"]["mutations_allowed"] is False


def test_assistant_flow_session_shape_includes_mutation() -> None:
    _setup_assistant_registry()
    flat = {
        "session_id": "inst-1",
        "instance_id": "inst-1",
        "status": "WAITING_FOR_INPUT",
        "current_step_slug": "intent",
        "flow_name": "palm-operator-entry",
        "prompt": {
            "text": "What would you like to do?",
            "field_type": "choice",
            "choices": ["todo-builder", "inspect-only"],
            "step_kind": "input",
        },
    }
    payload = shape_flow_session_view(
        flat,
        format="assistant",
        session_id="inst-1",
        flow_id="palm-operator-entry",
    )
    assert payload["mutation"]["mutations_allowed"] is True
    assert payload["mutation"].get("confirm_step") is not True