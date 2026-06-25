"""Local runtime invoker for compositional Palm calls."""

from __future__ import annotations

from typing import Any

from palm.providers.palm.bindings.orchestration.payload import (
    job_payload,
    with_invoke_context,
)
from palm.providers.palm.bindings.orchestration.wait import wait_for_job
from palm.providers.palm.bindings.runtimes.wiring import get_bound_runtime
from palm.providers.palm.exceptions import PalmLocalError
from palm.providers.palm.flow.context import InvokeContext
from palm.providers.palm.flow.params import PalmInvokeParams
from palm.providers.palm.flow.target import PalmInvokeTarget


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
                primary = wait_for_job(
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
            job = wait_for_job(
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


def _require_local_runtime() -> Any:
    runtime = get_bound_runtime()
    if runtime is None or not runtime.is_started:
        raise PalmLocalError(
            "No local runtime bound; call runtime.start() or set remote_url",
        )
    return runtime