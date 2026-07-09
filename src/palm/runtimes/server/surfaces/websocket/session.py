"""WebSocket Assist session loop — hello / ping / dispatch (0.32.1+).

0.32.1: hello + ping/pong.
0.32.2: ``dispatch`` → same spine as MCP ``palm_assist`` → ``turn`` frames.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from palm.runtimes.server.surfaces.websocket.frames import (
    OP_CLOSE,
    OP_PING,
    OP_PONG,
    OP_TEXT,
    FrameReader,
    encode_close,
    encode_pong,
    encode_text,
)

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = 1
ASSIST_WS_PATH = "/ws/v1/assist"
MAX_MESSAGE_BYTES = 256 * 1024


def run_assist_websocket(
    *,
    rfile: object,
    wfile: object,
    ctx: ServerContext | None = None,
    headers: dict[str, str] | None = None,
) -> None:
    """Blocking assist channel after HTTP upgrade has completed."""
    conn = _ConnectionState(headers=headers or {})
    reader = FrameReader(rfile)
    version = _palm_version()
    _send_json(
        wfile,
        {
            "op": "hello",
            "protocol": PROTOCOL_VERSION,
            "server": "palm",
            "version": version,
            "channel": "assist",
            "path": ASSIST_WS_PATH,
            "ops": ["hello", "ping", "dispatch", "bind"],
            "auth": {"mode": conn.auth_mode, "subject": conn.subject},
        },
    )

    while True:
        try:
            opcode, payload = reader.read_frame()
        except ConnectionError:
            break
        except OSError:
            break

        if opcode == OP_CLOSE:
            try:
                wfile.write(encode_close())  # type: ignore[attr-defined]
                wfile.flush()  # type: ignore[attr-defined]
            except OSError:
                pass
            break
        if opcode == OP_PING:
            try:
                wfile.write(encode_pong(payload))  # type: ignore[attr-defined]
                wfile.flush()  # type: ignore[attr-defined]
            except OSError:
                break
            continue
        if opcode == OP_PONG:
            continue
        if opcode != OP_TEXT:
            _send_json(
                wfile,
                {
                    "op": "error",
                    "id": None,
                    "error": {
                        "code": "unsupported_opcode",
                        "message": f"unsupported websocket opcode {opcode}",
                    },
                },
            )
            continue

        if len(payload) > MAX_MESSAGE_BYTES:
            _send_json(
                wfile,
                {
                    "op": "error",
                    "id": None,
                    "error": {
                        "code": "message_too_large",
                        "message": f"max message size is {MAX_MESSAGE_BYTES} bytes",
                    },
                },
            )
            continue

        try:
            message = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _send_json(
                wfile,
                {
                    "op": "error",
                    "id": None,
                    "error": {"code": "invalid_json", "message": str(exc)},
                },
            )
            continue

        if not isinstance(message, dict):
            _send_json(
                wfile,
                {
                    "op": "error",
                    "id": None,
                    "error": {
                        "code": "invalid_request",
                        "message": "JSON object required",
                    },
                },
            )
            continue

        response = handle_client_message(message, ctx=ctx, conn=conn)
        if response is None:
            continue
        _send_json(wfile, response)


class _ConnectionState:
    """Per-connection bind state (0.32.3 continuity)."""

    def __init__(self, *, headers: dict[str, str]) -> None:
        self.session_id: str | None = None
        self.flow_id: str | None = None
        self.client: str | None = None
        lower = {k.lower(): v for k, v in headers.items()}
        auth = lower.get("authorization", "")
        if auth.lower().startswith("bearer ") and auth[7:].strip():
            self.auth_mode = "bearer"
            self.subject = auth[7:].strip()[:64]
        else:
            self.auth_mode = "open"
            self.subject = lower.get("x-palm-subject") or "anonymous"


def handle_client_message(
    message: dict[str, Any],
    *,
    ctx: ServerContext | None = None,
    conn: _ConnectionState | None = None,
) -> dict[str, Any] | None:
    """Handle one client JSON message; return server frame or None."""
    op = message.get("op")
    msg_id = message.get("id")
    state = conn or _ConnectionState(headers={})

    if op == "hello":
        if message.get("client") is not None:
            state.client = str(message.get("client"))
        # Optional bind on hello for reconnect
        if message.get("session_id"):
            state.session_id = str(message["session_id"])
        if message.get("flow_id"):
            state.flow_id = str(message["flow_id"])
        return {
            "op": "hello",
            "id": msg_id,
            "protocol": PROTOCOL_VERSION,
            "server": "palm",
            "version": _palm_version(),
            "channel": "assist",
            "ack": True,
            "client": state.client or message.get("client"),
            "ops": ["hello", "ping", "dispatch", "bind"],
            "bound": {
                "session_id": state.session_id,
                "flow_id": state.flow_id,
            },
            "auth": {"mode": state.auth_mode},
        }

    if op == "ping":
        return {"op": "pong", "id": msg_id}

    if op == "bind":
        return _handle_bind(message, state)

    if op == "dispatch":
        return _handle_dispatch(message, ctx=ctx, conn=state)

    return {
        "op": "error",
        "id": msg_id,
        "error": {
            "code": "unknown_op",
            "message": f"unknown op {op!r}",
        },
    }


def _handle_bind(
    message: dict[str, Any],
    conn: _ConnectionState,
) -> dict[str, Any]:
    """Bind session_id / flow_id for reconnect continuity (0.32.3)."""
    msg_id = message.get("id")
    if message.get("clear") in (True, "true", "1", 1):
        conn.session_id = None
        conn.flow_id = None
    if "session_id" in message:
        raw_sid = message.get("session_id")
        if raw_sid is None or str(raw_sid).strip() == "":
            conn.session_id = None
        else:
            conn.session_id = str(raw_sid).strip() or None
    if "flow_id" in message:
        raw_fid = message.get("flow_id")
        if raw_fid is None or str(raw_fid).strip() == "":
            conn.flow_id = None
        else:
            conn.flow_id = str(raw_fid).strip() or None
    return {
        "op": "bound",
        "id": msg_id,
        "session_id": conn.session_id,
        "flow_id": conn.flow_id,
    }


def _handle_dispatch(
    message: dict[str, Any],
    *,
    ctx: ServerContext | None,
    conn: _ConnectionState | None = None,
) -> dict[str, Any]:
    """Run assist meta-dispatch (same spine as MCP palm_assist) → turn/error."""
    msg_id = message.get("id")
    state = conn or _ConnectionState(headers={})
    if ctx is None:
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "unavailable",
                "message": "server context not available for dispatch",
            },
        }

    path_raw = message.get("path")
    alias = message.get("alias")
    params = message.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "validation",
                "message": "params must be an object",
            },
        }
    params = dict(params)
    # Allow top-level convenience keys (chat clients)
    for key in ("value", "input", "session_id", "flow_id", "body", "query", "q"):
        if key in message and key not in params:
            params[key] = message[key]
    # 0.32.3 — fill from connection bind when client omits ids
    if not params.get("session_id") and state.session_id:
        params["session_id"] = state.session_id
    if not params.get("flow_id") and state.flow_id:
        params["flow_id"] = state.flow_id
    # 0.32.6 — Portal needs structured input; service builds it when this is set
    params.setdefault("include_input_schema", True)

    path_list: list[str] | None = None
    if isinstance(path_raw, list):
        path_list = [str(p) for p in path_raw]
    elif path_raw is not None:
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "validation",
                "message": "path must be an array of strings",
            },
        }

    try:
        from palm.runtimes.mcp.assist.dispatch import (
            dispatch_operator_path,
            normalize_assist_dispatch_args,
            resolve_dispatch_path,
            shape_dispatch_result,
        )
        from palm.services.assist.views import ensure_assist_view_registration

        ensure_assist_view_registration()
        norm_path, norm_alias, dispatch_params, _used_default = (
            normalize_assist_dispatch_args(
                path=path_list,
                alias=str(alias) if alias is not None else None,
                params=params,
            )
        )
        resolved = resolve_dispatch_path(
            path=norm_path,
            alias=norm_alias,
            params=dispatch_params,
        )
        raw = dispatch_operator_path(ctx, resolved, dispatch_params)
        view_format = str(message.get("format") or "assistant")
        # After create, re-inspect so first turn includes input schema (Portal)
        if (
            view_format == "assistant"
            and len(resolved) >= 2
            and resolved[0] == "flows"
            and resolved[-1] == "create"
            and isinstance(raw, dict)
            and raw.get("session_id")
        ):
            flow_id = resolved[1]
            session_id = str(raw["session_id"])
            inspect_path = ["flows", flow_id, "session", session_id]
            try:
                raw = dispatch_operator_path(
                    ctx,
                    inspect_path,
                    {"format": "assistant"},
                )
                resolved = inspect_path
            except Exception:
                logger.debug("ws create re-inspect failed; using create envelope", exc_info=True)
        shaped = shape_dispatch_result(
            resolved,
            raw,
            format=view_format,
            params=dispatch_params,
            tool_format=view_format,
            include_input_schema=True,  # Portal dynamic widgets (not on MCP)
        )
        shaped = _rewrite_actions_for_websocket(shaped)
        # 0.32.5 — human-first: auto-start demo flow after operator-entry complete
        if view_format == "assistant":
            chained = _maybe_auto_start_handoff_flow(ctx, shaped, dispatch_params)
            if chained is not None:
                shaped = chained
                shaped = _rewrite_actions_for_websocket(shaped)
            # 0.32.8 — skip introduction ack (banner kept on next step)
            advanced = _maybe_auto_continue_introduction(ctx, shaped, dispatch_params)
            if advanced is not None:
                shaped = advanced
                shaped = _rewrite_actions_for_websocket(shaped)
        # Refresh bind from turn payload for reconnect convenience
        sid = shaped.get("session_id") or shaped.get("instance_id")
        if sid:
            state.session_id = str(sid)
        flow = _flow_id_from_turn(shaped)
        if flow:
            state.flow_id = str(flow)
            # Keep refs honest for Portal clients that prefer refs over bound
            refs = shaped.get("refs")
            if not isinstance(refs, dict):
                refs = {}
                shaped["refs"] = refs
            refs.setdefault("flow_id", state.flow_id)
        return {
            "op": "turn",
            "id": msg_id,
            "payload": shaped,
            "bound": {
                "session_id": state.session_id,
                "flow_id": state.flow_id,
            },
        }
    except ValueError as exc:
        return {
            "op": "error",
            "id": msg_id,
            "error": {"code": "validation", "message": str(exc)},
        }
    except Exception as exc:
        logger.exception("websocket assist dispatch failed")
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "internal",
                "message": str(exc) or exc.__class__.__name__,
            },
        }


_PORTAL_NOISE_LABELS = frozenset(
    {
        "send answer",
        "inspect session",
        "resume session",
        "inspect this session",
    }
)


def _rewrite_actions_for_websocket(payload: dict[str, Any]) -> dict[str, Any]:
    """Map peer MCP tool actions to dispatch-friendly alias/params for Portal."""
    actions = payload.get("actions")
    if not isinstance(actions, list):
        return payload
    rewritten: list[dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        item = dict(action)
        label = str(item.get("label") or "").strip()
        # 0.32.5 — drop agent chrome that confuses human chat
        if label.lower() in _PORTAL_NOISE_LABELS:
            continue
        tool = str(item.get("tool") or "")
        # Prefer alias/path already set
        if item.get("alias") or item.get("path"):
            item.pop("tool", None)
            rewritten.append(item)
            continue
        if tool in {"", "palm_assist"}:
            # Keep params for client re-dispatch over WS
            item.pop("tool", None)
            if not item.get("params") and not item.get("alias"):
                continue
            rewritten.append(item)
            continue
        if tool == "palm_flows_create_session":
            params = dict(item.get("params") or {})
            flow_id = params.get("flow_id")
            if flow_id:
                rewritten.append(
                    {
                        "label": item.get("label") or "Run flow",
                        "params": {"flow_id": flow_id},
                    }
                )
            continue
        if tool == "palm_flows_session_resume":
            rewritten.append(
                {
                    "label": item.get("label") or "Resume",
                    "alias": "flows/session-resume",
                    "params": dict(item.get("params") or {}),
                }
            )
            continue
        if tool in {"palm_design_publish_flow", "palm_design_publish_resource"}:
            alias = (
                "design/publish"
                if "flow" in tool
                else "design/publish-resource"
            )
            rewritten.append(
                {
                    "label": item.get("label") or "Publish",
                    "alias": alias,
                    "params": dict(item.get("params") or {}),
                }
            )
            continue
        if tool == "palm_system_doctor":
            rewritten.append(
                {
                    "label": item.get("label") or "Doctor",
                    "alias": "assist/doctor",
                }
            )
            continue
        # Drop unknown peer tools — Portal only speaks dispatch frames
        if tool.startswith("palm_"):
            continue
        rewritten.append(item)
    out = dict(payload)
    if rewritten:
        out["actions"] = rewritten
    elif "actions" in out:
        out.pop("actions", None)
    return out


_DEMO_FLOW_INTENTS = frozenset(
    {"todo-builder", "compositional-parent", "coconut-npc"}
)


def _maybe_auto_start_handoff_flow(
    ctx: object,
    shaped: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, Any] | None:
    """If operator-entry completed with a demo flow intent, start that flow.

    Human-first Portal: pick Todo Builder → land in Todo Builder, not a dead end.
    Opt out with params.auto_start=false.
    """
    if params.get("auto_start") is False:
        return None
    status = str(shaped.get("status") or "")
    if status not in {"complete", "SUCCEEDED", "success"}:
        return None
    if not shaped.get("handoff_ready") and not _intent_from_turn(shaped):
        return None
    intent = _intent_from_turn(shaped)
    if intent not in _DEMO_FLOW_INTENTS:
        return None
    # Prefer explicit Start {flow} action params
    flow_id = intent
    try:
        from palm.runtimes.mcp.assist.dispatch import (
            dispatch_operator_path,
            shape_dispatch_result,
        )

        raw = dispatch_operator_path(
            ctx,
            ["flows", flow_id, "create"],
            {"format": "assistant"},
        )
        # Re-inspect for first-turn input schema
        session_id = None
        if isinstance(raw, dict):
            session_id = raw.get("session_id") or raw.get("instance_id")
        if session_id:
            inspect_path = ["flows", flow_id, "session", str(session_id)]
            try:
                raw = dispatch_operator_path(
                    ctx,
                    inspect_path,
                    {"format": "assistant"},
                )
                resolved = inspect_path
            except Exception:
                resolved = ["flows", flow_id, "create"]
                logger.debug("auto-start re-inspect failed", exc_info=True)
        else:
            resolved = ["flows", flow_id, "create"]
        next_turn = shape_dispatch_result(
            resolved,
            raw,
            format="assistant",
            params={"format": "assistant"},
            tool_format="assistant",
            include_input_schema=True,
        )
        # Soft handoff banner
        prior_q = shaped.get("question")
        if prior_q and not str(next_turn.get("question") or "").startswith("Started"):
            banner = f"Started {flow_id}."
            q = next_turn.get("question")
            next_turn["question"] = f"{banner} {q}".strip() if q else banner
        next_turn["handoff_from"] = {
            "session_id": shaped.get("session_id"),
            "scenario_id": shaped.get("scenario_id"),
            "intent": intent,
        }
        # Ensure bind targets the *business* flow, not operator-entry
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


def _intent_from_turn(shaped: dict[str, Any]) -> str | None:
    summary = shaped.get("answers_summary")
    if isinstance(summary, str) and "intent=" in summary:
        part = summary.split("intent=", 1)[-1].split(",", 1)[0].strip()
        if part:
            return part
    # actions: Start Todo Builder with flow_id
    for action in shaped.get("actions") or []:
        if not isinstance(action, dict):
            continue
        params = action.get("params") or {}
        if isinstance(params, dict) and params.get("flow_id"):
            fid = str(params["flow_id"])
            if fid in _DEMO_FLOW_INTENTS:
                return fid
        label = str(action.get("label") or "").lower()
        if label.startswith("start "):
            for intent in _DEMO_FLOW_INTENTS:
                if intent.replace("-", " ") in label or intent in label:
                    return intent
    compose = shaped.get("compose")
    if isinstance(compose, dict) and compose.get("intent"):
        return str(compose["intent"])
    return None


def _flow_id_from_turn(shaped: dict[str, Any]) -> str | None:
    """Resolve flow id for WS bind — prefer path over sticky operator-entry bind."""
    path = shaped.get("path")
    if isinstance(path, list) and len(path) >= 2 and str(path[0]) == "flows":
        # ["flows", flow_id, "session", …] or ["flows", flow_id, "create"]
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


def _is_introduction_turn(shaped: dict[str, Any]) -> bool:
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


def _maybe_auto_continue_introduction(
    ctx: object,
    shaped: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, Any] | None:
    """Advance past introduction steps so humans land on real work (0.32.8).

    Introduction leaves still wait for input in the wizard engine; empty value
    is a valid ack. Portal should not force "okay" / free text on a welcome.
    Opt out: ``params.auto_continue_intro=false``.
    """
    if params.get("auto_continue_intro") is False:
        return None
    if str(shaped.get("status") or "") not in {"waiting", "WAITING_FOR_INPUT"}:
        return None
    if not _is_introduction_turn(shaped):
        return None
    session_id = shaped.get("session_id") or shaped.get("instance_id")
    flow_id = _flow_id_from_turn(shaped)
    if not session_id or not flow_id:
        return None
    intro_text = str(shaped.get("question") or "").strip()
    try:
        from palm.runtimes.mcp.assist.dispatch import (
            dispatch_operator_path,
            shape_dispatch_result,
        )

        input_path = ["flows", str(flow_id), "session", str(session_id), "input"]
        # Empty string is a valid introduction ack (required=False on step)
        raw = dispatch_operator_path(
            ctx,
            input_path,
            {"value": "", "format": "assistant", "include_input_schema": True},
        )
        next_turn = shape_dispatch_result(
            input_path,
            raw,
            format="assistant",
            params={"format": "assistant", "include_input_schema": True},
            tool_format="assistant",
            include_input_schema=True,
        )
        # Keep welcome copy as a soft banner on the first real step
        if intro_text:
            next_q = str(next_turn.get("question") or "").strip()
            if next_q and intro_text not in next_q:
                next_turn["question"] = f"{intro_text}\n\n{next_q}"
            elif not next_q:
                next_turn["question"] = intro_text
            next_turn["intro_banner"] = intro_text
        # Preserve handoff_from if we chained from operator-entry
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


def _send_json(wfile: object, payload: dict[str, Any]) -> None:
    data = encode_text(json.dumps(payload, separators=(",", ":")))
    wfile.write(data)  # type: ignore[attr-defined]
    wfile.flush()  # type: ignore[attr-defined]


def _palm_version() -> str:
    try:
        from palm import __version__

        return str(__version__)
    except Exception:
        return "unknown"


__all__ = [
    "ASSIST_WS_PATH",
    "PROTOCOL_VERSION",
    "handle_client_message",
    "run_assist_websocket",
]
