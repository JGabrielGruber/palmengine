"""Coordination layer for Palm compositional invocations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol

from palm.core.orchestration import Job, JobStatus
from palm.core.resource.invocation import WaitMode
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
            if params.wait_options.should_wait:
                primary = _wait_for_job(
                    runtime,
                    primary.id,
                    params.wait_timeout,
                    params.resolved_wait_mode,
                )
            payload = job_payload(primary)
            payload["jobs"] = [job_payload(job) for job in job_list]
            return with_invoke_context(
                payload,
                depth=context.depth,
                chain=context.chain,
                parent_job_id=context.parent_job_id,
                wait_mode=params.resolved_wait_mode,
            )

        job = runtime.submit_flow(
            target.ref,
            by_id=target.by_id,
            job_id=params.job_id,
            state=state,
            metadata=metadata,
        )
        if params.wait_options.should_wait:
            job = _wait_for_job(
                runtime,
                job.id,
                params.wait_timeout,
                params.resolved_wait_mode,
            )
        return with_invoke_context(
            job_payload(job),
            depth=context.depth,
            chain=context.chain,
            parent_job_id=context.parent_job_id,
            wait_mode=params.resolved_wait_mode,
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

        if params.wait_options.should_wait and payload.get("job_id"):
            completed = wait_for_job_remote(
                base_url,
                str(payload["job_id"]),
                token=params.remote_token,
                timeout=params.wait_timeout,
                retries=params.remote_retries,
                wait_mode=params.resolved_wait_mode,
            )
            payload = remote_job_payload(completed)

        return with_invoke_context(
            payload,
            depth=context.depth,
            chain=context.chain,
            parent_job_id=context.parent_job_id,
            wait_mode=params.resolved_wait_mode,
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


def _wait_for_job(
    runtime: Any,
    job_id: str,
    timeout: float,
    wait_mode: WaitMode,
) -> Job:
    deadline = time.monotonic() + timeout
    last: Job | None = None
    while time.monotonic() < deadline:
        job = runtime.get_job(job_id)
        last = job
        if _job_ready(job, wait_mode):
            return job
        runtime.wait_until_idle(timeout=min(0.1, max(0.0, deadline - time.monotonic())))
        time.sleep(0.01)
    raise PalmTimeoutError(_format_wait_timeout(job_id, last, wait_mode, timeout))


def _job_ready(job: Job, wait_mode: WaitMode) -> bool:
    if wait_mode == WaitMode.FIRE_AND_FORGET:
        return True
    if wait_mode == WaitMode.UNTIL_INPUT:
        return job.is_terminal or job.status == JobStatus.WAITING_FOR_INPUT
    return job.is_terminal


def _format_wait_timeout(
    job_id: str,
    job: Job | None,
    wait_mode: WaitMode,
    timeout: float,
) -> str:
    status = job.status.value if job is not None else "unknown"
    base = (
        f"Timed out after {timeout:g}s waiting for job {job_id!r} "
        f"(wait_mode={wait_mode.value}, current status={status})"
    )
    if (
        wait_mode == WaitMode.UNTIL_TERMINAL
        and job is not None
        and job.status == JobStatus.WAITING_FOR_INPUT
    ):
        return (
            f"{base}. The child flow is waiting for interactive input. "
            "Use wait_mode='until_input' on the resource step to return control "
            "to the parent wizard with the child job_id and instance_id."
        )
    if wait_mode == WaitMode.UNTIL_INPUT and job is not None and job.status == JobStatus.RUNNING:
        return (
            f"{base}. The child job has not reached WAITING_FOR_INPUT yet; "
            "increase timeout_seconds or verify the child flow exposes an interactive step."
        )
    return base
