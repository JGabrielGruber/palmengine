"""Minimal RFC6455 text-frame codec for Palm WebSocket Assist (0.32.1).

Server→client frames are unmasked. Client→server frames must be masked.
Only text and close/ping/pong control frames are supported.
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
    """True when the request is a WebSocket upgrade handshake."""
    lower = {k.lower(): v for k, v in headers.items()}
    upgrade = lower.get("upgrade", "").lower()
    connection = lower.get("connection", "").lower()
    key = lower.get("sec-websocket-key", "")
    return "websocket" in upgrade and "upgrade" in connection and bool(key)


def encode_frame(payload: bytes | str, *, opcode: int = OP_TEXT) -> bytes:
    """Encode a server→client frame (unmasked)."""
    data = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
    header = bytearray()
    header.append(0x80 | (opcode & 0x0F))  # FIN + opcode
    n = len(data)
    if n < 126:
        header.append(n)
    elif n < (1 << 16):
        header.append(126)
        header.extend(struct.pack("!H", n))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", n))
    return bytes(header) + data


def encode_text(payload: str, *, opcode: int = OP_TEXT) -> bytes:
    """Encode a server→client text frame (unmasked)."""
    return encode_frame(payload, opcode=opcode)


def encode_close(code: int = 1000, reason: str = "") -> bytes:
    body = struct.pack("!H", code) + reason.encode("utf-8")
    return encode_frame(body, opcode=OP_CLOSE)


def encode_pong(payload: bytes = b"") -> bytes:
    return encode_frame(payload, opcode=OP_PONG)


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
    "encode_close",
    "encode_pong",
    "encode_text",
    "is_websocket_upgrade",
    "websocket_accept_key",
]
