"""
Stdlib HTTP transport — zero-dependency threading server for :class:`ServerApp`.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from palm.common.runtimes.server.protocol import ServerRequest
from palm.common.runtimes.server.responses import error_response

if TYPE_CHECKING:
    from palm.common.runtimes.server.app import ServerApp


class StdlibHttpTransport:
    """Threading stdlib HTTP binding implementing :class:`~palm.common.runtimes.server.transport.BaseTransport`."""

    name = "stdlib"

    def __init__(self, app: ServerApp, host: str, port: int) -> None:
        self._app = app
        self._host = host
        self._port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def host(self) -> str:
        if self._server is not None:
            return str(self._server.server_address[0])
        return self._host

    @property
    def port(self) -> int:
        if self._server is not None:
            return int(self._server.server_address[1])
        return self._port

    def start(self, *, blocking: bool = False) -> None:
        if self._server is not None:
            return
        self._server = ThreadingHTTPServer((self._host, self._port), _build_handler(self._app))
        if blocking:
            self._server.serve_forever()
            return
        thread = threading.Thread(
            target=self._server.serve_forever,
            name="StdlibHttpTransport",
            daemon=True,
        )
        thread.start()
        self._thread = thread

    def stop(self) -> None:
        server = self._server
        if server is None:
            return
        server.shutdown()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
        self._server = None
        self._thread = None


def create_stdlib_transport(app: ServerApp, host: str, port: int) -> StdlibHttpTransport:
    """Factory registered on :data:`~palm.common.runtimes.server.transport.transport_registry`."""
    return StdlibHttpTransport(app, host, port)


def serve_app(
    app: ServerApp,
    *,
    host: str,
    port: int,
) -> StdlibHttpTransport:
    """Backward-compatible helper — create and start a stdlib transport."""
    transport = StdlibHttpTransport(app, host, port)
    transport.start()
    return transport


def _build_handler(app: ServerApp) -> type[BaseHTTPRequestHandler]:
    class StdlibHttpHandler(BaseHTTPRequestHandler):
        server: ThreadingHTTPServer
        # RFC6455 WebSocket opening handshake requires HTTP/1.1+.
        # Python default is HTTP/1.0 — strict clients (YAAK, some proxies) reject it.
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:
            return None

        def do_GET(self) -> None:
            if self._try_websocket_upgrade():
                return
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def do_PUT(self) -> None:
            self._dispatch("PUT")

        def do_PATCH(self) -> None:
            self._dispatch("PATCH")

        def do_DELETE(self) -> None:
            self._dispatch("DELETE")

        def _try_websocket_upgrade(self) -> bool:
            """0.32.1 — handle WebSocket upgrade for Assist channel.

            Proxies (Cloudflare Tunnel) may send mixed-case header names.
            Always resolve handshake fields case-insensitively.
            """
            from palm.runtimes.server.surfaces.websocket.frames import (
                is_websocket_upgrade,
                websocket_accept_key,
            )
            from palm.runtimes.server.surfaces.websocket.session import (
                ASSIST_WS_PATH,
                run_assist_websocket,
            )

            # Preserve original pairs for session; use lower map for decisions
            headers = {key: value for key, value in self.headers.items()}
            lower = {str(k).lower(): str(v) for k, v in headers.items()}
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            target = ASSIST_WS_PATH.rstrip("/") or "/"
            if path != target:
                return False
            # Prefer lower-map check so SEC-WEBSOCKET-KEY / Connection: Upgrade work
            upgrade_ok = (
                "websocket" in lower.get("upgrade", "").lower()
                and "upgrade" in lower.get("connection", "").lower()
                and bool(lower.get("sec-websocket-key", "").strip())
            )
            if not upgrade_ok and not is_websocket_upgrade(headers):
                return False

            key = (lower.get("sec-websocket-key") or "").strip()
            if not key:
                return False

            accept = websocket_accept_key(key)
            self.send_response(101, "Switching Protocols")
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.send_header("Sec-WebSocket-Accept", accept)
            # Avoid accidental Content-Length on 101 (some proxies mishandle it)
            self.end_headers()

            ctx = getattr(app, "context", None)
            try:
                run_assist_websocket(
                    rfile=self.rfile,
                    wfile=self.wfile,
                    ctx=ctx,
                    headers=headers,
                )
            except Exception:
                pass
            return True

        def _dispatch(self, method: str) -> None:
            parsed = urlparse(self.path)
            query = {key: values[-1] for key, values in parse_qs(parsed.query).items() if values}
            body, body_error = _read_request_body(self)
            request = ServerRequest(
                method=method,
                path=parsed.path,
                headers={key: value for key, value in self.headers.items()},
                body=body,
                query=query,
            )
            if body_error is not None:
                response = body_error
            else:
                response = app.dispatch(request)
            self._write_response(response)

        def _write_response(self, response: Any) -> None:
            if response.raw_body is not None:
                body = response.raw_body
                content_type = response.content_type
            else:
                body = json.dumps(response.body).encode("utf-8")
                content_type = response.content_type
            self.send_response(response.status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for key, value in response.headers.items():
                if key.lower() != "content-type":
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

    return StdlibHttpHandler


def _read_request_body(handler: BaseHTTPRequestHandler) -> tuple[dict[str, Any] | None, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return None, None
    raw = handler.rfile.read(length)
    content_type = handler.headers.get("Content-Type", "").lower()
    if "application/x-www-form-urlencoded" in content_type:
        return _read_form_body(raw), None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, error_response(400, "invalid_json", str(exc))
    if not isinstance(data, dict):
        return None, error_response(400, "invalid_request", "JSON object required")
    return data, None


def _read_form_body(raw: bytes) -> dict[str, Any]:
    from urllib.parse import parse_qs

    parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}
