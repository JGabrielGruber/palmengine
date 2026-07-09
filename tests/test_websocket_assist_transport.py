"""0.32.1 — WebSocket Assist transport MVP (hello / ping)."""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
from collections.abc import Iterator

import pytest

from palm.runtimes.server.runtime import ServerRuntime
from palm.runtimes.server.surfaces.websocket.frames import (
    OP_TEXT,
    is_websocket_upgrade,
    websocket_accept_key,
)
from palm.runtimes.server.surfaces.websocket.session import (
    ASSIST_WS_PATH,
    PROTOCOL_VERSION,
    handle_client_message,
)


def test_websocket_accept_key_rfc_sample() -> None:
    # RFC 6455 example
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    assert websocket_accept_key(key) == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_is_websocket_upgrade() -> None:
    assert is_websocket_upgrade(
        {
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": "x",
        }
    )
    assert not is_websocket_upgrade({"Upgrade": "websocket"})


def test_handle_client_hello_and_ping() -> None:
    hello = handle_client_message({"op": "hello", "id": "1", "client": "test"})
    assert hello is not None
    assert hello["op"] == "hello"
    assert hello["protocol"] == PROTOCOL_VERSION
    assert hello["ack"] is True

    pong = handle_client_message({"op": "ping", "id": "2"})
    assert pong == {"op": "pong", "id": "2"}

    err = handle_client_message({"op": "dispatch", "id": "3", "params": {}})
    assert err is not None
    assert err["op"] == "error"
    assert err["error"]["code"] == "not_implemented"


def _mask_client_frame(payload: bytes, *, opcode: int = OP_TEXT) -> bytes:
    mask = os.urandom(4)
    header = bytearray()
    header.append(0x80 | opcode)
    n = len(payload)
    if n < 126:
        header.append(0x80 | n)
    elif n < (1 << 16):
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", n))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", n))
    header.extend(mask)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return bytes(header) + masked


def _read_server_frame(sock: socket.socket) -> tuple[int, bytes]:
    b1 = sock.recv(1)
    b2 = sock.recv(1)
    if not b1 or not b2:
        raise ConnectionError("closed")
    opcode = b1[0] & 0x0F
    length = b2[0] & 0x7F
    if length == 126:
        length = struct.unpack("!H", sock.recv(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", sock.recv(8))[0]
    # server frames unmasked
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    return opcode, data


@pytest.fixture
def palm_server() -> Iterator[ServerRuntime]:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def test_websocket_info_route_live(palm_server: ServerRuntime) -> None:
    import urllib.request

    with urllib.request.urlopen(
        f"{palm_server.base_url}/v1/surfaces/websocket",
        timeout=5,
    ) as resp:
        body = json.loads(resp.read().decode())
    assert body["status"] == "live"
    assert body["assist_path"] == ASSIST_WS_PATH
    assert body["protocol"] == PROTOCOL_VERSION


def test_websocket_assist_hello_roundtrip(palm_server: ServerRuntime) -> None:
    h, port = palm_server.host, palm_server.port
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    req = (
        f"GET {ASSIST_WS_PATH} HTTP/1.1\r\n"
        f"Host: {h}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    ).encode("ascii")

    sock = socket.create_connection((h, port), timeout=5)
    try:
        sock.sendall(req)
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        assert b"101" in buf.split(b"\r\n", 1)[0]
        accept_expected = websocket_accept_key(key)
        assert accept_expected.encode() in buf

        opcode, payload = _read_server_frame(sock)
        assert opcode == OP_TEXT
        hello = json.loads(payload.decode())
        assert hello["op"] == "hello"
        assert hello["protocol"] == PROTOCOL_VERSION
        assert hello["channel"] == "assist"

        sock.sendall(_mask_client_frame(json.dumps({"op": "ping", "id": "p1"}).encode()))
        opcode, payload = _read_server_frame(sock)
        pong = json.loads(payload.decode())
        assert pong["op"] == "pong"
        assert pong["id"] == "p1"
    finally:
        sock.close()
