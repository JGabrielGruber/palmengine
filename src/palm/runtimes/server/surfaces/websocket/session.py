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
    del headers  # reserved for auth in 0.32.3
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
            "ops": ["hello", "ping", "dispatch"],
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

        response = handle_client_message(message, ctx=ctx)
        if response is None:
            continue
        _send_json(wfile, response)


def handle_client_message(
    message: dict[str, Any],
    *,
    ctx: ServerContext | None = None,
) -> dict[str, Any] | None:
    """Handle one client JSON message; return server frame or None."""
    op = message.get("op")
    msg_id = message.get("id")

    if op == "hello":
        return {
            "op": "hello",
            "id": msg_id,
            "protocol": PROTOCOL_VERSION,
            "server": "palm",
            "version": _palm_version(),
            "channel": "assist",
            "ack": True,
            "client": message.get("client"),
            "ops": ["hello", "ping", "dispatch"],
        }

    if op == "ping":
        return {"op": "pong", "id": msg_id}

    if op == "dispatch":
        return _handle_dispatch(message, ctx=ctx)

    return {
        "op": "error",
        "id": msg_id,
        "error": {
            "code": "unknown_op",
            "message": f"unknown op {op!r}",
        },
    }


def _handle_dispatch(
    message: dict[str, Any],
    *,
    ctx: ServerContext | None,
) -> dict[str, Any]:
    """Run assist meta-dispatch (same spine as MCP palm_assist) → turn/error."""
    msg_id = message.get("id")
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
        shaped = shape_dispatch_result(
            resolved,
            raw,
            format=view_format,
            params=dispatch_params,
            tool_format=view_format,
        )
        shaped = _rewrite_actions_for_websocket(shaped)
        return {
            "op": "turn",
            "id": msg_id,
            "payload": shaped,
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
