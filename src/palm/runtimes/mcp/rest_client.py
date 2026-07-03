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
        return self._request(
            "GET",
            f"/v1/api/system/jobs?status=WAITING_FOR_INPUT&limit={limit}",
        )

    def flows_list(self) -> dict[str, Any]:
        return self._request("GET", "/v1/api/flows")

    def flows_describe(self, flow_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/api/flows/{flow_id}")

    def flows_create_session(self, flow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/api/flows/{flow_id}/create",
            body=body,
            auth=True,
        )

    def flows_get_session(
        self,
        flow_id: str | None,
        session_id: str,
    ) -> dict[str, Any]:
        resolved_flow = flow_id or self._resolve_flow_id(session_id)
        return self._request(
            "GET",
            f"/v1/api/flows/{resolved_flow}/session/{session_id}",
        )

    def flows_session_input(
        self,
        flow_id: str,
        session_id: str,
        value: Any,
        *,
        input_token: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"value": value}
        if input_token is not None:
            body["input_token"] = input_token
        return self._request(
            "POST",
            f"/v1/api/flows/{flow_id}/session/{session_id}/input",
            body=body,
            auth=True,
        )

    def flows_session_backtrack(
        self,
        flow_id: str,
        session_id: str,
        *,
        to_step: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if to_step is not None:
            body["to_step"] = to_step
        return self._request(
            "POST",
            f"/v1/api/flows/{flow_id}/session/{session_id}/backtrack",
            body=body,
            auth=True,
        )

    def flows_session_resume(self, flow_id: str, session_id: str) -> dict[str, Any]:
        self._request(
            "POST",
            f"/v1/api/flows/{flow_id}/session/{session_id}/resume",
            auth=True,
        )
        return self.flows_get_session(flow_id, session_id)

    def flows_session_resume_child_wait(
        self,
        flow_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/api/flows/{flow_id}/session/{session_id}/resume-child-wait",
            auth=True,
        )

    def get_wizard(self, instance_id: str) -> dict[str, Any]:
        from palm.runtimes.mcp.flows.views import flatten_session_view

        return flatten_session_view(self.flows_get_session(None, instance_id))

    def provide_wizard_input(self, instance_id: str, value: Any) -> dict[str, Any]:
        from palm.runtimes.mcp.flows.views import flatten_session_view, resolve_flow_id_from_inspect

        inspect = self.get_wizard(instance_id)
        flow_id = resolve_flow_id_from_inspect(inspect)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {instance_id!r}")
        view = self.flows_session_input(flow_id, instance_id, value)
        return flatten_session_view(view)

    def resume_child_wait(self, instance_id: str) -> dict[str, Any]:
        from palm.runtimes.mcp.flows.views import flatten_session_view, resolve_flow_id_from_inspect

        inspect = self.get_wizard(instance_id)
        flow_id = resolve_flow_id_from_inspect(inspect)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {instance_id!r}")
        view = self.flows_session_resume_child_wait(flow_id, instance_id)
        return flatten_session_view(view)

    def get_instance_tree(self, instance_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/api/system/instances/{instance_id}/tree")

    def get_job_context(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/api/system/jobs/{job_id}/context")

    def provide_job_input(self, job_id: str, value: Any) -> dict[str, Any]:
        from palm.runtimes.mcp.flows.views import flatten_session_view, resolve_flow_id_from_inspect

        context = self.get_job_context(job_id)
        instance = context.get("instance")
        instance_id = (
            instance.get("instance_id")
            if isinstance(instance, dict)
            else None
        ) or (context.get("metadata") or {}).get("instance_id")
        if not instance_id:
            raise PalmRestError(400, f"could not resolve instance_id for job {job_id!r}")
        flow_id = resolve_flow_id_from_inspect(context)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for job {job_id!r}")
        view = self.flows_session_input(str(flow_id), str(instance_id), value)
        return flatten_session_view(view)

    def resume_wizard_tick(self, instance_id: str) -> dict[str, Any]:
        from palm.runtimes.mcp.flows.views import resolve_flow_id_from_inspect

        inspect = self.get_wizard(instance_id)
        flow_id = resolve_flow_id_from_inspect(inspect)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {instance_id!r}")
        return self.flows_session_resume(flow_id, instance_id)

    def backtrack_wizard(self, instance_id: str, *, to_step: str | None = None) -> dict[str, Any]:
        from palm.runtimes.mcp.flows.views import flatten_session_view, resolve_flow_id_from_inspect

        inspect = self.get_wizard(instance_id)
        flow_id = resolve_flow_id_from_inspect(inspect)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {instance_id!r}")
        view = self.flows_session_backtrack(flow_id, instance_id, to_step=to_step)
        return flatten_session_view(view)

    def submit_wizard(self, body: dict[str, Any]) -> dict[str, Any]:
        flow_id = str(body.get("flow_name") or _flow_id_from_submit_body(body) or "flow")
        return self.flows_create_session(flow_id, body)

    def submit_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        flow_id = str(
            body.get("flow_name")
            or _flow_id_from_submit_body(body)
            or "flow"
        )
        return self.flows_create_session(flow_id, body)

    def list_flows(self, *, pattern: str | None = None) -> dict[str, Any]:
        path = "/v1/api/definitions/flows"
        if pattern:
            path = f"{path}?pattern={pattern}"
        return self._request("GET", path)

    def get_flow(self, flow_id: str, *, verbose: bool = False) -> dict[str, Any]:
        suffix = "" if verbose else "?verbose=0"
        return self._request("GET", f"/v1/api/definitions/flows/{flow_id}{suffix}")

    def list_processes(self) -> dict[str, Any]:
        return self._request("GET", "/v1/api/definitions/processes")

    def get_process(self, process_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/api/definitions/processes/{process_id}")

    def list_resources(self, *, provider: str | None = None) -> dict[str, Any]:
        path = "/v1/api/definitions/resources"
        if provider:
            path = f"{path}?provider={provider}"
        return self._request("GET", path)

    def get_resource(self, resource_ref: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/api/definitions/resources/{resource_ref}")

    def get_openapi(self) -> dict[str, Any]:
        return self._request("GET", "/v1/openapi.json")

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/api/system/jobs/{job_id}/cancel",
            auth=True,
        )

    def prepare_plans(self, body: dict[str, Any]) -> dict[str, Any]:
        process_id = _process_id_from_body(body)
        return self._request(
            "POST",
            f"/v1/api/processes/{process_id}/prepare",
            body=body,
            auth=True,
        )

    def submit_plans(self, plan_ids: list[str]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/api/processes/submit",
            body={"plan_ids": plan_ids},
            auth=True,
        )

    def get_doctor(self) -> dict[str, Any]:
        return self._request("GET", "/v1/api/system/doctor")

    def assist_dispatch(
        self,
        path: list[str],
        params: dict[str, Any] | None = None,
    ) -> Any:
        from palm.runtimes.mcp.assist.dispatch import map_dispatch_to_rest

        method, url_path, body, auth = map_dispatch_to_rest(path, params)
        return self._request(method, url_path, body=body, auth=auth)

    def validate_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/api/definitions/flows/validate", body=body, auth=True)

    def _resolve_flow_id(self, session_id: str) -> str:
        from palm.runtimes.mcp.flows.views import flatten_session_view, resolve_flow_id_from_inspect

        rows = self.flows_list().get("flows") or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            flow_id = row.get("flow_id") or row.get("name")
            if not flow_id:
                continue
            try:
                view = flatten_session_view(self.flows_get_session(str(flow_id), session_id))
            except PalmRestError as exc:
                if exc.status == 404:
                    continue
                raise
            resolved = resolve_flow_id_from_inspect(view)
            if resolved:
                return resolved
            return str(flow_id)
        raise PalmRestError(404, f"could not resolve flow_id for session {session_id!r}")

    def list_snapshots(self, instance_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/api/system/instances/{instance_id}/snapshots")

    def get_snapshot(self, instance_id: str, snapshot_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/api/system/instances/{instance_id}/snapshots/{snapshot_id}",
        )

    def invoke_resource(self, body: dict[str, Any]) -> dict[str, Any]:
        resource_ref = str(body.get("resource_ref") or "").strip()
        if not resource_ref:
            raise PalmRestError(400, "resource_ref is required")
        provider = body.get("provider")
        if not provider:
            described = self.get_resource(resource_ref)
            provider = described.get("provider")
        if not provider:
            raise PalmRestError(400, f"could not resolve provider for resource {resource_ref!r}")
        invoke_body = {
            key: body[key]
            for key in ("action", "params", "resource_id", "state")
            if key in body
        }
        return self._request(
            "POST",
            f"/v1/api/providers/{provider}/{resource_ref}/invoke",
            body=invoke_body,
            auth=True,
        )

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


def _process_id_from_body(body: dict[str, Any]) -> str:
    if body.get("process_name"):
        return str(body["process_name"])
    process = body.get("process")
    if isinstance(process, dict) and process.get("name"):
        return str(process["name"])
    return "process"


def _flow_id_from_submit_body(body: dict[str, Any]) -> str | None:
    wizard = body.get("wizard")
    if isinstance(wizard, dict):
        name = wizard.get("name")
        return str(name) if name is not None else None
    flow = body.get("flow")
    if isinstance(flow, dict):
        for key in ("name", "flow", "flow_name"):
            value = flow.get(key)
            if value is not None:
                return str(value)
    return None


__all__ = ["PalmRestClient", "PalmRestError"]
