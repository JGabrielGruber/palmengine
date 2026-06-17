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

        def log_message(self, format: str, *args: Any) -> None:
            return None

        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def do_PUT(self) -> None:
            self._dispatch("PUT")

        def do_PATCH(self) -> None:
            self._dispatch("PATCH")

        def do_DELETE(self) -> None:
            self._dispatch("DELETE")

        def _dispatch(self, method: str) -> None:
            parsed = urlparse(self.path)
            query = {key: values[-1] for key, values in parse_qs(parsed.query).items() if values}
            body, body_error = _read_json_body(self)
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
            self._write_json(response.status, response.body, extra_headers=response.headers)

        def _write_json(
            self,
            status: int,
            payload: dict[str, Any],
            *,
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for key, value in (extra_headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

    return StdlibHttpHandler


def _read_json_body(handler: BaseHTTPRequestHandler) -> tuple[dict[str, Any] | None, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return None, None
    try:
        raw = handler.rfile.read(length)
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, error_response(400, "invalid_json", str(exc))
    if not isinstance(data, dict):
        return None, error_response(400, "invalid_request", "JSON object required")
    return data, None