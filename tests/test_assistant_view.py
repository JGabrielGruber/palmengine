"""Tests for assistant operator view shaping."""

from __future__ import annotations

from palm.common.operator.view_registry import (
    OperatorViewContext,
    build_operator_view,
    clear_operator_view_builders,
)
from palm.services.assist.registry import (
    clear_assist_contributors,
    register_assistant_enricher,
)
from palm.services.assist.views import build_assistant_view, ensure_assist_view_registration


def _operator_entry_flat() -> dict:
    return {
        "session_id": "inst-1",
        "instance_id": "inst-1",
        "job_id": "job-1",
        "flow_name": "palm-operator-entry",
        "status": "WAITING_FOR_INPUT",
        "current_step_slug": "intent",
        "prompt": {
            "step": "intent",
            "title": "Operator Intent",
            "text": "What would you like to do with Palm?",
            "field_type": "choice",
            "step_kind": "input",
            "choices": ["todo-builder", "compositional-parent", "inspect-only"],
        },
        "answers": {},
    }


def _setup() -> None:
    clear_operator_view_builders()
    clear_assist_contributors()
    ensure_assist_view_registration()


def test_assistant_view_choice_humanize() -> None:
    _setup()
    ctx = OperatorViewContext(
        session_id="inst-1",
        flow_id="flow-palm-operator-entry",
        scenario_id="operator-entry",
    )
    payload = build_assistant_view(_operator_entry_flat(), context=ctx)

    assert payload["session_id"] == "inst-1"
    assert payload["scenario_id"] == "operator-entry"
    assert payload["status"] == "waiting"
    assert payload["question"] == "What would you like to do with Palm?"
    assert payload["hint"] == "Reply with a number or choice name."
    assert payload["compose"]["step"] == "intent"
    assert payload["refs"] == {
        "job_id": "job-1",
        "flow_id": "flow-palm-operator-entry",
    }
    assert payload["choices"] == [
        {"n": 1, "label": "Todo Builder", "value": "todo-builder"},
        {"n": 2, "label": "Compositional Parent", "value": "compositional-parent"},
        {"n": 3, "label": "Inspect Only", "value": "inspect-only"},
    ]
    assert "operator_hint" not in payload
    assert "step_kind" not in payload


def test_assistant_view_child_wait() -> None:
    _setup()
    flat = {
        "instance_id": "inst-parent",
        "status": "WAITING_FOR_INPUT",
        "current_step_slug": "child_step",
        "prompt": {
            "text": "Parent prompt",
            "waiting_for_child": True,
            "waiting_for_child_instance_id": "inst-child",
            "child_status": "WAITING_FOR_INPUT",
        },
    }
    payload = build_assistant_view(
        flat,
        context=OperatorViewContext(session_id="inst-parent"),
    )

    assert payload["question"] == "Waiting for nested flow to finish."
    assert "child session" in payload["hint"]
    assert payload["compose"]["active_child"]["instance_id"] == "inst-child"
    assert payload["compose"]["active_child"]["status"] == "waiting"


def test_assistant_view_collection_menu_hint() -> None:
    _setup()
    flat = {
        "instance_id": "inst-1",
        "status": "WAITING_FOR_INPUT",
        "prompt": {
            "text": "Collection menu",
            "collection_phase": "menu",
            "field_type": "choice",
        },
    }
    payload = build_assistant_view(flat, context=OperatorViewContext(session_id="inst-1"))
    assert payload["hint"] == "Say add, edit, remove, or done."


def test_assistant_view_handoff_ready_hint() -> None:
    _setup()
    payload = build_assistant_view(
        _operator_entry_flat(),
        context=OperatorViewContext(
            session_id="inst-1",
            handoff_ready=True,
        ),
    )
    assert payload["handoff_ready"] is True
    assert "hand off" in payload["hint"].lower()


def test_assistant_enricher_runs() -> None:
    _setup()

    def enrich_operator_entry(view: dict, *, context: OperatorViewContext) -> dict:
        view = dict(view)
        view["hint"] = "Custom hint from contributor."
        return view

    register_assistant_enricher("operator-entry", enrich_operator_entry)
    payload = build_assistant_view(
        _operator_entry_flat(),
        context=OperatorViewContext(session_id="inst-1", scenario_id="operator-entry"),
    )
    assert payload["hint"] == "Custom hint from contributor."


def test_build_operator_view_assistant_format() -> None:
    _setup()
    payload = build_operator_view(
        "assistant",
        flat_view=_operator_entry_flat(),
        context=OperatorViewContext(session_id="inst-1", scenario_id="operator-entry"),
    )
    assert payload["question"] == "What would you like to do with Palm?"
    assert payload["choices"][0]["n"] == 1


def test_assist_service_registers_assistant_format() -> None:
    from palm.services.assist.service import AssistService

    clear_operator_view_builders()
    clear_assist_contributors()

    class _Bus:
        pass

    svc = AssistService(
        commands=_Bus(),
        queries=_Bus(),
        schemas=_Bus(),
        definitions=object(),  # type: ignore[arg-type]
        execution=object(),  # type: ignore[arg-type]
        system=object(),  # type: ignore[arg-type]
    )
    del svc

    payload = build_operator_view(
        "assistant",
        flat_view=_operator_entry_flat(),
        context=OperatorViewContext(session_id="inst-1"),
    )
    assert "question" in payload