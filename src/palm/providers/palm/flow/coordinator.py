"""Coordination layer for Palm compositional invocations."""

from __future__ import annotations

from typing import Any, Protocol

from palm.providers.palm.bindings.orchestration.local import LocalPalmInvoker
from palm.providers.palm.bindings.recursion.guard import RecursionLimits, palm_invoke_frame
from palm.providers.palm.exceptions import PalmLocalError
from palm.providers.palm.flow.context import InvokeContext
from palm.providers.palm.flow.params import PalmInvokeParams
from palm.providers.palm.flow.remote.invoker import RemotePalmInvoker
from palm.providers.palm.flow.target import PalmInvokeTarget


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