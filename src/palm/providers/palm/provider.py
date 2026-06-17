"""Palm resource provider — compositional orchestration (Palm calling Palm)."""

from __future__ import annotations

import time
import uuid
from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.core.resource import BaseProvider
from palm.core.resource.result import ProviderActionDescriptor, ProviderDescriptor, ProviderHealth, ProviderResult
from palm.providers.palm.recursion import PalmRecursionError, RecursionLimits, palm_invoke_frame
from palm.providers.palm.remote import (
    get_job_remote,
    submit_flow_remote,
    submit_process_remote,
    wait_for_job_remote,
)
from palm.providers.palm.target import PalmInvokeTarget, parse_target
from palm.providers.palm.wiring import get_bound_runtime
from palm.states import BlackboardState

_RESERVED_PARAMS = frozenset(
    {
        "remote_url",
        "remote_token",
        "wait",
        "wait_timeout",
        "max_depth",
        "by_id",
        "target_kind",
        "kind",
        "target",
        "flow_name",
        "process_name",
        "resource_ref",
        "name",
        "metadata",
        "job_id",
        "initial_state",
        "state",
        "resource_action",
        "provider",
        "action",
        "resource_id",
        "__palm:parent_job_id",
    },
)


class PalmProvider(BaseProvider):
    """Invoke Palm flows, processes, and resources locally or via Server HTTP."""

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        """Fetch a job snapshot by id (``fetch`` action alias)."""
        result = self.invoke("fetch", resource_id=resource_id, params=dict(params))
        if not result.success:
            raise RuntimeError(result.error or "fetch failed")
        return result.data

    def invoke(
        self,
        action: str,
        *,
        params: dict[str, Any] | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        bound = dict(params or {})
        if resource_id is not None:
            bound.setdefault("resource_id", resource_id)
        bound.update(kwargs)

        if action == "fetch":
            return self._fetch_job(bound, resource_id=resource_id)

        try:
            target = parse_target(action=action, resource_id=resource_id, params=bound)
        except ValueError as exc:
            return ProviderResult.fail(
                str(exc),
                action=action,
                provider=self.name,
                resource_id=resource_id,
            )

        remote_url = bound.get("remote_url")
        wait = bool(bound.get("wait", False))
        wait_timeout = float(bound.get("wait_timeout", 30.0))
        max_depth = int(bound.get("max_depth", 8))
        parent_job_id = bound.get("__palm:parent_job_id")

        try:
            with palm_invoke_frame(
                target.kind,
                target.ref,
                limits=RecursionLimits(max_depth=max_depth),
            ) as (depth, chain):
                if remote_url:
                    payload = self._invoke_remote(
                        action,
                        target,
                        bound,
                        remote_url=str(remote_url),
                        remote_token=bound.get("remote_token"),
                        wait=wait,
                        wait_timeout=wait_timeout,
                        depth=depth,
                        chain=chain,
                        parent_job_id=parent_job_id,
                    )
                else:
                    payload = self._invoke_local(
                        action,
                        target,
                        bound,
                        wait=wait,
                        wait_timeout=wait_timeout,
                        depth=depth,
                        chain=chain,
                        parent_job_id=parent_job_id,
                    )
        except PalmRecursionError as exc:
            return ProviderResult.fail(
                str(exc),
                action=action,
                provider=self.name,
                resource_id=resource_id,
            )
        except TimeoutError as exc:
            return ProviderResult.fail(
                str(exc),
                action=action,
                provider=self.name,
                resource_id=resource_id,
            )
        except Exception as exc:
            return ProviderResult.fail(
                str(exc),
                action=action,
                provider=self.name,
                resource_id=resource_id,
            )

        return ProviderResult.ok(
            payload,
            action=action,
            provider=self.name,
            resource_id=resource_id or target.ref,
            mode="remote" if remote_url else "local",
            invoke_depth=payload.get("invoke_depth"),
            parent_job_id=parent_job_id,
        )

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            description="Compositional Palm orchestration — invoke flows, processes, and resources",
            actions=(
                ProviderActionDescriptor(
                    "submit_flow",
                    "Submit a child flow by name or flow:<ref>",
                ),
                ProviderActionDescriptor(
                    "submit_process",
                    "Submit a child process by name or process:<ref>",
                ),
                ProviderActionDescriptor(
                    "invoke_resource",
                    "Invoke a registered resource definition on the bound runtime",
                ),
                ProviderActionDescriptor(
                    "fetch",
                    "Fetch job status and result by job id",
                ),
            ),
        )

    def health(self) -> ProviderHealth:
        runtime = get_bound_runtime()
        if runtime is not None and runtime.is_started:
            return ProviderHealth(healthy=True, message="local runtime bound")
        return ProviderHealth(
            healthy=False,
            message="no local runtime bound; use remote_url for remote mode",
        )

    def _fetch_job(
        self,
        params: dict[str, Any],
        *,
        resource_id: str | None,
    ) -> ProviderResult:
        job_id = str(
            params.get("job_id")
            or params.get("target")
            or resource_id
            or "",
        ).strip()
        if not job_id:
            return ProviderResult.fail(
                "fetch requires job_id or resource_id",
                action="fetch",
                provider=self.name,
            )

        remote_url = params.get("remote_url")
        if remote_url:
            payload = get_job_remote(
                str(remote_url),
                job_id,
                token=params.get("remote_token"),
            )
            return ProviderResult.ok(
                _remote_job_payload(payload),
                action="fetch",
                provider=self.name,
                resource_id=job_id,
                mode="remote",
            )

        runtime = get_bound_runtime()
        if runtime is None or not runtime.is_started:
            return ProviderResult.fail(
                "No local runtime bound for fetch",
                action="fetch",
                provider=self.name,
                resource_id=job_id,
            )
        job = runtime.get_job(job_id)
        return ProviderResult.ok(
            _job_payload(job),
            action="fetch",
            provider=self.name,
            resource_id=job_id,
            mode="local",
        )

    def _invoke_local(
        self,
        action: str,
        target: PalmInvokeTarget,
        params: dict[str, Any],
        *,
        wait: bool,
        wait_timeout: float,
        depth: int,
        chain: tuple[str, ...],
        parent_job_id: Any,
    ) -> dict[str, Any]:
        runtime = get_bound_runtime()
        if runtime is None or not runtime.is_started:
            raise RuntimeError(
                "No local runtime bound; call runtime.start() or set remote_url",
            )

        metadata = _correlation_metadata(params, depth=depth, chain=chain, parent_job_id=parent_job_id)
        job_id = _optional_job_id(params)
        state = _resolve_state(params)

        if action == "invoke_resource" or target.kind == "resource":
            child_params = _child_params(params)
            child_provider = child_params.pop("provider", None)
            child_action = child_params.pop("resource_action", None) or child_params.pop("action", None)
            child_resource_id = child_params.pop("resource_id", None)
            result = runtime.resource.invoke(
                target.ref,
                provider=child_provider,
                action=child_action,
                params=child_params or None,
                resource_id=child_resource_id,
                state=state,
            )
            if not result.success:
                raise RuntimeError(result.error or "child resource invoke failed")
            return {
                "kind": "resource",
                "ref": target.ref,
                "invoke_depth": depth,
                "invoke_chain": list(chain),
                "parent_job_id": parent_job_id,
                "result": result.data,
                "metadata": dict(result.metadata),
            }

        if action == "submit_process" or target.kind == "process":
            jobs = runtime.executor.submit_process(
                target.ref,
                by_id=target.by_id,
                job_id=job_id,
                state=state,
                metadata=metadata,
            )
            primary = jobs[0] if isinstance(jobs, list) else jobs
            if wait:
                primary = _wait_for_job(runtime, primary.id, wait_timeout)
            payload = _job_payload(primary)
            payload["jobs"] = [_job_payload(job) for job in (jobs if isinstance(jobs, list) else [jobs])]
            payload["invoke_depth"] = depth
            payload["invoke_chain"] = list(chain)
            payload["parent_job_id"] = parent_job_id
            return payload

        job = runtime.submit_flow(
            target.ref,
            by_id=target.by_id,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )
        if wait:
            job = _wait_for_job(runtime, job.id, wait_timeout)
        payload = _job_payload(job)
        payload["invoke_depth"] = depth
        payload["invoke_chain"] = list(chain)
        payload["parent_job_id"] = parent_job_id
        return payload

    def _invoke_remote(
        self,
        action: str,
        target: PalmInvokeTarget,
        params: dict[str, Any],
        *,
        remote_url: str,
        remote_token: Any,
        wait: bool,
        wait_timeout: float,
        depth: int,
        chain: tuple[str, ...],
        parent_job_id: Any,
    ) -> dict[str, Any]:
        token = str(remote_token) if remote_token else None
        job_id = _optional_job_id(params)

        if action == "invoke_resource" or target.kind == "resource":
            raise RuntimeError("invoke_resource is not supported in remote mode yet")

        if action == "submit_process" or target.kind == "process":
            accepted = submit_process_remote(
                remote_url,
                target.ref,
                by_id=target.by_id,
                job_id=job_id,
                token=token,
            )
            payload = _remote_job_payload(accepted)
            payload["jobs"] = accepted.get("jobs", [accepted])
            if wait and payload.get("job_id"):
                completed = wait_for_job_remote(
                    remote_url,
                    str(payload["job_id"]),
                    token=token,
                    timeout=wait_timeout,
                )
                payload = _remote_job_payload(completed)
            payload["invoke_depth"] = depth
            payload["invoke_chain"] = list(chain)
            payload["parent_job_id"] = parent_job_id
            return payload

        accepted = submit_flow_remote(
            remote_url,
            target.ref,
            by_id=target.by_id,
            job_id=job_id,
            token=token,
        )
        payload = _remote_job_payload(accepted)
        if wait and payload.get("job_id"):
            completed = wait_for_job_remote(
                remote_url,
                str(payload["job_id"]),
                token=token,
                timeout=wait_timeout,
            )
            payload = _remote_job_payload(completed)
        payload["invoke_depth"] = depth
        payload["invoke_chain"] = list(chain)
        payload["parent_job_id"] = parent_job_id
        return payload


def _correlation_metadata(
    params: dict[str, Any],
    *,
    depth: int,
    chain: tuple[str, ...],
    parent_job_id: Any,
) -> dict[str, Any]:
    meta = dict(params.get("metadata") or {})
    meta["__palm:invoke_depth"] = depth
    meta["__palm:invoke_chain"] = list(chain)
    if parent_job_id:
        meta["__palm:parent_job_id"] = str(parent_job_id)
    return meta


def _child_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if key not in _RESERVED_PARAMS}


def _optional_job_id(params: dict[str, Any]) -> str | None:
    raw = params.get("job_id")
    return str(raw) if raw else None


def _resolve_state(params: dict[str, Any]) -> BlackboardState | None:
    raw = params.get("initial_state") or params.get("state")
    if raw is None:
        return None
    if isinstance(raw, BlackboardState):
        return raw
    if isinstance(raw, dict):
        return BlackboardState(raw)
    return None


def _wait_for_job(runtime: Any, job_id: str, timeout: float) -> Job:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = runtime.get_job(job_id)
        if job.is_terminal:
            return job
        runtime.wait_until_idle(timeout=min(0.1, max(0.0, deadline - time.monotonic())))
        time.sleep(0.01)
    raise TimeoutError(f"Timed out waiting for job {job_id!r}")


def _job_payload(job: Job) -> dict[str, Any]:
    return {
        "job_id": job.id,
        "instance_id": job.metadata.get("instance_id"),
        "status": job.status.value,
        "result": job.result,
        "metadata": dict(job.metadata),
        "error": str(job.error) if job.error else None,
    }


def _remote_job_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if "job_id" not in payload and "jobs" in payload and payload["jobs"]:
        first = payload["jobs"][0]
        if isinstance(first, dict):
            return _remote_job_payload(first)
    return {
        "job_id": payload.get("job_id"),
        "instance_id": payload.get("instance_id"),
        "status": payload.get("status"),
        "result": payload.get("result"),
        "metadata": dict(payload.get("metadata") or {}),
        "error": payload.get("error"),
    }


def new_child_job_id(prefix: str = "palm-child") -> str:
    """Generate a correlation-friendly child job id."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"