"""Minimal RFC6455 text-frame codec for Palm WebSocket surfaces (0.32.1).

Server→client frames are unmasked. Client→server frames must be masked.
Only text and close/ping/pong control frames are supported.

Shared by server transport and palm provider ``PalmEventsWebSocketClient`` (0.43.1).
"""

from __future__ import annotations

import base64
import hashlib
import struct
from typing import Final

WS_GUID: Final[str] = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_CONTINUATION = 0x0
OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA


def websocket_accept_key(sec_websocket_key: str) -> str:
    """Compute ``Sec-WebSocket-Accept`` from the client key."""
    digest = hashlib.sha1((sec_websocket_key.strip() + WS_GUID).encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


def is_websocket_upgrade(headers: dict[str, str]) -> bool:
    """True when the request is a WebSocket upgrade handshake.

    Header names are matched case-insensitively (proxies vary casing).
    ``Connection`` may be a list, e.g. ``keep-alive, Upgrade``.
    """
    lower = {str(k).lower(): str(v) for k, v in headers.items()}
    upgrade = lower.get("upgrade", "").lower()
    connection = lower.get("connection", "").lower()
    key = (lower.get("sec-websocket-key") or "").strip()
    return "websocket" in upgrade and "upgrade" in connection and bool(key)


def encode_frame(
    payload: bytes | str,
    *,
    opcode: int = OP_TEXT,
    mask: bool = False,
) -> bytes:
    """Encode a WebSocket frame. Server→client is unmasked; clients must mask."""
    import os

    data = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
    header = bytearray()
    header.append(0x80 | (opcode & 0x0F))  # FIN + opcode
    n = len(data)
    mask_bit = 0x80 if mask else 0
    if n < 126:
        header.append(mask_bit | n)
    elif n < (1 << 16):
        header.append(mask_bit | 126)
        header.extend(struct.pack("!H", n))
    else:
        header.append(mask_bit | 127)
        header.extend(struct.pack("!Q", n))
    if mask:
        key = os.urandom(4)
        header.extend(key)
        data = bytes(b ^ key[i % 4] for i, b in enumerate(data))
    return bytes(header) + data


def encode_text(payload: str, *, opcode: int = OP_TEXT, mask: bool = False) -> bytes:
    """Encode a text frame (set ``mask=True`` for client→server)."""
    return encode_frame(payload, opcode=opcode, mask=mask)


def encode_client_text(payload: str) -> bytes:
    """Client→server text frame (masked, RFC6455)."""
    return encode_text(payload, mask=True)


def encode_close(code: int = 1000, reason: str = "", *, mask: bool = False) -> bytes:
    body = struct.pack("!H", code) + reason.encode("utf-8")
    return encode_frame(body, opcode=OP_CLOSE, mask=mask)


def encode_client_close(code: int = 1000, reason: str = "") -> bytes:
    return encode_close(code, reason, mask=True)


def encode_pong(payload: bytes = b"", *, mask: bool = False) -> bytes:
    return encode_frame(payload, opcode=OP_PONG, mask=mask)


def encode_client_ping(payload: bytes = b"") -> bytes:
    return encode_frame(payload, opcode=OP_PING, mask=True)


class FrameReader:
    """Incremental reader for one WebSocket frame from a raw socket file."""

    def __init__(self, rfile: object) -> None:
        self._rfile = rfile

    def read_frame(self) -> tuple[int, bytes]:
        """Return ``(opcode, payload)``. Raises ``ConnectionError`` on EOF."""
        b1 = self._read_exact(1)
        b2 = self._read_exact(1)
        opcode = b1[0] & 0x0F
        masked = bool(b2[0] & 0x80)
        length = b2[0] & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(length) if length else b""
        if masked:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        return opcode, payload

    def _read_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self._rfile.read(n - len(buf))  # type: ignore[attr-defined]
            if not chunk:
                raise ConnectionError("websocket peer closed connection")
            buf += chunk
        return buf


__all__ = [
    "FrameReader",
    "OP_CLOSE",
    "OP_PING",
    "OP_PONG",
    "OP_TEXT",
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