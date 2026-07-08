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
from palm.services.assist.schemas import build_assist_session_context
from palm.services.assist.views import (
    build_assistant_actions,
    build_assistant_view,
    ensure_assist_view_registration,
)


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


def test_assistant_view_collection_menu_actions() -> None:
    _setup()
    flat = {
        "instance_id": "inst-1",
        "flow_name": "todo-builder",
        "status": "WAITING_FOR_INPUT",
        "prompt": {
            "text": "Manage your todos",
            "collection_phase": "menu",
            "field_type": "choice",
            "step_kind": "collection",
            "choices": ["Add a new item", "Continue to summary"],
        },
    }
    payload = build_assistant_view(
        flat,
        context=OperatorViewContext(session_id="inst-1", flow_id="todo-builder"),
    )
    actions = payload.get("actions") or []
    labels = [entry["label"] for entry in actions]
    assert "Add item" in labels
    assert "Add titled item" in labels
    assert actions[0].get("alias") == "flows/session-input"


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


def test_assistant_actions_from_next_commands() -> None:
    _setup()
    ctx = build_assist_session_context(
        session_id="inst-1",
        flow_id="flow-palm-operator-entry",
        view=_operator_entry_flat(),
        scenario_id="operator-entry",
        handoff_ready=False,
    )
    actions = build_assistant_actions(ctx)
    labels = [action["label"] for action in actions]
    assert "Inspect session" in labels
    assert "Send answer" in labels
    assert "Go back" in labels
    assert "Cancel session" in labels
    assert all("operator_hint" not in action for action in actions)


def test_assistant_to_dict_includes_actions() -> None:
    _setup()
    ctx = build_assist_session_context(
        session_id="inst-1",
        flow_id="flow-palm-operator-entry",
        view=_operator_entry_flat(),
        scenario_id="operator-entry",
    )
    payload = ctx.to_dict(view_format="assistant")
    assert "actions" in payload
    assert payload["actions"][0]["path"][0] == "assist"


def test_waiting_turn_gets_send_answer_cta() -> None:
    _setup()
    payload = build_assistant_view(
        _operator_entry_flat(),
        context=OperatorViewContext(
            session_id="inst-1",
            flow_id="flow-palm-operator-entry",
        ),
    )
    assert payload["status"] == "waiting"
    assert payload.get("question")
    actions = payload.get("actions") or []
    assert any(
        a.get("label") == "Send answer" and a.get("tool") == "palm_assist"
        for a in actions
        if isinstance(a, dict)
    )


def test_complete_turn_gets_finished_blurb_and_run_again() -> None:
    _setup()
    flat = {
        "session_id": "inst-done",
        "instance_id": "inst-done",
        "job_id": "job-done",
        "flow_name": "foo-bar",
        "status": "SUCCEEDED",
        "current_step_slug": None,
        "prompt": {},
        "answers": {"foo": "alpha", "bar": "beta"},
    }
    payload = build_assistant_view(
        flat,
        context=OperatorViewContext(session_id="inst-done", flow_id="foo-bar"),
    )
    assert payload["status"] == "complete"
    assert "Finished" in str(payload.get("question") or "")
    assert "alpha" in str(payload.get("question") or "") or "foo" in str(
        payload.get("question") or ""
    )
    assert "complete" in str(payload.get("hint") or "").lower()
    labels = [a.get("label") for a in payload.get("actions") or [] if isinstance(a, dict)]
    assert "Run again" in labels
    assert "Start operator entry" in labels


def test_resource_error_surfaces_resume_actions() -> None:
    _setup()
    from palm.services.assist.views import build_assistant_view

    flat = {
        "session_id": "inst-res-1",
        "instance_id": "inst-res-1",
        "status": "WAITING_FOR_INPUT",
        "flow_name": "coconut-npc",
        "prompt": {
            "title": "Load",
            "prompt": "load failed",
            "step": "load_player",
            "step_kind": "resource",
            "resource_error": "resource not found",
            "resource_remediation": "Register the resource or run palm_system_doctor.",
        },
        "step_kind": "resource",
        "resource_error": "resource not found",
        "resource_remediation": "Register the resource or run palm_system_doctor.",
    }
    payload = build_assistant_view(
        flat,
        context=OperatorViewContext(
            session_id="inst-res-1",
            flow_id="coconut-npc",
        ),
    )
    assert "resource_error" in payload or "Register" in str(payload.get("hint") or "")
    tools = {a.get("tool") for a in payload.get("actions") or []}
    assert "palm_flows_session_resume" in tools
    assert "palm_system_doctor" in tools


def test_to_dict_merges_design_actions_for_create_flow_intent() -> None:
    _setup()
    from palm.services.assist.views import merge_assistant_actions

    merged = merge_assistant_actions(
        [{"label": "Send answer", "path": ["assist", "session", "x", "input"]}],
        [{"label": "Propose new flow", "tool": "palm_design_propose_flow"}],
        [{"label": "Propose new flow", "tool": "palm_design_propose_flow"}],
    )
    assert len(merged) == 2

    view = {
        **_operator_entry_flat(),
        "answers": {"intent": "create-flow"},
        "status": "WAITING_FOR_INPUT",
        "prompt": {"step_kind": "summary", "title": "Summary"},
    }
    ctx = build_assist_session_context(
        session_id="inst-1",
        flow_id="flow-palm-operator-entry",
        view=view,
        scenario_id="operator-entry",
        handoff_ready=True,
    )
    payload = ctx.to_dict(view_format="assistant")
    tools = {a.get("tool") for a in payload.get("actions") or []}
    assert "palm_design_publish_flow" in tools


def test_assistant_handoff_action_uses_alias() -> None:
    _setup()
    from palm.services.assist.registry import AssistContributor, register_assist_contributor

    register_assist_contributor(
        AssistContributor(
            contributor_id="test",
            scenario_id="operator-entry",
            flow_id="flow-palm-operator-entry",
            mcp_aliases=(
                ("operator-entry/handoff", ("assist", "session", "{session_id}", "handoff")),
            ),
        )
    )
    ctx = build_assist_session_context(
        session_id="inst-1",
        flow_id="flow-palm-operator-entry",
        view={**_operator_entry_flat(), "status": "SUCCEEDED"},
        scenario_id="operator-entry",
        handoff_ready=True,
    )
    actions = build_assistant_actions(ctx)
    handoff_actions = [a for a in actions if "hand" in a["label"].lower()]
    assert handoff_actions
    assert handoff_actions[0].get("alias") == "operator-entry/handoff"
    assert handoff_actions[0]["params"] == {"session_id": "inst-1"}


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