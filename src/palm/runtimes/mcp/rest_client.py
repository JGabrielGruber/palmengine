"""Thin HTTP client for the Palm REST API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from palm.common.runtimes.server.middleware import PALM_SUBJECT_HEADER
from palm.runtimes.mcp.config import PalmMcpConfig


class PalmRestError(RuntimeError):
    """REST call failed with a non-success response."""

    def __init__(self, status: int, detail: Any) -> None:
        self.status = status
        self.detail = detail
        message = detail if isinstance(detail, str) else json.dumps(detail)
        super().__init__(f"Palm REST {status}: {message}")


class PalmRestClient:
    """Synchronous REST proxy used by MCP tools and resources."""

    def __init__(self, config: PalmMcpConfig) -> None:
        self._config = config

    @property
    def base_url(self) -> str:
        return self._config.base_url

    def get_health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def list_waiting_jobs(self, *, limit: int = 50) -> dict[str, Any]:
        return self._request("GET", f"/v1/jobs?status=WAITING_FOR_INPUT&limit={limit}")

    def get_wizard(self, instance_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/wizards/{instance_id}")

    def provide_wizard_input(self, instance_id: str, value: Any) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/wizards/{instance_id}/input",
            body={"value": value},
            auth=True,
        )

    def resume_child_wait(self, instance_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/wizards/{instance_id}/resume-child-wait",
            auth=True,
        )

    def get_instance_tree(self, instance_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/instances/{instance_id}/tree")

    def get_job_context(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/jobs/{job_id}/context")

    def provide_job_input(self, job_id: str, value: Any) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/jobs/{job_id}/input",
            body={"value": value},
            auth=True,
        )

    def resume_wizard_tick(self, instance_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/wizards/{instance_id}/resume-wizard-tick",
            auth=True,
        )

    def backtrack_wizard(self, instance_id: str, *, to_step: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if to_step is not None:
            body["to_step"] = to_step
        return self._request(
            "POST",
            f"/v1/wizards/{instance_id}/backtrack",
            body=body,
            auth=True,
        )

    def submit_wizard(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/wizards", body=body, auth=True)

    def submit_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/jobs", body=body, auth=True)

    def list_flows(self, *, pattern: str | None = None) -> dict[str, Any]:
        path = "/v1/flows"
        if pattern:
            path = f"{path}?pattern={pattern}"
        return self._request("GET", path)

    def get_flow(self, flow_id: str, *, verbose: bool = False) -> dict[str, Any]:
        suffix = "" if verbose else "?verbose=0"
        return self._request("GET", f"/v1/flows/{flow_id}{suffix}")

    def list_processes(self) -> dict[str, Any]:
        return self._request("GET", "/v1/processes")

    def get_process(self, process_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/processes/{process_id}")

    def list_resources(self, *, provider: str | None = None) -> dict[str, Any]:
        path = "/v1/resources"
        if provider:
            path = f"{path}?provider={provider}"
        return self._request("GET", path)

    def get_resource(self, resource_ref: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/resources/{resource_ref}")

    def get_openapi(self) -> dict[str, Any]:
        return self._request("GET", "/v1/openapi.json")

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/jobs/{job_id}/cancel",
            auth=True,
        )

    def prepare_plans(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/plans/prepare", body=body, auth=True)

    def submit_plans(self, plan_ids: list[str]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/plans/submit",
            body={"plan_ids": plan_ids},
            auth=True,
        )

    def get_doctor(self) -> dict[str, Any]:
        return self._request("GET", "/v1/doctor")

    def validate_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/flows/validate", body=body, auth=True)

    def list_snapshots(self, instance_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/instances/{instance_id}/snapshots")

    def get_snapshot(self, instance_id: str, snapshot_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/instances/{instance_id}/snapshots/{snapshot_id}",
        )

    def invoke_resource(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/resources/invoke", body=body, auth=True)

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        url = f"{self._config.base_url}{path}"
        headers = {"Accept": "application/json"}
        if auth:
            headers[PALM_SUBJECT_HEADER] = self._config.subject
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise PalmRestError(response.status, payload)
                return payload
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                detail: Any = json.loads(raw)
            except json.JSONDecodeError:
                detail = raw
            raise PalmRestError(exc.code, detail) from exc


__all__ = ["PalmRestClient", "PalmRestError"]
