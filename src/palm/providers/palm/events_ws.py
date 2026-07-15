"""Native WebSocket client for Palm ``/ws/v1/events`` (0.42.3).

Stdlib only (RFC6455). Complements :class:`PalmEventsClient` (HTTP journal poll).
"""

from __future__ import annotations

import base64
import json
import os
import socket
import ssl
import threading
import time
from typing import Any, Callable, Iterator
from urllib.parse import urlparse

from palm.common.websocket.frames import (
    OP_CLOSE,
    OP_PING,
    OP_PONG,
    OP_TEXT,
    FrameReader,
    encode_client_close,
    encode_client_ping,
    encode_client_text,
    encode_pong,
)

EVENTS_PATH = "/ws/v1/events"


def http_base_to_ws_url(base_url: str, *, path: str = EVENTS_PATH) -> str:
    """``http://host:8080`` → ``ws://host:8080/ws/v1/events``."""
    raw = str(base_url).rstrip("/")
    if raw.startswith("https://"):
        return "wss://" + raw[len("https://") :] + path
    if raw.startswith("http://"):
        return "ws://" + raw[len("http://") :] + path
    if raw.startswith("ws://") or raw.startswith("wss://"):
        parsed = urlparse(raw)
        if parsed.path and parsed.path not in {"", "/"}:
            return raw
        return raw.rstrip("/") + path
    return "ws://" + raw + path


class PalmEventsWebSocketClient:
    """Subscribe to live (+ optional journal catch-up) events on an origin Palm."""

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        subject: str = "dev",
        connect_timeout: float = 10.0,
        path: str = EVENTS_PATH,
    ) -> None:
        self.ws_url = http_base_to_ws_url(base_url, path=path)
        self.token = token
        self.subject = subject
        self.connect_timeout = connect_timeout
        self._sock: socket.socket | None = None
        self._rfile: Any = None
        self._reader: FrameReader | None = None
        self._lock = threading.Lock()
        self._hello: dict[str, Any] | None = None
        self._subscribed: dict[str, Any] | None = None
        self._pending: list[dict[str, Any]] = []
        self._closed = False

    @property
    def hello(self) -> dict[str, Any] | None:
        return self._hello

    @property
    def subscribed(self) -> dict[str, Any] | None:
        return self._subscribed

    @property
    def connected(self) -> bool:
        return self._sock is not None and not self._closed

    def connect(self) -> dict[str, Any]:
        """Open WebSocket; return hello frame body."""
        if self._sock is not None:
            return self._hello or {}
        parsed = urlparse(self.ws_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        path = parsed.path or EVENTS_PATH
        if parsed.query:
            path = f"{path}?{parsed.query}"

        raw = socket.create_connection((host, port), timeout=self.connect_timeout)
        if parsed.scheme == "wss":
            ctx = ssl.create_default_context()
            raw = ctx.wrap_socket(raw, server_hostname=host)
        raw.settimeout(self.connect_timeout)

        key = base64.b64encode(os.urandom(16)).decode("ascii")
        headers = [
            f"GET {path} HTTP/1.1",
            f"Host: {host}:{port}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key}",
            "Sec-WebSocket-Version: 13",
            f"X-Palm-Subject: {self.subject}",
        ]
        if self.token:
            headers.append(f"Authorization: Bearer {self.token}")
        headers.append("")
        headers.append("")
        raw.sendall("\r\n".join(headers).encode("utf-8"))

        # Read HTTP response status line + headers
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = raw.recv(4096)
            if not chunk:
                raw.close()
                raise ConnectionError("websocket handshake closed early")
            buf += chunk
            if len(buf) > 65536:
                raw.close()
                raise ConnectionError("websocket handshake response too large")
        head, rest = buf.split(b"\r\n\r\n", 1)
        status_line = head.split(b"\r\n", 1)[0].decode("latin-1", errors="replace")
        if "101" not in status_line:
            raw.close()
            raise ConnectionError(f"websocket upgrade failed: {status_line!r}")

        # leftover bytes after headers are start of WS frames
        self._sock = raw
        self._rfile = raw.makefile("rb")
        if rest:
            # push leftover into a wrapper — simplest: put on socket buffer via unread
            # Use a tee buffer reader
            self._rfile = _PrefixedReader(rest, self._rfile)
        self._reader = FrameReader(self._rfile)
        self._closed = False

        hello = self._recv_json(timeout=self.connect_timeout)
        if not isinstance(hello, dict) or hello.get("op") != "hello":
            self.close()
            raise ConnectionError(f"expected hello frame, got {hello!r}")
        self._hello = hello
        return hello

    def subscribe(
        self,
        *,
        types: list[str] | None = None,
        since_offset: int | None = 0,
        sub_id: str = "1",
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Send subscribe; return ``subscribed`` frame (catch-up may already be queued)."""
        self.connect()
        body: dict[str, Any] = {"op": "subscribe", "id": sub_id}
        if types is not None:
            body["types"] = list(types)
        if since_offset is not None:
            body["since_offset"] = int(since_offset)
        if limit is not None:
            body["limit"] = int(limit)
        self._send_json(body)
        self._pending = []
        deadline = time.monotonic() + self.connect_timeout
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            msg = self._recv_json(timeout=remaining)
            if not isinstance(msg, dict):
                continue
            op = msg.get("op")
            if op == "error":
                raise ConnectionError(f"subscribe error: {msg}")
            if op == "event":
                self._pending.append(msg)
                continue
            if op == "subscribed":
                self._subscribed = msg
                return msg
        raise ConnectionError("timeout waiting for subscribed")

    def events(
        self,
        *,
        timeout: float | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield ``event`` frames until close/timeout (None = block)."""
        while self._pending:
            yield self._pending.pop(0)
        deadline = None if timeout is None else time.monotonic() + timeout
        while not self._closed:
            remaining = None
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
            try:
                msg = self._recv_json(timeout=remaining)
            except TimeoutError:
                return
            except ConnectionError:
                return
            if not isinstance(msg, dict):
                continue
            op = msg.get("op")
            if op == "event":
                yield msg
            elif op == "error":
                yield msg
            elif op == "pong":
                continue

    def wait_for(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Read events until *predicate* matches."""
        for ev in self.events(timeout=timeout):
            if ev.get("op") == "event" and predicate(ev):
                return ev
        raise TimeoutError("no matching websocket event")

    def ping(self) -> None:
        self._ensure()
        assert self._sock is not None
        with self._lock:
            self._sock.sendall(encode_client_ping())

    def close(self) -> None:
        self._closed = True
        sock = self._sock
        self._sock = None
        self._reader = None
        if sock is None:
            return
        try:
            sock.sendall(encode_client_close())
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass

    def __enter__(self) -> PalmEventsWebSocketClient:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _ensure(self) -> None:
        if self._sock is None or self._reader is None:
            raise ConnectionError("not connected")

    def _send_json(self, obj: dict[str, Any]) -> None:
        self._ensure()
        assert self._sock is not None
        data = encode_client_text(json.dumps(obj, default=str))
        with self._lock:
            self._sock.sendall(data)

    def _recv_json(self, *, timeout: float | None) -> dict[str, Any] | None:
        self._ensure()
        assert self._sock is not None and self._reader is not None
        if timeout is not None:
            self._sock.settimeout(max(0.01, float(timeout)))
        else:
            self._sock.settimeout(None)
        while True:
            try:
                opcode, payload = self._reader.read_frame()
            except (TimeoutError, socket.timeout):
                raise TimeoutError("websocket recv timeout") from None
            except ConnectionError:
                self._closed = True
                raise
            if opcode == OP_CLOSE:
                self._closed = True
                raise ConnectionError("websocket closed by peer")
            if opcode == OP_PING:
                with self._lock:
                    self._sock.sendall(encode_pong(payload, mask=True))
                continue
            if opcode == OP_PONG:
                continue
            if opcode != OP_TEXT:
                continue
            try:
                msg = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(msg, dict):
                return msg
            return None


class _PrefixedReader:
    """File-like: yield prefix bytes then delegate to *inner*."""

    def __init__(self, prefix: bytes, inner: Any) -> None:
        self._prefix = prefix
        self._inner = inner

    def read(self, n: int = -1) -> bytes:
        if self._prefix:
            if n < 0 or n >= len(self._prefix):
                out = self._prefix
                self._prefix = b""
                if n < 0:
                    return out + (self._inner.read() or b"")
                rest = self._inner.read(n - len(out))
                return out + (rest or b"")
            out = self._prefix[:n]
            self._prefix = self._prefix[n:]
            return out
        return self._inner.read(n) or b""


__all__ = [
    "EVENTS_PATH",
    "PalmEventsWebSocketClient",
    "http_base_to_ws_url",
]
