"""
WorkPlaneCoordinator (T2 / 0.48.3, seam 4) — owns the host's deferred-work plane.

Extracted from ``ApplicationHost``: the WorkIntent drain, inbound resource
bindings, and event-journal catch-up/redrive — their wiring, reload, tick, and
drain operations, plus the three slots (`_work_drain`/`_inbound`/`_event_journal`).
The host holds one of these and delegates; the public methods
(`reload_work_triggers`, `tick_work`, `drain_journal_*`, `redrive_journal`) keep
identical signatures.

Reads other host state (execution, definitions, runtime event engine, …) through
a back-reference, as ``HostObservability`` does; behaviour is preserved.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.app.host.workplane.inbound_service import InboundBindingService
from palm.app.host.workplane.work_drain_service import WorkDrainService
from palm.common.events import wire_event_journal as _wire_event_journal
from palm.common.events.consumers import consume_for_projections, consume_for_webhooks

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost


class WorkPlaneCoordinator:
    """WorkIntent drain + inbound bindings + event-journal ops for the host."""

    def __init__(self, host: ApplicationHost) -> None:
        self._host = host
        self._work_drain: Any | None = None
        self._inbound: Any | None = None
        self._event_journal: Any | None = None

    @property
    def work_drain(self) -> Any | None:
        return self._work_drain

    @property
    def inbound(self) -> Any | None:
        return self._inbound

    @property
    def event_journal(self) -> Any | None:
        return self._event_journal

    # ── wiring (called during host start) ────────────────────────────────────

    def wire_work_drain(self) -> None:
        """WorkIntent queue + trigger attach (0.37). Drain is explicit via tick()."""
        host = self._host
        if not host._app.storage.is_initialized:
            return

        def _submit(flow_id: str, payload: dict[str, Any]) -> Any:
            body = dict(payload or {})
            seed = body.pop("_seed_state", None)
            submit_body: dict[str, Any] = {"flow_name": flow_id, "metadata": body}
            if seed is not None:
                submit_body["state"] = seed
            return host._execution.flows.submit_flow_body(submit_body)

        settings = host.settings
        self._work_drain = WorkDrainService(
            host._app.storage,
            submit_flow=_submit,
            event_engine=host._runtime_event_engine(),
            able=lambda: host._started,
            max_depth=int(settings.work_drain_max_depth),
            poll_interval=float(settings.work_drain_poll_interval),
            batch_size=int(settings.work_drain_batch_size),
        )
        job_events = host._runtime_event_engine()
        if job_events.is_initialized:
            self._work_drain.attach_events(job_events)
        # Load triggers from flow catalog (after examples/definitions already loaded)
        self.reload_work_triggers()

    def wire_inbound(self) -> None:
        """Inbound resource bindings (0.43) — metadata.inbound → WorkIntent."""
        host = self._host
        if self._work_drain is None:
            return

        def _list() -> list[dict[str, Any]]:
            try:
                return list(host._definitions.list_resources() or [])
            except Exception:
                return []

        def _get(name: str) -> dict[str, Any] | None:
            try:
                return host._definitions.get_resource(name)
            except Exception:
                return None

        def _enqueue(intent: Any) -> str:
            return self._work_drain.enqueue(intent)

        def _invoke(
            resource_ref: str,
            *,
            action: str | None = None,
            params: dict[str, Any] | None = None,
        ) -> Any:
            return host.invoke_resource(resource_ref, action=action, params=params)

        self._inbound = InboundBindingService(
            enqueue=_enqueue,
            event_engine=host._runtime_event_engine(),
            list_resources=_list,
            get_resource=_get,
            invoke_resource=_invoke,
        )
        self.reload_inbound_bindings()

    def wire_event_journal(self) -> None:
        host = self._host
        if not host._app.storage.is_initialized:
            return
        if not host._event.is_initialized:
            return
        journal, _sub = _wire_event_journal(host._event, host._app.storage)
        self._event_journal = journal

    # ── reload / tick / drain (public host API delegates here) ───────────────

    def reload_work_triggers(self) -> int:
        """Reload definition triggers into the work drain (after design/example load)."""
        host = self._host
        if self._work_drain is None:
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

            return int(self._work_drain.reload_triggers(rows, get_metadata=_meta) or 0)
        except Exception:
            return 0

    def reload_inbound_bindings(self) -> int:
        """Rescan resources with metadata.inbound (0.43)."""
        if self._inbound is None:
            return 0
        try:
            n = int(self._inbound.reload_from_definitions() or 0)
            self._inbound.start_workers()
            return n
        except Exception:
            return 0

    def tick_work(self, *, limit: int = 10, schedules: bool = True) -> int:
        """Process due WorkIntents (and optional schedule triggers). Returns count."""
        if self._inbound is not None:
            self._inbound.flush_debounced()
        if self._work_drain is None:
            return 0
        n = 0
        if schedules:
            n += self._work_drain.tick_schedules()
        n += self._work_drain.tick(limit=limit)
        return n

    def drain_journal_webhooks(self, *, limit: int = 50, on_entry: Any | None = None) -> int:
        """Catch-up webhooks consumer from journal (0.40.3). Returns entries processed."""
        if self._event_journal is None:
            return 0
        count = 0

        def _handler(entry: Any) -> None:
            nonlocal count
            count += 1
            if on_entry is not None:
                on_entry(entry)

        consume_for_webhooks(self._event_journal, _handler, limit=limit)
        return count

    def drain_journal_projections(self, *, limit: int = 50, on_entry: Any | None = None) -> int:
        """Catch-up projections consumer from journal (0.40.3)."""
        if self._event_journal is None:
            return 0
        count = 0

        def _handler(entry: Any) -> None:
            nonlocal count
            count += 1
            if on_entry is not None:
                on_entry(entry)

        consume_for_projections(self._event_journal, _handler, limit=limit)
        return count

    def redrive_journal(
        self,
        *,
        from_offset: int = 0,
        to_offset: int | None = None,
        event_types: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Replay journal entries for operator tooling (does not move consumer offsets)."""
        if self._event_journal is None:
            return []
        types = frozenset(event_types) if event_types else None
        entries = self._event_journal.redrive(
            from_offset=from_offset,
            to_offset=to_offset,
            event_types=types,
            limit=limit,
        )
        return [e.to_dict() for e in entries]

    # ── background lifecycle (called from host start/shutdown) ───────────────

    def start_background(self) -> None:
        if self._work_drain is not None:
            self._work_drain.start_background()

    def stop_background(self) -> None:
        if self._work_drain is not None:
            self._work_drain.stop_background()

    def stop_inbound(self) -> None:
        if self._inbound is not None:
            try:
                self._inbound.stop()
            except Exception:
                pass


__all__ = ["WorkPlaneCoordinator"]
