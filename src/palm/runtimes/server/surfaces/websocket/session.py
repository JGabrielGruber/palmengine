"""WebSocket Assist session loop — hello / ping / dispatch (0.32.1+).

0.32.1: hello + ping/pong + echo error for unknown ops.
0.32.2: wire ``dispatch`` to assist services.
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
        }

    if op == "ping":
        return {"op": "pong", "id": msg_id}

    if op == "dispatch":
        # 0.32.2 will wire AssistService; 0.32.1 returns not_implemented
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "not_implemented",
                "message": (
                    "dispatch frames land in 0.32.2; "
                    "connection hello/ping are live in 0.32.1"
                ),
            },
        }

    return {
        "op": "error",
        "id": msg_id,
        "error": {
            "code": "unknown_op",
            "message": f"unknown op {op!r}",
        },
    }


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
