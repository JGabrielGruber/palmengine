"""Coordination layer for Palm compositional invocations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol

from palm.core.orchestration import Job
from palm.providers.palm.exceptions import PalmLocalError, PalmRemoteError, PalmTimeoutError
from palm.providers.palm.params import PalmInvokeParams
from palm.providers.palm.payload import job_payload, remote_job_payload, with_invoke_context
from palm.providers.palm.recursion import RecursionLimits, palm_invoke_frame
from palm.providers.palm.remote import (
    get_job_remote,
    submit_flow_remote,
    submit_process_remote,
    wait_for_job_remote,
)
from palm.providers.palm.target import PalmInvokeTarget
from palm.providers.palm.wiring import get_bound_runtime


@dataclass(frozen=True)
class InvokeContext:
    """Recursion frame and correlation context for a single invoke."""

    depth: int
    chain: tuple[str, ...]
    parent_job_id: str | None


class PalmInvoker(Protocol):
    """Strategy for executing a compositional invoke in a given runtime mode."""

    def fetch_job(self, job_id: str, params: PalmInvokeParams) -> dict[str, Any]: ...

    def invoke(
        self,
        action: str,
        target: PalmInvokeTarget,
        params: PalmInvokeParams,
        context: InvokeContext,
    ) -> dict[str, Any]: ...


class LocalPalmInvoker:
    """Execute compositional invokes against the bound in-process runtime."""

    def fetch_job(self, job_id: str, params: PalmInvokeParams) -> dict[str, Any]:
        runtime = _require_local_runtime()
        return job_payload(runtime.get_job(job_id))

    def invoke(
        self,
        action: str,
        target: PalmInvokeTarget,
        params: PalmInvokeParams,
        context: InvokeContext,
    ) -> dict[str, Any]:
        runtime = _require_local_runtime()
        metadata = params.correlation_metadata(depth=context.depth, chain=context.chain)
        state = params.resolve_state()

        if action == "invoke_resource" or target.kind == "resource":
            child_params = params.child_resource_params()
            child_provider = child_params.pop("provider", None)
            child_action = child_params.pop("resource_action", None) or child_params.pop(
                "action", None
            )
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
                raise PalmLocalError(result.error or "child resource invoke failed")
            return {
                "kind": "resource",
                "ref": target.ref,
                "invoke_depth": context.depth,
                "invoke_chain": list(context.chain),
                "parent_job_id": context.parent_job_id,
                "result": result.data,
                "metadata": dict(result.metadata),
            }

        if action == "submit_process" or target.kind == "process":
            jobs = runtime.executor.submit_process(
                target.ref,
                by_id=target.by_id,
                job_id=params.job_id,
                state=state,
                metadata=metadata,
            )
            job_list = jobs if isinstance(jobs, list) else [jobs]
            primary = job_list[0]
            if params.wait:
                primary = _wait_for_job(runtime, primary.id, params.wait_timeout)
            payload = job_payload(primary)
            payload["jobs"] = [job_payload(job) for job in job_list]
            return with_invoke_context(
                payload,
                depth=context.depth,
                chain=context.chain,
                parent_job_id=context.parent_job_id,
            )

        job = runtime.submit_flow(
            target.ref,
            by_id=target.by_id,
            job_id=params.job_id,
            state=state,
            metadata=metadata,
        )
        if params.wait:
            job = _wait_for_job(runtime, job.id, params.wait_timeout)
        return with_invoke_context(
            job_payload(job),
            depth=context.depth,
            chain=context.chain,
            parent_job_id=context.parent_job_id,
        )


class RemotePalmInvoker:
    """Execute compositional invokes via ServerRuntime HTTP."""

    def fetch_job(self, job_id: str, params: PalmInvokeParams) -> dict[str, Any]:
        payload = get_job_remote(
            str(params.remote_url),
            job_id,
            token=params.remote_token,
            retries=params.remote_retries,
        )
        return remote_job_payload(payload)

    def invoke(
        self,
        action: str,
        target: PalmInvokeTarget,
        params: PalmInvokeParams,
        context: InvokeContext,
    ) -> dict[str, Any]:
        base_url = str(params.remote_url)

        if action == "invoke_resource" or target.kind == "resource":
            raise PalmRemoteError("invoke_resource is not supported in remote mode yet")

        if action == "submit_process" or target.kind == "process":
            accepted = submit_process_remote(
                base_url,
                target.ref,
                by_id=target.by_id,
                job_id=params.job_id,
                token=params.remote_token,
                retries=params.remote_retries,
            )
            payload = remote_job_payload(accepted)
            payload["jobs"] = accepted.get("jobs", [accepted])
        else:
            accepted = submit_flow_remote(
                base_url,
                target.ref,
                by_id=target.by_id,
                job_id=params.job_id,
                token=params.remote_token,
                retries=params.remote_retries,
            )
            payload = remote_job_payload(accepted)

        if params.wait and payload.get("job_id"):
            completed = wait_for_job_remote(
                base_url,
                str(payload["job_id"]),
                token=params.remote_token,
                timeout=params.wait_timeout,
                retries=params.remote_retries,
            )
            payload = remote_job_payload(completed)

        return with_invoke_context(
            payload,
            depth=context.depth,
            chain=context.chain,
            parent_job_id=context.parent_job_id,
        )


class PalmInvokeCoordinator:
    """Orchestrates target dispatch, recursion guardrails, and invoker selection."""

    def __init__(
        self,
        *,
        local: PalmInvoker | None = None,
        remote: PalmInvoker | None = None,
    ) -> None:
        self._local = local or LocalPalmInvoker()
        self._remote = remote or RemotePalmInvoker()

    def fetch(self, params: PalmInvokeParams, *, resource_id: str | None) -> dict[str, Any]:
        job_id = params.resolve_job_id(resource_id=resource_id)
        if not job_id:
            raise PalmLocalError("fetch requires job_id or resource_id")
        invoker = self._remote if params.is_remote else self._local
        return invoker.fetch_job(job_id, params)

    def invoke(
        self,
        action: str,
        target: PalmInvokeTarget,
        params: PalmInvokeParams,
    ) -> dict[str, Any]:
        with palm_invoke_frame(
            target.kind,
            target.ref,
            limits=RecursionLimits(max_depth=params.max_depth),
        ) as (depth, chain):
            context = InvokeContext(
                depth=depth,
                chain=chain,
                parent_job_id=params.parent_job_id,
            )
            invoker = self._remote if params.is_remote else self._local
            return invoker.invoke(action, target, params, context)


def _require_local_runtime() -> Any:
    runtime = get_bound_runtime()
    if runtime is None or not runtime.is_started:
        raise PalmLocalError(
            "No local runtime bound; call runtime.start() or set remote_url",
        )
    return runtime


def _wait_for_job(runtime: Any, job_id: str, timeout: float) -> Job:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = runtime.get_job(job_id)
        if job.is_terminal:
            return job
        runtime.wait_until_idle(timeout=min(0.1, max(0.0, deadline - time.monotonic())))
        time.sleep(0.01)
    raise PalmTimeoutError(f"Timed out waiting for job {job_id!r}")
