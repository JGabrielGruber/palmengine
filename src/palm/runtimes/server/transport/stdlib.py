"""
Stdlib HTTP transport — threading server binding for :class:`ServerApp`.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from palm.common.runtimes.server.protocol import ServerRequest

if TYPE_CHECKING:
    from palm.common.runtimes.server.app import ServerApp


class StdlibHttpServer(ThreadingHTTPServer):
    """Threading HTTP server bound to a :class:`~palm.common.runtimes.server.app.ServerApp`."""

    app: ServerApp

    def __init__(self, server_address: tuple[str, int], app: ServerApp) -> None:
        self.app = app
        super().__init__(server_address, StdlibHttpHandler)


class StdlibHttpHandler(BaseHTTPRequestHandler):
    """Maps stdlib HTTP requests onto :class:`ServerApp` dispatch."""

    server: StdlibHttpServer

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
        request = ServerRequest(
            method=method,
            path=parsed.path,
            headers={key: value for key, value in self.headers.items()},
            body=self._read_json_body(),
            query=query,
        )
        response = self.server.app.dispatch(request)
        self._write_json(response.status, response.body, extra_headers=response.headers)

    def _read_json_body(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return None
        try:
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        return data if isinstance(data, dict) else None

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


def serve_app(
    app: ServerApp,
    *,
    host: str,
    port: int,
) -> StdlibHttpServer:
    """Create a threading HTTP server for the given app (caller starts serve)."""
    return StdlibHttpServer((host, port), app)