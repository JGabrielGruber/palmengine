"""
WorkPlaneCoordinator — host packaging over system start plane + inbound + journal.

Owns host slots (`_inbound` / `_event_journal`). The start plane is
system-owned — read ``runtime.work_plane``. Host only binds product submit,
drain able, ready admission_able, and catalog. Public methods stay thin
delegates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bundles.standard.app.host.workplane.start_ports import product_start_ports
from palm.core.structure import CAPABILITY_JOURNAL
from palm.system.subsystems.planes.work.inbound import InboundBindingService
from palm.system.subsystems.supervisor import CallableSystemService

if TYPE_CHECKING:
    from bundles.standard.app.host.application_host import ApplicationHost


class WorkPlaneCoordinator:
    """WorkIntent drain + inbound bindings + event-journal ops for the host."""

    def __init__(self, host: ApplicationHost) -> None:
        self._host = host
        self._inbound: Any | None = None
        self._event_journal: Any | None = None

    @property
    def inbound(self) -> Any | None:
        return self._inbound

    @property
    def event_journal(self) -> Any | None:
        return self._event_journal

    # ── wiring (called during host start) ────────────────────────────────────

    def start_ports(self) -> tuple[Any, Any, Any]:
        """Product submit + drain able + ready admission_able."""
        host = self._host
        return product_start_ports(
            execution=host._execution,
            session=host.session,
            started=lambda: bool(host._started),
            admission=lambda: host.admission,
        )

    def wire_start_ports(self) -> None:
        """Bind product start ports on the install board. Does not take the plane."""
        host = self._host
        if not host._app.storage.is_initialized:
            return
        try:
            runtime = host.runtime()
        except Exception:
            return
        plane = runtime.work_plane
        install = runtime.install
        if plane is None or not getattr(plane, "is_attached", False) or install is None:
            return
        submit, able, admission_able = self.start_ports()
        install.bind(submit=submit, able=able, admission_able=admission_able)
        self.reload_work_triggers()

    def wire_inbound(self) -> None:
        """Inbound resource bindings — enqueue on the system start plane."""
        host = self._host
        try:
            plane = host.runtime().work_plane
        except Exception:
            plane = None
        if plane is None:
            return
        defs = host._definitions
        inbound = InboundBindingService(
            enqueue=plane.enqueue,
            event_engine=host._runtime_event_engine(),
            list_resources=lambda: list(defs.list_resources() or []),
            get_resource=defs.get_resource,
            invoke_resource=host.invoke_resource,
        )
        self._inbound = inbound
        self.reload_inbound_bindings()
        try:
            supervisor = host.runtime().supervisor
        except Exception:
            return
        if supervisor is None:
            return
        supervisor.register(
            CallableSystemService(
                "inbound",
                start=inbound.start_workers,
                stop=inbound.stop,
                status=inbound.status,
            )
        )

    def wire_event_journal(self) -> None:
        host = self._host
        # 0.67.8: host slot reads the hand's journal. Do not attach again.
        if not host.admission.has_capability(CAPABILITY_JOURNAL):
            self._event_journal = None
            return
        try:
            self._event_journal = host.runtime().install.event_journal
        except Exception:
            self._event_journal = None

    # ── reload / tick / drain (public host API delegates here) ───────────────

    def reload_work_triggers(self) -> int:
        """Reload definition triggers into the work drain (after design/example load).

        **0.60.7:** when the drain is the system work plane and product
        definitions are unavailable, fall back to the runtime definition
        repository on the system instance.
        """
        host = self._host
        try:
            plane = host.runtime().work_plane
        except Exception:
            plane = None
        if plane is None:
            return 0
        try:
            rows = host._definitions.list_flows() or []

            def _meta(name: str) -> dict[str, Any] | None:
                try:
                    detail = host._definitions.get_flow(name, verbose=True)
                except Exception:
                    return None
                if not isinstance(detail, dict):
                    return None
                # Prefer explicit metadata; else options (examples put triggers there).
                meta = detail.get("metadata")
                if isinstance(meta, dict) and meta.get("triggers"):
                    return meta
                opts = detail.get("options")
                return opts if isinstance(opts, dict) else meta

            return int(plane.reload_triggers(rows, get_metadata=_meta) or 0)
        except Exception:
            # Hostless / product-thin: repository on the system instance.
            if hasattr(plane, "reload_from_repository"):
                try:
                    repo = getattr(host.runtime(), "repository", None)
                    if repo is not None:
                        return int(plane.reload_from_repository(repo) or 0)
                except Exception:
                    return 0
            return 0

    def reload_inbound_bindings(self) -> int:
        """Rescan resources with metadata.inbound (0.43)."""
        if self._inbound is None:
            return 0
        try:
            n = int(self._inbound.reload_from_definitions() or 0)
            # Prefer supervisor start when inbound is registered (0.60.8).
            try:
                runtime = self._host._app.runtime()
                sup = getattr(runtime, "supervisor", None)
                if sup is not None and sup.get("inbound") is not None:
                    sup.start("inbound")
                    return n
            except Exception:
                pass
            self._inbound.start_workers()
            return n
        except Exception:
            return 0

    def tick_work(self, *, limit: int = 10, schedules: bool = True) -> int:
        """Process due WorkIntents (and optional schedule triggers). Returns count."""
        if self._inbound is not None:
            self._inbound.flush_debounced()
        try:
            plane = self._host.runtime().work_plane
        except Exception:
            plane = None
        if plane is None:
            return 0
        n = 0
        if schedules:
            n += plane.tick_schedules()
        n += plane.tick(limit=limit)
        return n

    def stop_inbound(self) -> None:
        try:
            runtime = self._host._app.runtime()
            sup = getattr(runtime, "supervisor", None)
            if sup is not None and sup.get("inbound") is not None:
                sup.stop("inbound")
                return
        except Exception:
            pass
        if self._inbound is not None:
            try:
                self._inbound.stop()
            except Exception:
                pass


__all__ = ["WorkPlaneCoordinator"]
