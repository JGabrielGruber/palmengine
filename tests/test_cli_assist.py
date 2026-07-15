"""CLI assist commands — assistant envelope rendering and REPL integration."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from palm.runtimes.cli.commands.registry import build_registry
from palm.runtimes.cli.tui.display import render_assistant_panel
from palm.runtimes.cli.tui.repl import dispatch_repl_line


def test_assist_list_includes_operator_entry(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "assist list") == 0


def test_assist_start_operator_entry_sets_active_session(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "assist start operator-entry") == 0
    assert cli_ctx.active_assist_session_id is not None
    assert cli_ctx.active_assist_scenario_id == "operator-entry"


def test_assist_start_returns_assistant_shape_not_powertool(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "assist start operator-entry")
    session_id = cli_ctx.active_assist_session_id
    assert session_id is not None

    view = (
        cli_ctx.host.assist.session(session_id)
        .context(view_format="assistant")
        .to_dict(view_format="assistant")
    )
    assert view.get("question")
    assert view.get("choices")
    assert view.get("status") == "waiting"
    assert "operator_hint" not in view


def test_assist_input_advances_session(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "assist start operator-entry")
    assert reg.dispatch(cli_ctx, "assist input todo-builder") == 0


def test_assist_handoff_after_operator_entry(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "assist start operator-entry")
    reg.dispatch(cli_ctx, "assist input todo-builder")
    updated = (
        cli_ctx.host.assist.session(cli_ctx.active_assist_session_id)
        .context(view_format="assistant")
        .to_dict(view_format="assistant")
    )
    if updated.get("status") == "waiting":
        reg.dispatch(cli_ctx, "assist input yes")

    assert reg.dispatch(cli_ctx, "assist handoff") == 0
    handoff = cli_ctx.host.assist.handoff(cli_ctx.active_assist_session_id)
    assert handoff["handoff"]["kind"] == "flow"
    assert handoff["handoff"]["flow_id"] == "todo-builder"


def test_render_assistant_panel_shows_question_and_choices() -> None:
    output = StringIO()
    console = Console(file=output, width=120, force_terminal=True)
    render_assistant_panel(
        console,
        {
            "session_id": "inst-test",
            "scenario_id": "operator-entry",
            "status": "waiting",
            "question": "What would you like to do with Palm?",
            "choices": [
                {"n": 1, "label": "Build a todo flow", "value": "todo-builder"},
            ],
            "hint": "Reply with a number or choice name.",
        },
    )
    text = output.getvalue()
    assert "What would you like to do with Palm?" in text
    assert "Build a todo flow" in text
    assert "operator_hint" not in text


def test_repl_plain_input_routes_to_assist_input(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "assist start operator-entry")
    assert reg.matches_command("assist input todo-builder") is True
    assert reg.matches_command("todo-builder") is False
    assert dispatch_repl_line(cli_ctx, reg, "todo-builder") == 0


def test_assist_status_powertool_format(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "assist start operator-entry")
    assert reg.dispatch(cli_ctx, "assist status --format powertool") == 0


def test_assist_cancel_clears_active_session(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "assist start operator-entry")
    assert cli_ctx.active_assist_session_id is not None
    assert reg.dispatch(cli_ctx, "assist cancel") == 0
    assert cli_ctx.active_assist_session_id is None