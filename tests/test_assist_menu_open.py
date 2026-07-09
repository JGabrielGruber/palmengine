"""0.34 Assist menu / open / design auto-start / confirm choices."""

from __future__ import annotations

from palm.runtimes.mcp.assist.normalize import normalize_assist_dispatch_args, resolve_dispatch_path
from palm.services.assist.catalog.menu import build_menu_page, menu_for_assist
from palm.services.assist.catalog.open import parse_open_token
from palm.services.assist.grammar import AssistCommandKind, parse_assist_command
from palm.services.assist.present.humanize import humanize_assistant_view
from palm.services.assist.profiles.continuity import (
    ensure_design_handoff_actions,
    maybe_auto_start_design_entry,
)
from palm.services.assist.profiles.policy import (
    CHAT_DESIGN_AUTO_START_INTENTS,
)
from palm.common.operator.view_registry import OperatorViewContext


def test_parse_menu_and_open_paths() -> None:
    assert parse_assist_command(["assist", "menu"]).kind == AssistCommandKind.MENU
    assert parse_assist_command(["menu", "flows"]).kind == AssistCommandKind.MENU
    assert parse_assist_command(["assist", "open"]).kind == AssistCommandKind.OPEN
    assert parse_assist_command(["catalog", "open"]).kind == AssistCommandKind.OPEN


def test_aliases_resolve() -> None:
    assert resolve_dispatch_path(alias="assist/menu") == ["assist", "menu"]
    assert resolve_dispatch_path(alias="assist/open") == ["assist", "open"]


def test_open_token_routes_normalize() -> None:
    path, alias, params, _ = normalize_assist_dispatch_args(
        params={
            "value": "open:flow:todo-builder",
            "session_id": "inst-stale",
            "flow_id": "flow-stale",
        }
    )
    assert path == ["assist", "open"]
    assert alias is None
    assert params.get("value") == "open:flow:todo-builder"


def test_parse_open_token() -> None:
    assert parse_open_token("open:flow:todo-builder") == ("flow", "todo-builder")
    assert parse_open_token("yes") is None


def test_build_menu_page_pagination() -> None:
    items = [
        {
            "id": f"f{i}",
            "kind": "flow",
            "label": f"Flow {i}",
            "open": {"kind": "flow", "id": f"f{i}"},
        }
        for i in range(25)
    ]
    page = build_menu_page(section="flows", items=items, limit=10, cursor=0)
    assert page["has_more"] is True
    assert page["next_cursor"] == "10"
    assert len(page["items"]) == 10
    assert page["choices"][0]["value"] == "open:flow:f0"
    assert any(a.get("label") == "Show more" for a in page["actions"])

    page2 = build_menu_page(section="flows", items=items, limit=10, cursor="10")
    assert page2["cursor"] == "10"
    assert page2["items"][0]["id"] == "f10"


def test_menu_search_filters() -> None:
    items = [
        {"id": "todo-builder", "kind": "flow", "label": "Todo", "open": {"kind": "flow", "id": "todo-builder"}},
        {"id": "coconut-npc", "kind": "flow", "label": "Coconut", "open": {"kind": "flow", "id": "coconut-npc"}},
    ]
    page = build_menu_page(section="flows", items=items, query="todo")
    assert page["total"] == 1
    assert page["items"][0]["id"] == "todo-builder"


def test_confirm_choices_injected() -> None:
    composed = {
        "status": "WAITING_FOR_INPUT",
        "field_type": "confirm",
        "step_kind": "summary",
        "step": "summary",
        "prompt": "Confirm?",
        "instance_id": "inst-1",
    }
    view = humanize_assistant_view(
        composed,
        context=OperatorViewContext(
            session_id="inst-1",
            include_input_schema=True,
        ),
    )
    choices = view.get("choices") or []
    values = {c.get("value") for c in choices}
    assert "yes" in values and "no" in values
    assert view.get("input", {}).get("widget") == "confirm"


def test_design_handoff_actions() -> None:
    payload = {
        "status": "complete",
        "answers_summary": "intent=improve-flow",
        "handoff_ready": True,
        "actions": [{"label": "Start operator entry", "alias": "operator-entry/start"}],
        "hint": "Ready to hand off — call assist session handoff or choose continue.",
    }
    out = ensure_design_handoff_actions(payload)
    aliases = [a.get("alias") for a in out.get("actions") or []]
    assert "design-entry/start" in aliases
    assert "call assist" not in str(out.get("hint") or "").lower()


def test_design_auto_start_intent_set() -> None:
    assert "improve-flow" in CHAT_DESIGN_AUTO_START_INTENTS
    assert "create-flow" in CHAT_DESIGN_AUTO_START_INTENTS


def test_browse_menu_actions_on_operator_intent() -> None:
    from palm.services.assist.profiles.actions_chat import ensure_browse_menu_actions

    payload = {
        "status": "waiting",
        "scenario_id": "operator-entry",
        "compose": {"step": "intent"},
        "choices": [{"value": "todo-builder"}, {"value": "improve-flow"}],
        "actions": [{"label": "Cancel session", "path": ["assist", "session", "x", "cancel"]}],
    }
    out = ensure_browse_menu_actions(payload)
    assert any(
        a.get("alias") == "assist/menu" and (a.get("params") or {}).get("section") == "flows"
        for a in out.get("actions") or []
    )


def test_maybe_auto_start_design_entry_chain() -> None:
    calls: list[tuple[list[str], dict]] = []

    def dispatch(path: list[str], params: dict) -> dict:
        calls.append((list(path), dict(params)))
        if path[-1] == "start":
            return {"session_id": "inst-design-1", "status": "waiting", "question": "Design?"}
        if path[-1] == "input":
            return {
                "session_id": "inst-design-1",
                "status": "waiting",
                "question": "Name or base flow?",
                "compose": {"step": "name_or_base"},
            }
        return {"session_id": "inst-design-1"}

    def shape(path, raw, **kwargs):
        out = dict(raw) if isinstance(raw, dict) else {"raw": raw}
        out["path"] = path
        return out

    shaped = {
        "status": "complete",
        "answers_summary": "intent=improve-flow",
        "handoff_ready": True,
        "session_id": "inst-op",
    }
    next_turn = maybe_auto_start_design_entry(
        shaped, {}, dispatch=dispatch, shape=shape
    )
    assert next_turn is not None
    assert next_turn.get("question") == "Name or base flow?"
    assert any(c[0][-1] == "start" for c in calls)
    assert any(c[0][-1] == "input" and c[1].get("value") == "improve-flow" for c in calls)
