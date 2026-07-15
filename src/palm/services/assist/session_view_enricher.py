"""
Assist session-view enricher — blends scenario-aware CTAs onto a flows-path turn.

Registered into the common session-view registry on package import (see
``palm.services.assist.__init__``), so ``common`` never imports assist to enrich
a flow session view.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import JobStatus
from palm.services.assist.grammar import command_path
from palm.services.assist.schemas import AssistSessionContext
from palm.services.assist.views import build_assistant_actions, merge_assistant_actions


def merge_assist_session_actions(
    payload: dict[str, Any],
    *,
    session_id: str,
    scenario_id: str,
    handoff_ready: bool,
    status: str,
) -> dict[str, Any]:
    """Blend scenario-aware CTAs onto a flows-path turn (0.32.5)."""
    waiting = status in {
        JobStatus.WAITING_FOR_INPUT.value,
        "waiting",
        "WAITING_FOR_INPUT",
    }
    succeeded = status in {
        JobStatus.SUCCEEDED.value,
        "complete",
        "SUCCEEDED",
        "SUCCESS",
    }
    # handoff_ready already scenario/intent-gated in _handoff_ready_from_flat
    ready = bool(handoff_ready)
    ctx = AssistSessionContext(
        session_id=session_id,
        scenario_id=scenario_id,
        handoff_ready=ready,
        status=JobStatus.SUCCEEDED.value if succeeded else status,
        waiting_for_input=waiting,
    )
    commands: list[list[str]] = [command_path(session_id=session_id)]
    if waiting:
        commands.append(command_path(session_id=session_id, verb="input"))
        commands.append(command_path(session_id=session_id, verb="backtrack"))
        commands.append(command_path(session_id=session_id, verb="resume"))
    if ready:
        commands.append(command_path(session_id=session_id, verb="handoff"))
    commands.append(command_path(session_id=session_id, verb="cancel"))
    ctx.next_commands = commands
    base = build_assistant_actions(ctx)
    existing = payload.get("actions")
    existing_list = existing if isinstance(existing, list) else []
    # Prefer enricher/human CTAs first, then assist verbs
    merged = merge_assistant_actions(existing_list, base)
    out = dict(payload)
    if merged:
        out["actions"] = merged
    if ready:
        out["handoff_ready"] = True
    elif succeeded:
        # Business flow done — clear accidental handoff chrome
        out["handoff_ready"] = False
        if not out.get("actions"):
            out["actions"] = [{"label": "Start operator entry", "alias": "operator-entry/start"}]
    if scenario_id and not out.get("scenario_id"):
        out["scenario_id"] = scenario_id
    return out


__all__ = ["merge_assist_session_actions"]
