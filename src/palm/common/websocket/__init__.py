"""Shared WebSocket primitives (RFC6455) for server and provider clients."""

from palm.common.websocket.frames import (
    OP_CLOSE,
    OP_PING,
    OP_PONG,
    OP_TEXT,
    WS_GUID,
    FrameReader,
    encode_client_close,
    encode_client_ping,
    encode_client_text,
    encode_close,
    encode_frame,
    encode_pong,
    encode_text,
    is_websocket_upgrade,
    websocket_accept_key,
)

__all__ = [
    "FrameReader",
    "OP_CLOSE",
    "OP_PING",
    "OP_PONG",
    "OP_TEXT",
    "WS_GUID",
    "encode_client_close",
    "encode_client_ping",
    "encode_client_text",
    "encode_close",
    "encode_frame",
    "encode_pong",
    "encode_text",
    "is_websocket_upgrade",
    "websocket_accept_key",
]