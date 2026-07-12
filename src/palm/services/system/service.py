"""System service — operational inspect and debug API."""

from __future__ import annotations

from typing import Any

from palm.common.cqrs.command import CancelJobCommand
from palm.common.cqrs.query import (
    GetJobContextQuery,
    GetJobStatusQuery,
    InspectInstanceQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
)
from palm.common.runtimes.server.diagnostics import build_doctor_report
from palm.common.services.base import BaseService
from palm.common.services.errors import InstanceNotFoundServiceError


def _application_host_from(runtime: Any) -> Any | None:
    """Resolve ApplicationHost (ServerRuntime.host is the bind address string)."""
    for attr in ("application_host", "host_bridge", "_host_bridge"):
        cand = getattr(runtime, attr, None)
        if cand is not None and hasattr(cand, "control_plane_status"):
            return cand
    cand = getattr(runtime, "host", None)
    if cand is not None and hasattr(cand, "control_plane_status"):
        return cand
    return None


class SystemService(BaseService):
    """Debug and inspect surface — composes CQRS into business-shaped methods."""

    def doctor(self, runtime: Any) -> dict[str, Any]:
        """Engine health report for operators (includes control_plane when host-backed)."""
        control_plane = None
        host = _application_host_from(runtime)
        if host is not None and hasattr(host, "control_plane_status"):
            try:
                control_plane = host.control_plane_status()
            except Exception:
                control_plane = None
        return build_doctor_report(runtime, control_plane=control_plane)

    def list_jobs(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[Any]:
        rows = self.ask(ListJobStatusQuery(status=status, limit=limit))
        if rows and hasattr(rows[0], "to_dict"):
            return [row.to_dict() for row in rows]
        return rows

    def inspect_job(self, job_id: str) -> dict[str, Any]:
        return self.ask(GetJobContextQuery(job_id=job_id))

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self.ask(GetJobStatusQuery(job_id=job_id))

    def inspect_instance(self, instance_id: str) -> dict[str, Any]:
        """Pattern-aware instance view via :class:`InspectInstanceQuery`."""
        view = self.ask(InspectInstanceQuery(instance_id=instance_id))
        if view is None:
            raise InstanceNotFoundServiceError(instance_id)
        return view if isinstance(view, dict) else view.to_dict()

    def list_instances(
        self,
        *,
        status: str | None = None,
        flow_name: str | None = None,
        include_terminal: bool = True,
        limit: int | None = None,
    ) -> list[Any]:
        rows = self.ask(
            ListInstancesQuery(
                status=status,
                flow_name=flow_name,
                include_terminal=include_terminal,
                limit=limit,
            )
        )
        if rows and hasattr(rows[0], "to_dict"):
            return [row.to_dict() for row in rows]
        return rows

    def list_snapshots(self, instance_id: str) -> list[Any]:
        return self.ask(ListInstanceSnapshotsQuery(instance_id=instance_id))

    def cancel_job(self, job_id: str, *, runtime_name: str | None = None) -> dict[str, Any]:
        return self.dispatch(CancelJobCommand(job_id=job_id, runtime_name=runtime_name))


__all__ = ["SystemService"]
