"""Remote runtime invoker for compositional Palm calls."""

from __future__ import annotations

from typing import Any

from palm.providers.palm.bindings.orchestration.payload import (
    remote_job_payload,
    with_invoke_context,
)
from palm.providers.palm.exceptions import PalmRemoteError
from palm.providers.palm.flow.context import InvokeContext
from palm.providers.palm.flow.params import PalmInvokeParams
from palm.providers.palm.flow.remote.client import (
    get_job_remote,
    invoke_resource_remote,
    submit_flow_remote,
    submit_process_remote,
    wait_for_job_remote,
)
from palm.providers.palm.flow.target import PalmInvokeTarget
from palm.states import BlackboardState


def _state_dict(state: BlackboardState | None) -> dict[str, Any] | None:
    if state is None:
        return None
    return state.snapshot()


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
            remote_result = invoke_resource_remote(
                base_url,
                target.ref,
                action=params.resource_action,
                params=params.child_resource_params() or None,
                resource_id=params.resource_id,
                state=_state_dict(params.resolve_state()),
                token=params.remote_token,
                timeout=params.wait_timeout,
                retries=params.remote_retries,
            )
            if not remote_result.get("success"):
                raise PalmRemoteError(remote_result.get("error") or "remote resource invoke failed")
            data = remote_result.get("data")
            return {
                "kind": "resource",
                "ref": target.ref,
                "invoke_depth": context.depth,
                "invoke_chain": list(context.chain),
                "parent_job_id": context.parent_job_id,
                "result": data,
                "metadata": dict(remote_result.get("metadata") or {}),
            }

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
