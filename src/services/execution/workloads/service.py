"""Workload execution service — policy + engine façade (product path).

Does not import neonroot/docker. Resolves runtime → WorkloadEngine.
See VISION-0.56 §8 · ADR-024 D8.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.services.base import BaseService
from palm.core.workload.exceptions import WorkloadError
from palm.core.workload.owner import WorkloadOwner
from palm.core.workload.spec import WorkloadSpec
from palm.core.workload.status import WorkloadStatus

if TYPE_CHECKING:
    from palm.system.runtime.base import BaseRuntime


class WorkloadExecutionService(BaseService):
    """Thin product API over the system ExecutionPort (workload methods)."""

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
        admission_source: Callable[[], Any] | Any | None = None,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver
        # 0.63.31 — published admission (product façade; no base class).
        self._admission_source = admission_source

    def resolve_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        if self._runtime_resolver is not None:
            return self._runtime_resolver(runtime_name)
        if self._runtime is None:
            raise RuntimeError("WorkloadExecutionService has no bound runtime")
        return self._runtime

    def admission_gate(self) -> object:
        """Published admission source for product workload start (0.63.31)."""
        if self._admission_source is not None:
            return self._admission_source
        return self.resolve_runtime()

    def _port(self, runtime_name: str | None = None) -> Any:
        return self.resolve_runtime(runtime_name).execution

    def start(
        self,
        spec: WorkloadSpec | dict[str, Any],
        *,
        owner: WorkloadOwner | dict[str, Any] | None = None,
        workload_id: str | None = None,
        idempotency_key: str | None = None,
        host_id: str | None = None,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Start a workload (product start — admission + ExecutionPort).

        **0.63.31:** product edge fails closed via ``admission_gate()``; port
        remains a second admission check.
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self.admission_gate())
        parsed = (
            spec if isinstance(spec, WorkloadSpec) else WorkloadSpec.from_dict(dict(spec))
        )
        bound_owner = _parse_owner(owner)
        try:
            wl = self._port(runtime_name).start_workload(
                parsed,
                owner=bound_owner,
                workload_id=workload_id,
                idempotency_key=idempotency_key,
                host_id=host_id,
            )
        except WorkloadError:
            raise
        return wl.to_dict()

    def exec(
        self,
        workload_id: str,
        command: list[str] | tuple[str, ...],
        *,
        timeout_s: float | None = None,
        env: dict[str, str] | None = None,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Exec argv on a READY workspace/service (product start).

        **0.63.31:** product edge fails closed via ``admission_gate()``.
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self.admission_gate())
        result = self._port(runtime_name).exec_workload(
            str(workload_id),
            command,
            timeout_s=timeout_s,
            env=env,
        )
        return result.to_dict()

    def stop(
        self,
        workload_id: str,
        *,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Idempotent stop — control path (not a business path that needs admission).

        Named residual: shutdown/cleanup when admission is closed.
        """
        wl = self._port(runtime_name).stop_workload(str(workload_id))
        return wl.to_dict()

    def cancel(
        self,
        workload_id: str,
        *,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Owner-driven stop (alias of stop for v1)."""
        return self.stop(workload_id, runtime_name=runtime_name)

    def get(
        self,
        workload_id: str,
        *,
        refresh: bool = False,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        wl = self._port(runtime_name).workload_status(
            str(workload_id), refresh=refresh
        )
        return wl.to_dict()

    def list(
        self,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        session_id: str | None = None,
        status: str | WorkloadStatus | None = None,
        runtime: str | None = None,
        runtime_name: str | None = None,
    ) -> list[dict[str, Any]]:
        status_enum: WorkloadStatus | None = None
        if status is not None:
            status_enum = (
                status if isinstance(status, WorkloadStatus) else WorkloadStatus(str(status))
            )
        rows = self._port(runtime_name).list_workloads(
            job_id=job_id,
            instance_id=instance_id,
            session_id=session_id,
            status=status_enum,
            runtime=runtime,
        )
        return [r.to_dict() for r in rows]

    def hosts(self, *, runtime_name: str | None = None) -> list[dict[str, Any]]:
        """Host registry v0 — single implicit local host."""
        _ = runtime_name
        return [
            {
                "id": "local",
                "kind": "local",
                "enabled": True,
                "health": "ok",
                "allowed_runtimes": ["local", "host", "neonroot"],
                "labels": {},
            }
        ]

    def runtimes(self, *, runtime_name: str | None = None) -> list[dict[str, Any]]:
        """Doctor-oriented runtime catalog from the port (includes health)."""
        return list(self._port(runtime_name).list_workload_runtimes())

    def doctor(self, *, runtime_name: str | None = None) -> dict[str, Any]:
        """Workload-plane doctor snapshot (engine + runner health via port)."""
        return dict(self._port(runtime_name).doctor_workloads())

    def stop_owned(
        self,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        session_id: str | None = None,
        runtime_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Cancel path: stop workloads owned by job/session/instance."""
        rows = self._port(runtime_name).stop_owned_workloads(
            job_id=job_id,
            instance_id=instance_id,
            session_id=session_id,
        )
        return [r.to_dict() for r in rows]


def _parse_owner(owner: WorkloadOwner | dict[str, Any] | None) -> WorkloadOwner:
    if owner is None:
        return WorkloadOwner()
    if isinstance(owner, WorkloadOwner):
        return owner
    return WorkloadOwner.from_dict(owner)


__all__ = ["WorkloadExecutionService"]
