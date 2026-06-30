"""Execution service — instance-centric run, input, and lifecycle API."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.job_context import instance_id_for_job
from palm.common.services.base import BaseService
from palm.common.services.session import InstanceSession

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime
    from palm.common.services.internal import InternalService


class ExecutionService(BaseService):
    """Run flows and drive instances — composes CQRS and interactive runtime helpers."""

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        internal: InternalService,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._internal = internal
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver

    def on(self, instance_id: str) -> InstanceSession:
        """Return a session bound to a durable instance."""
        return InstanceSession(self, instance_id)

    def run_wizard(self, body: dict[str, Any]) -> InstanceSession:
        """Submit a wizard flow and return a session on the new instance."""
        job = self.dispatch(flow_command_from_body(body))
        self.wait_until_idle()
        return self.on(instance_id_for_job(job))

    def run_flow(
        self,
        flow: Any,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> InstanceSession:
        """Submit a flow and return a session on the new instance."""
        job = self.dispatch(
            SubmitFlowCommand(
                flow=flow,
                by_id=by_id,
                job_id=job_id,
                metadata=metadata or {},
            )
        )
        self.wait_until_idle()
        return self.on(instance_id_for_job(job))

    def inspect_instance(self, instance_id: str) -> dict[str, Any]:
        """Delegate to internal inspect for session status views."""
        return self._internal.inspect_instance(instance_id)

    def resolve_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        if self._runtime_resolver is not None:
            return self._runtime_resolver(runtime_name)
        if self._runtime is not None:
            return self._runtime
        raise RuntimeError("ExecutionService requires a runtime or runtime_resolver")

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        return self.resolve_runtime().wait_until_idle(timeout=timeout)


def flow_command_from_body(body: dict[str, Any]) -> SubmitFlowCommand:
    """Build :class:`SubmitFlowCommand` from REST/MCP-style submission bodies."""
    if "flow" in body and isinstance(body["flow"], dict):
        payload = dict(body["flow"])
        if body.get("job_id") is not None:
            payload["job_id"] = body["job_id"]
        return SubmitFlowCommand(flow=payload)
    if "wizard" in body:
        return SubmitFlowCommand(
            flow={
                "wizard": body["wizard"],
                **({"job_id": body["job_id"]} if body.get("job_id") is not None else {}),
            }
        )
    if "flow_name" in body:
        return SubmitFlowCommand(
            flow=str(body["flow_name"]),
            by_id=bool(body.get("by_id", False)),
            job_id=_optional_str(body.get("job_id")),
        )
    raise ValueError("expected 'flow', 'wizard', or 'flow_name' in request body")


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


__all__ = ["ExecutionService", "flow_command_from_body"]
