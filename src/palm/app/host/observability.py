"""
HostObservability — the ApplicationHost's status/observability reports (T2 / 0.48.1, PD-018).

Extracted from ``ApplicationHost`` so the composition root no longer owns the
three status vocabularies. Behavior-preserving: the JSON shapes are frozen by
``tests/test_host_status_characterization_0_48.py``. The host keeps
``event_plane_status``/``ops_status``/``control_plane_status`` as 1-line
delegators (public API unchanged).

For now this reads the live host collaborators (`_work_drain`, `_inbound`,
`_event_journal`, `_outbox_service`, …) through a back-reference; later seams
(work-plane / runtime coordinators) formalize those into held collaborators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.app.cli_settings import is_durable_storage
from palm.common.events.consumers import DEFAULT_JOURNAL_CONSUMERS, journal_consumer_status
from palm.common.resource.document_storage import resolve_kv_backend

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost


class HostObservability:
    """Owns the host's event-plane / ops / control-plane status reports."""

    def __init__(self, host: ApplicationHost) -> None:
        self._host = host

    def event_plane_status(self) -> dict[str, Any]:
        """Which EventEngine each reactive surface uses (0.45.5 doctor contract)."""
        host = self._host
        orchestration_bus = "host_fallback"
        try:
            runtime = host._app.runtime()
            engine = runtime.event
            if engine is not None and engine.is_initialized:
                orchestration_bus = "runtime"
        except Exception:
            pass
        internal_bindings = 0
        if host.inbound is not None:
            try:
                internal_bindings = sum(
                    1 for row in host.inbound.list_bindings() if row.get("mode") == "internal"
                )
            except Exception:
                internal_bindings = 0
        return {
            "orchestration_bus": orchestration_bus,
            "host_coordination_bus": "host",
            "inbound_internal_bus": orchestration_bus,
            "work_drain_bus": orchestration_bus,
            "journal_bus": "host",
            "internal_inbound_bindings": internal_bindings,
            "orchestration_event_types": [
                "job.completed",
                "flow.session.succeeded",
                "flow.session.failed",
            ],
            "note": (
                "Orchestration events emit on runtime.event when the runtime is "
                "started; host.event is coordination only (host.started, journal, "
                "outbox). Internal inbound and work-drain subscribe to the "
                "orchestration bus."
            ),
        }

    def ops_status(self) -> dict[str, Any]:
        """Operator ergonomics — invoke routes, storage, event-log durability (0.45.8)."""
        host = self._host
        storage = host._app.storage
        backend_name = storage.backend_name if storage is not None else None
        durable = is_durable_storage(backend_name)
        event_log_durable: bool | None = None
        event_log_note: str | None = None
        try:
            described = host._definitions.get_resource("palm-system-event-log")
        except Exception:
            described = None
        if isinstance(described, dict):
            params = described.get("params") if isinstance(described.get("params"), dict) else {}
            kv_param = str((params or {}).get("backend") or "auto")
            try:
                resolved = resolve_kv_backend(
                    kv_param,
                    storage=storage,
                    storage_backend_name=backend_name,
                )
                event_log_durable = resolved != "memory"
            except ValueError:
                event_log_durable = False
            if event_log_durable is False:
                event_log_note = (
                    "palm-system-event-log resolves to memory kv; use "
                    "PALM_STORAGE_BACKEND=filesystem or params.backend=storage "
                    "for durable ops tail"
                )
        server_hint: str | None = None
        if host.profile.server and not durable:
            server_hint = (
                "server profile: set PALM_STORAGE_BACKEND=filesystem (or postgres) "
                "so instances, kv tails, and work queue survive restart"
            )
        return {
            "invoke_route": "POST /v1/api/providers/{provider}/{resource_ref}/invoke",
            "invoke_route_short": "POST /v1/api/resources/{resource_ref}/invoke",
            "storage_backend": backend_name,
            "storage_durable": durable,
            "event_log_durable": event_log_durable,
            "event_log_note": event_log_note,
            "server_profile_hint": server_hint,
        }

    def control_plane_status(self) -> dict[str, Any]:
        """Pending work + journal lag for doctor/ops (0.38 / 0.40.3)."""
        host = self._host
        work_pending = 0
        if host.work_drain is not None:
            work_pending = host.work_drain.store.pending_count()
        journal_status: dict[str, Any] = {}
        if host.event_journal is not None:
            journal_status = journal_consumer_status(
                host.event_journal,
                consumers=list(DEFAULT_JOURNAL_CONSUMERS),
            )
        outbox_pending = 0
        if host.outbox_service is not None:
            outbox_pending = host.outbox_service.store.pending_count()
        bg = False
        dropped = 0
        if host.work_drain is not None:
            bg = bool(host.work_drain.is_running)
            dropped = int(host.work_drain.dropped_depth_count)
        schedules: list[dict[str, Any]] = []
        if host.work_drain is not None:
            try:
                schedules = list(host.work_drain.schedules.list_entries())
            except Exception:
                schedules = []
        inbound_bindings: list[dict[str, Any]] = []
        if host.inbound is not None:
            try:
                inbound_bindings = list(host.inbound.list_bindings())
            except Exception:
                inbound_bindings = []
        return {
            "work_pending": work_pending,
            "work_drain_running": bg,
            "work_drain_background": bg,
            "work_dropped_depth": dropped,
            "schedules": schedules,
            "schedule_count": len(schedules),
            "outbox_pending": outbox_pending,
            "journal": journal_status,
            "journal_consumers": list(DEFAULT_JOURNAL_CONSUMERS),
            "inbound_bindings": inbound_bindings,
            "inbound_count": len(inbound_bindings),
            "event_plane": self.event_plane_status(),
            "ops": self.ops_status(),
        }


__all__ = ["HostObservability"]
