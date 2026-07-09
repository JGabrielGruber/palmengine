"""Chat continuity — auto-start demos + skip introduction (profile policy).

Transport (WS) injects dispatch/shape callables so this module stays free of
runtime imports (services must not import runtimes).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from palm.services.assist.profiles.policy import (
    CHAT_AUTO_START_INTENTS,
    wants_auto_continue_intro,
    wants_auto_start,
)
from palm.services.assist.profiles.turn_meta import (
    flow_id_from_turn,
    intent_from_turn,
    is_introduction_turn,
)

logger = logging.getLogger(__name__)

# path + params → raw domain result
DispatchFn = Callable[[list[str], dict[str, Any]], Any]
# path, raw, kwargs → shaped assistant turn
ShapeFn = Callable[..., dict[str, Any]]


def maybe_auto_start_handoff_flow(
    shaped: dict[str, Any],
    params: dict[str, Any],
    *,
    dispatch: DispatchFn,
    shape: ShapeFn,
) -> dict[str, Any] | None:
    """If operator-entry completed with a demo flow intent, start that flow."""
    if not wants_auto_start(params, default=True):
        return None
    status = str(shaped.get("status") or "")
    if status not in {"complete", "SUCCEEDED", "success"}:
        return None
    if not shaped.get("handoff_ready") and not intent_from_turn(shaped):
        return None
    intent = intent_from_turn(shaped)
    if intent not in CHAT_AUTO_START_INTENTS:
        return None
    flow_id = intent
    try:
        raw = dispatch(["flows", flow_id, "create"], {"format": "assistant"})
        session_id = None
        if isinstance(raw, dict):
            session_id = raw.get("session_id") or raw.get("instance_id")
        if session_id:
            inspect_path = ["flows", flow_id, "session", str(session_id)]
            try:
                raw = dispatch(inspect_path, {"format": "assistant"})
                resolved = inspect_path
            except Exception:
                resolved = ["flows", flow_id, "create"]
                logger.debug("auto-start re-inspect failed", exc_info=True)
        else:
            resolved = ["flows", flow_id, "create"]
        next_turn = shape(
            resolved,
            raw,
            format="assistant",
            params={"format": "assistant"},
            tool_format="assistant",
            include_input_schema=True,
        )
        next_turn.setdefault("intro_banner", f"Started {flow_id}.")
        next_turn["handoff_from"] = {
            "session_id": shaped.get("session_id"),
            "scenario_id": shaped.get("scenario_id"),
            "intent": intent,
        }
        next_turn["flow_id"] = flow_id
        refs = next_turn.get("refs")
        if not isinstance(refs, dict):
            refs = {}
            next_turn["refs"] = refs
        refs["flow_id"] = flow_id
        return next_turn
    except Exception:
        logger.debug("auto-start handoff flow failed for %s", flow_id, exc_info=True)
        return None


def maybe_auto_continue_introduction(
    shaped: dict[str, Any],
    params: dict[str, Any],
    *,
    dispatch: DispatchFn,
    shape: ShapeFn,
) -> dict[str, Any] | None:
    """Advance past introduction steps so humans land on real work."""
    if not wants_auto_continue_intro(params, default=True):
        return None
    if str(shaped.get("status") or "") not in {"waiting", "WAITING_FOR_INPUT"}:
        return None
    if not is_introduction_turn(shaped):
        return None
    session_id = shaped.get("session_id") or shaped.get("instance_id")
    flow_id = flow_id_from_turn(shaped)
    if not session_id or not flow_id:
        return None
    banner_parts: list[str] = []
    prior_banner = str(shaped.get("intro_banner") or "").strip()
    if prior_banner:
        banner_parts.append(prior_banner)
    intro_q = str(shaped.get("question") or "").strip()
    if intro_q and intro_q not in banner_parts:
        banner_parts.append(intro_q)
    intro_text = "\n\n".join(banner_parts)
    try:
        input_path = ["flows", str(flow_id), "session", str(session_id), "input"]
        raw = dispatch(
            input_path,
            {"value": "", "format": "assistant", "include_input_schema": True},
        )
        next_turn = shape(
            input_path,
            raw,
            format="assistant",
            params={"format": "assistant", "include_input_schema": True},
            tool_format="assistant",
            include_input_schema=True,
        )
        if intro_text:
            next_turn["intro_banner"] = intro_text
            if not str(next_turn.get("question") or "").strip():
                next_turn["question"] = intro_text
                next_turn.pop("intro_banner", None)
        if shaped.get("handoff_from") and not next_turn.get("handoff_from"):
            next_turn["handoff_from"] = shaped["handoff_from"]
        next_turn.setdefault("flow_id", flow_id)
        refs = next_turn.get("refs")
        if not isinstance(refs, dict):
            refs = {}
            next_turn["refs"] = refs
        refs.setdefault("flow_id", flow_id)
        return next_turn
    except Exception:
        logger.debug("auto-continue introduction failed", exc_info=True)
        return None


def apply_chat_continuity(
    shaped: dict[str, Any],
    params: dict[str, Any],
    *,
    dispatch: DispatchFn,
    shape: ShapeFn,
    rewrite_actions: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run chat policy chain: auto-start → intro continue; optional action rewrite."""
    from palm.services.assist.profiles.actions_chat import rewrite_actions_for_chat

    rewrite = rewrite_actions or rewrite_actions_for_chat
    out = rewrite(shaped)
    chained = maybe_auto_start_handoff_flow(out, params, dispatch=dispatch, shape=shape)
    if chained is not None:
        out = rewrite(chained)
    advanced = maybe_auto_continue_introduction(out, params, dispatch=dispatch, shape=shape)
    if advanced is not None:
        out = rewrite(advanced)
    return out


__all__ = [
    "DispatchFn",
    "ShapeFn",
    "apply_chat_continuity",
    "maybe_auto_continue_introduction",
    "maybe_auto_start_handoff_flow",
]
