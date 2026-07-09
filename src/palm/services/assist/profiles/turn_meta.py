"""Extract intent / flow_id / introduction flags from shaped assist turns."""

from __future__ import annotations

from typing import Any

from palm.services.assist.profiles.policy import CHAT_AUTO_START_INTENTS


def intent_from_turn(shaped: dict[str, Any]) -> str | None:
    summary = shaped.get("answers_summary")
    if isinstance(summary, str) and "intent=" in summary:
        part = summary.split("intent=", 1)[-1].split(",", 1)[0].strip()
        if part:
            return part
    for action in shaped.get("actions") or []:
        if not isinstance(action, dict):
            continue
        params = action.get("params") or {}
        if isinstance(params, dict) and params.get("flow_id"):
            fid = str(params["flow_id"])
            if fid in CHAT_AUTO_START_INTENTS:
                return fid
        label = str(action.get("label") or "").lower()
        if label.startswith("start "):
            for intent in CHAT_AUTO_START_INTENTS:
                if intent.replace("-", " ") in label or intent in label:
                    return intent
    compose = shaped.get("compose")
    if isinstance(compose, dict) and compose.get("intent"):
        return str(compose["intent"])
    return None


def flow_id_from_turn(shaped: dict[str, Any]) -> str | None:
    """Resolve flow id for bind — prefer path over sticky operator-entry bind."""
    path = shaped.get("path")
    if isinstance(path, list) and len(path) >= 2 and str(path[0]) == "flows":
        candidate = str(path[1])
        if candidate and candidate not in {"session", "create"}:
            return candidate
    refs = shaped.get("refs")
    if isinstance(refs, dict) and refs.get("flow_id"):
        return str(refs["flow_id"])
    for key in ("flow_id", "flow"):
        if shaped.get(key):
            return str(shaped[key])
    return None


def is_introduction_turn(shaped: dict[str, Any]) -> bool:
    """True when the active step is a non-interactive welcome/intro."""
    schema = shaped.get("input") if isinstance(shaped.get("input"), dict) else {}
    step_kind = str(schema.get("step_kind") or "").lower()
    if step_kind in {"introduction", "intro"}:
        return True
    compose = shaped.get("compose") if isinstance(shaped.get("compose"), dict) else {}
    step = str(compose.get("step") or schema.get("step") or "").lower()
    if step in {"intro", "introduction", "welcome"}:
        return True
    mutation = shaped.get("mutation") if isinstance(shaped.get("mutation"), dict) else {}
    slug = str(mutation.get("step_slug") or "").lower()
    return slug in {"intro", "introduction", "welcome"}


__all__ = [
    "flow_id_from_turn",
    "intent_from_turn",
    "is_introduction_turn",
]
