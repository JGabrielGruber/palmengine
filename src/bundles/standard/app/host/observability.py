"""
HostObservability — residual packaging status for ApplicationHost (CS-002).

0.48.1 (PD-018): extracted the three status reports from the composition root.
0.61.7 (CS-002): demoted — these bags are **host packaging residual**, not
living-load law. Living eyes live in ``palm.system.vitality`` and are
presented via ``InspectService.top`` / ``.vitality``.

Public host methods ``event_plane_status`` / ``ops_status`` /
``control_plane_status`` remain thin residual aliases for consumers.
Prefer :meth:`packaging_status` when a single packaging bag is needed.

Do **not** grow a fourth host status method as living truth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bundles.standard.app.cli_settings import is_durable_storage
from bundles.standard.app.host.boot.modes import list_boot_modes
from palm.common.events.consumers import DEFAULT_JOURNAL_CONSUMERS, journal_consumer_status
from palm.common.resource.document_storage import resolve_kv_backend
from palm.system.boot import schedule_catalog
from palm.system.log import get_system_log

if TYPE_CHECKING:
    from bundles.standard.app.host.application_host import ApplicationHost

# CS-002 demotion markers — packaging residual, not seat / vitality law.
PACKAGING_ROLE = "host_packaging"
EYES_LAW = "palm.system.vitality"
OPERATE_EYES_PATHS = (
    "inspect/top",
    "inspect/vitality",
    "assist/top",
    "assist/vitality",
)
PACKAGING_NOTE = (
    "Host packaging residual (CS-002). Living load eyes: InspectService.top / "
    "vitality → palm.system.vitality. Do not treat this bag as seat law."
)


def _with_packaging_markers(
    bag: dict[str, Any],
    *,
    extra_note: str | None = None,
) -> dict[str, Any]:
    """Stamp demotion markers; preserve domain notes when present."""
    out = dict(bag)
    out["role"] = PACKAGING_ROLE
    out["eyes_law"] = EYES_LAW
    out["operate_paths"] = list(OPERATE_EYES_PATHS)
    domain = extra_note if extra_note is not None else bag.get("note")
    if isinstance(domain, str) and domain.strip() and domain.strip() != PACKAGING_NOTE:
        out["note"] = f"{PACKAGING_NOTE} | {domain}"
    else:
        out["note"] = PACKAGING_NOTE
    return out


class HostObservability:
    """Owns residual host packaging reports (not living vitality)."""

    def __init__(self, host: ApplicationHost) -> None:
        self._host = host

    def packaging_status(self) -> dict[str, Any]:
        """Single residual packaging bag (control-plane body + demotion).

        Prefer this over the triple method names for new packaging consumers.
        Living eyes remain ``inspect.top`` / ``inspect.vitality``.
        """
        return self.control_plane_status()

    def event_plane_status(self) -> dict[str, Any]:
        """Residual bus/packaging map (0.45.5). Not living seat law."""
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
        slog = get_system_log()
        domain_note = (
            "Orchestration events emit on runtime.event when the runtime is "
            "started; host.event is coordination only (host.started). "
            "Journal, internal inbound, and work-drain subscribe to the "
            "orchestration bus. system_log_* is process narrative (0.59.1a), "
            "not the domain event bus."
        )
        return _with_packaging_markers(
            {
                "orchestration_bus": orchestration_bus,
                "host_coordination_bus": "host",
                "inbound_internal_bus": orchestration_bus,
                "work_drain_bus": orchestration_bus,
                "journal_bus": orchestration_bus,
                "internal_inbound_bindings": internal_bindings,
                "orchestration_event_types": [
                    "job.completed",
                    "flow.session.succeeded",
                    "flow.session.failed",
                ],
                "system_log_level": slog.level,
                "system_log_recent": [r.to_dict() for r in slog.recent(limit=15)],
            },
            extra_note=domain_note,
        )

    def ops_status(self) -> dict[str, Any]:
        """Residual operator ergonomics packaging (0.45.8). Not living seat law."""
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
        return _with_packaging_markers(
            {
                "invoke_route": "POST /v1/api/providers/{provider}/{resource_ref}/invoke",
                "invoke_route_short": "POST /v1/api/resources/{resource_ref}/invoke",
                "storage_backend": backend_name,
                "storage_durable": durable,
                "event_log_durable": event_log_durable,
                "event_log_note": event_log_note,
                "server_profile_hint": server_hint,
            }
        )

    def control_plane_status(self) -> dict[str, Any]:
        """Residual work/journal/boot packaging (0.38 / 0.40.3). Not living seat law."""
        host = self._host
        work_pending = 0
        plane = None
        try:
            plane = host.runtime().work_plane
        except Exception:
            plane = None
        if plane is not None:
            work_pending = plane.store.pending_count()
        journal_status: dict[str, Any] = {}
        if host.event_journal is not None:
            journal_status = journal_consumer_status(
                host.event_journal,
                consumers=list(DEFAULT_JOURNAL_CONSUMERS),
            )
        outbox_pending = 0
        try:
            store = host.runtime().outbox_store
            if store is not None:
                outbox_pending = store.pending_count()
        except Exception:
            outbox_pending = 0
        bg = False
        dropped = 0
        if plane is not None:
            bg = bool(plane.is_running)
            dropped = int(plane.dropped_depth_count)
        schedules: list[dict[str, Any]] = []
        if plane is not None:
            try:
                schedules = list(plane.schedules.list_entries())
            except Exception:
                schedules = []
        inbound_bindings: list[dict[str, Any]] = []
        if host.inbound is not None:
            try:
                inbound_bindings = list(host.inbound.list_bindings())
            except Exception:
                inbound_bindings = []
        boot_mode = getattr(host, "boot_mode", None)
        domain_note = (
            "0.59.7 mode dogfood: ApplicationHost.for_mode('test'|'safe'|shapes); "
            "server/prod CI use server_port=0. CompositionProfile seeds membership "
            "except work_drain and outbox (definition capabilities after load). "
            "0.63: structure admission is law — see structure bag "
            "(not a soft dual of membership)."
        )
        structure_bag = self._structure_packaging()
        return _with_packaging_markers(
            {
                "work_pending": work_pending,
                "start_plane_running": bg,
                "work_dropped_depth": dropped,
                "schedules": schedules,
                "schedule_count": len(schedules),
                "outbox_pending": outbox_pending,
                "journal": journal_status,
                "journal_consumers": list(DEFAULT_JOURNAL_CONSUMERS),
                "inbound_bindings": inbound_bindings,
                "inbound_count": len(inbound_bindings),
                "boot": {
                    "mode": None if boot_mode is None else boot_mode.name,
                    "mode_detail": None if boot_mode is None else boot_mode.to_dict(),
                    "modes_available": list(list_boot_modes()),
                    "phase_tables": schedule_catalog(),
                    "membership": host.membership_snapshot(),
                    "last_walk": getattr(host, "boot_walk", None),
                    "note": domain_note,
                },
                # 0.63.8 admission inventory — nest live admission; packaging does not invent readiness.
                "structure": structure_bag,
                "event_plane": self.event_plane_status(),
                "ops": self.ops_status(),
            },
            extra_note=domain_note,
        )

    def _structure_packaging(self) -> dict[str, Any]:
        """Pointer to living admission (0.63) — not a second ready flag."""
        host = self._host
        try:
            from palm.system.structure.inventory import admission_inventory_snapshot

            runtime = host._app.runtime()
            snap = admission_inventory_snapshot(runtime)
            live = snap.get("live") or {}
            adm = live.get("admission") or {}
            return {
                "role": "admission_pointer",
                "eyes": "palm.system.vitality seat structure",
                "may_run_business": adm.get("may_run_business"),
                "definition_id": live.get("definition_id") or adm.get("definition_id"),
                "phase": adm.get("phase"),
                "capabilities": list(adm.get("capabilities") or []),
                "gated_count": snap.get("gated_count"),
                "readiness_edge_count": snap.get("readiness_edge_count"),
                # 0.63.38 exit residuals (cartography, not dual ready)
                "open_residual_count": snap.get("open_residual_count"),
                "open_residual_ids": snap.get("open_residual_ids"),
                "paid_edge_count": snap.get("paid_edge_count"),
                "note": (
                    "Read admission from the primary runtime / vitality structure seat. "
                    "This bag is packaging residual, not structure law. "
                    "open_residual_* is named-debt cartography for exit judgment."
                ),
            }
        except Exception as exc:
            return {
                "role": "admission_pointer",
                "may_run_business": None,
                "error": f"{type(exc).__name__}: {exc}",
                "note": "Primary runtime not ready or structure seat not present",
            }


__all__ = [
    "HostObservability",
    "PACKAGING_ROLE",
    "EYES_LAW",
    "OPERATE_EYES_PATHS",
    "PACKAGING_NOTE",
]
