"""
Minimal HTTP surface for :class:`~palm.runtimes.server.runtime.ServerRuntime`.

Uses only the stdlib so the server skeleton ships without extra dependencies.
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from palm.core.orchestration.exceptions import JobNotFoundError
from palm.definitions.flow import FlowDefinition

if TYPE_CHECKING:
    from palm.runtimes.server.runtime import ServerRuntime

_JOB_PATH = re.compile(r"^/v1/jobs/(?P<job_id>[^/]+)$")
_JOB_INPUT_PATH = re.compile(r"^/v1/jobs/(?P<job_id>[^/]+)/input$")


class PalmHttpServer(ThreadingHTTPServer):
    """Threading HTTP server bound to a :class:`~palm.runtimes.server.runtime.ServerRuntime`."""

    runtime: ServerRuntime

    def __init__(self, server_address: tuple[str, int], runtime: ServerRuntime) -> None:
        self.runtime = runtime
        super().__init__(server_address, PalmHttpHandler)


class PalmHttpHandler(BaseHTTPRequestHandler):
    """REST-style handler delegating to the hosting runtime."""

    server: PalmHttpServer  # type: ignore[assignment]

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            runtime = self.server.runtime
            self._json(
                200,
                {
                    "status": "ok",
                    "runtime": runtime.runtime_name,
                    "version": runtime.version,
                },
            )
            return

        match = _JOB_PATH.match(path)
        if match is not None:
            self._get_job(match.group("job_id"))
            return

        self._json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/v1/jobs":
            self._submit_job()
            return

        match = _JOB_INPUT_PATH.match(path)
        if match is not None:
            self._provide_input(match.group("job_id"))
            return

        self._json(404, {"error": "not_found", "path": path})

    def _get_job(self, job_id: str) -> None:
        runtime = self.server.runtime
        try:
            job = runtime.get_job(job_id)
        except JobNotFoundError:
            self._json(404, {"error": "job_not_found", "job_id": job_id})
            return

        payload: dict[str, Any] = {
            "job_id": job.id,
            "status": job.status.value,
            "metadata": job.metadata,
        }
        if job.result is not None:
            payload["result"] = job.result
        if job.error is not None:
            payload["error"] = str(job.error)
        step = _safe_wizard_step(runtime, job_id)
        if step is not None:
            payload["step"] = step
        self._json(200, payload)

    def _submit_job(self) -> None:
        body = self._read_json()
        if body is None:
            return

        runtime = self.server.runtime
        try:
            job = self._submit_from_body(body)
        except (TypeError, ValueError, KeyError) as exc:
            self._json(400, {"error": "invalid_request", "detail": str(exc)})
            return
        except Exception as exc:
            self._json(500, {"error": "submit_failed", "detail": str(exc)})
            return

        runtime.wait_until_idle()
        self._json(
            202,
            {
                "job_id": job.id,
                "status": job.status.value,
                "metadata": job.metadata,
            },
        )

    def _submit_from_body(self, body: dict[str, Any]) -> Any:
        runtime = self.server.runtime
        if "flow" in body and isinstance(body["flow"], dict):
            flow = FlowDefinition.from_dict(body["flow"])
            return runtime.submit_flow(flow, job_id=body.get("job_id"))

        if "wizard" in body:
            wizard = body["wizard"]
            if not isinstance(wizard, dict):
                raise TypeError("wizard must be an object")
            steps = wizard.get("steps")
            return runtime.submit_wizard(
                name=str(wizard.get("name", "wizard")),
                steps=int(steps) if steps is not None else None,
                job_id=body.get("job_id"),
            )

        if "flow_name" in body:
            return runtime.submit_flow(
                str(body["flow_name"]),
                by_id=bool(body.get("by_id", False)),
                job_id=body.get("job_id"),
            )

        raise ValueError("expected 'flow', 'wizard', or 'flow_name' in request body")

    def _provide_input(self, job_id: str) -> None:
        body = self._read_json()
        if body is None:
            return
        if "value" not in body:
            self._json(400, {"error": "invalid_request", "detail": "missing 'value'"})
            return

        runtime = self.server.runtime
        try:
            slug = runtime.provide_input(job_id, body["value"])
        except JobNotFoundError:
            self._json(404, {"error": "job_not_found", "job_id": job_id})
            return
        except (TypeError, RuntimeError) as exc:
            self._json(400, {"error": "input_rejected", "detail": str(exc)})
            return

        runtime.wait_until_idle()
        job = runtime.get_job(job_id)
        self._json(
            200,
            {
                "job_id": job_id,
                "slug": slug,
                "status": job.status.value,
                "step": _safe_wizard_step(runtime, job_id),
            },
        )

    def _read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            self._json(400, {"error": "invalid_request", "detail": "empty body"})
            return None
        try:
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._json(400, {"error": "invalid_json", "detail": str(exc)})
            return None
        if not isinstance(data, dict):
            self._json(400, {"error": "invalid_request", "detail": "JSON object required"})
            return None
        return data

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _safe_wizard_step(runtime: ServerRuntime, job_id: str) -> str | None:
    try:
        return runtime.current_wizard_step(job_id)
    except TypeError:
        return None


def serve_runtime(
    runtime: ServerRuntime,
    *,
    host: str,
    port: int,
) -> PalmHttpServer:
    """Create a threading HTTP server for the given runtime (caller starts serve)."""
    return PalmHttpServer((host, port), runtime)