"""Inspect service — operational present/debug API (product door).

0.61.4 / SD-007: renamed from product ``SystemService`` so English no longer
collides with the system layer or the supervisor continuous-loop protocol.

0.61.5: ``top`` / ``vitality`` present **only** from system vitality projection.

0.61.6 / OD-001: ``doctor`` is demoted to **anatomy packaging** — nests living
eyes from projection; does not invent seat law.

0.61.11: ``benchmark`` presents the vitality tool (opt-in thrash via
``run_benchmark``); not enabled on everyday ``top`` / ``project``.
"""

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
from palm.common.services.base import BaseService
from palm.common.services.errors import InstanceNotFoundServiceError
from palm.kits.server.diagnostics import build_doctor_report
from palm.services.inspect.present import (
    present_benchmark,
    present_doctor,
    present_top,
    present_vitality,
    present_vitality_for_doctor,
)
from palm.system.vitality import (
    DEFAULT_ITERATIONS,
    DEFAULT_RECIPE,
    ProjectionOptions,
)


def _application_host_from(runtime: Any) -> Any | None:
    """Resolve ApplicationHost (ServerRuntime.host is the bind address string)."""
    for attr in ("application_host", "host_bridge", "_host_bridge"):
        cand = getattr(runtime, attr, None)
        if cand is not None and (
            hasattr(cand, "packaging_status") or hasattr(cand, "control_plane_status")
        ):
            return cand
    cand = getattr(runtime, "host", None)
    if cand is not None and (
        hasattr(cand, "packaging_status") or hasattr(cand, "control_plane_status")
    ):
        return cand
    return None


def _host_packaging(host: Any) -> dict[str, Any] | None:
    """Residual host packaging bag (CS-002) — not living seat law."""
    if host is None:
        return None
    try:
        if hasattr(host, "packaging_status"):
            return host.packaging_status()
        if hasattr(host, "control_plane_status"):
            return host.control_plane_status()
    except Exception:
        return None
    return None


class InspectService(BaseService):
    """Product present door — composes CQRS into business-shaped methods.

    Living eyes: :meth:`top` and :meth:`vitality` read
    :mod:`palm.system.vitality` only.

    :meth:`benchmark` presents the opt-in load tool (recipe → snapshot diff).
    Not part of everyday ``top``; thrash only when called.

    :meth:`doctor` is a **legacy verb** (OD-001): anatomy packaging that nests
    projection output. Prefer ``top`` / ``vitality`` for operate physiology.

    Supervisor continuous loops keep the unrelated protocol name
    ``SystemService`` under ``palm.system.subsystems.supervisor``.
    """

    def top(
        self,
        runtime: Any,
        options: ProjectionOptions | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Living load ``top`` — vitality projection present only."""
        return present_top(runtime, options, **kwargs)

    def vitality(
        self,
        runtime: Any,
        options: ProjectionOptions | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Full vitality snapshot — projection only (not doctor structure)."""
        return present_vitality(runtime, options, **kwargs)

    def benchmark(
        self,
        runtime: Any,
        *,
        recipe: str = DEFAULT_RECIPE,
        iterations: int = DEFAULT_ITERATIONS,
        mode: str | None = None,
        store_full_snapshots: bool = False,
    ) -> dict[str, Any]:
        """Opt-in vitality benchmark present — system tool, product envelope.

        Does not enable thrash on :meth:`top` / everyday projection.
        """
        return present_benchmark(
            runtime,
            recipe=recipe,
            iterations=iterations,
            mode=mode,
            store_full_snapshots=store_full_snapshots,
        )

    def doctor(self, runtime: Any) -> dict[str, Any]:
        """Legacy anatomy packaging — nests vitality; does not invent seat law.

        Prefer :meth:`top` / :meth:`vitality` for living eyes (OD-001 demotion).
        """
        host = _application_host_from(runtime)
        # CS-002: packaging residual only — living eyes nest from projection below.
        control_plane = _host_packaging(host)
        anatomy = build_doctor_report(runtime, control_plane=control_plane)
        try:
            top = self.top(runtime)
            return present_doctor(
                anatomy,
                top=top,
                vitality=present_vitality_for_doctor(top),
            )
        except Exception as exc:
            return present_doctor(anatomy, top_error=str(exc))

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


__all__ = ["InspectService"]
