"""Workload place spawn — structure hands against WorkloadEngine (0.63.16).

``workload:`` places are structure bodies in the place registry. Not product job
path. Fail closed when no engine is bound. Default kind is *workspace* (warm
body) so ensure does not require a one-shot command.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from palm.core.workload.engine import WorkloadEngine
from palm.core.workload.exceptions import WorkloadNotFoundError
from palm.core.workload.handle import WorkloadHandle
from palm.core.workload.owner import WorkloadOwner
from palm.core.workload.record import Workload
from palm.core.workload.spec import (
    IsolationPolicy,
    LifecyclePolicy,
    WorkloadKind,
    WorkloadPlacement,
    WorkloadSpec,
)
from palm.core.workload.status import WorkloadStatus, is_terminal
from palm.system.structure.place_spawn import (
    PlaceSpawnResult,
    RegisteredPlaceSpawn,
    _argv_from_payload,
)


def _row(engine: WorkloadEngine | None, place_id: str) -> Workload | None:
    """Read the workload book by place id. Place id is the workload id."""
    if engine is None or not engine.is_initialized:
        return None
    try:
        return engine.get(place_id)
    except WorkloadNotFoundError:
        return None


def _fail_message(wl: Workload) -> str | None:
    if wl.message is not None:
        return wl.message
    if wl.result is not None:
        return wl.result.error
    return None


@dataclass
class WorkloadPlaceSpawn:
    """Ensure/release structure places via an optional :class:`WorkloadEngine`."""

    engine: WorkloadEngine | None = None
    default_runtime: str = "local"
    default_kind: str = "workspace"

    def bind_engine(self, engine: WorkloadEngine | None) -> None:
        self.engine = engine

    def ensure(self, place_id: str, payload: Mapping[str, Any] | None = None) -> PlaceSpawnResult:
        key = str(place_id or "").strip()
        if not key:
            return PlaceSpawnResult(state="failed", reason="empty_place_id")
        body = dict(payload or {})

        if self.engine is None:
            return PlaceSpawnResult(
                state="failed",
                reason="workload_engine_not_bound",
                payload={"place_id": key, **body},
            )
        if not self.engine.is_initialized:
            return PlaceSpawnResult(
                state="failed",
                reason="workload_engine_not_initialized",
                payload={"place_id": key},
            )

        existing = _row(self.engine, str(body.get("workload_id") or key))
        if existing is not None:
            status = existing.status
            wid = existing.workload_id or key
            if not is_terminal(status):
                return PlaceSpawnResult(
                    state="ready",
                    reason="workload_already",
                    handle=wid,
                    payload={"workload_id": wid, "status": str(status)},
                )
            if status is WorkloadStatus.STOPPED:
                return PlaceSpawnResult(
                    state="ready",
                    reason="workload_stopped_ok",
                    handle=wid,
                    payload={"workload_id": wid, "status": str(status)},
                )
            return PlaceSpawnResult(
                state="failed",
                reason="workload_failed",
                handle=wid,
                payload={"place_id": key, "workload_id": wid, "status": str(status)},
            )

        try:
            spec = self._spec_from_payload(key, body)
        except Exception as exc:
            return PlaceSpawnResult(
                state="failed",
                reason="workload_spec_invalid",
                payload={"place_id": key, "error": str(exc)},
            )

        owner = WorkloadOwner(
            session_id=str(body.get("session_id") or "structure"),
            lease_id=str(body.get("lease_id") or key),
        )
        wid = str(body.get("workload_id") or key)
        try:
            wl = self.engine.start(
                spec,
                owner=owner,
                workload_id=wid,
                idempotency_key=str(body.get("idempotency_key") or key),
            )
        except Exception as exc:
            return PlaceSpawnResult(
                state="failed",
                reason="workload_start_error",
                payload={"place_id": key, "error": str(exc)},
            )

        status = wl.status
        recorded = wl.workload_id or wid
        if status is WorkloadStatus.FAILED:
            return PlaceSpawnResult(
                state="failed",
                reason="workload_failed",
                handle=recorded,
                payload={
                    "place_id": key,
                    "workload_id": recorded,
                    "status": str(status),
                    "message": _fail_message(wl),
                },
            )

        return PlaceSpawnResult(
            state="ready",
            reason="workload_started",
            handle=recorded,
            payload={
                "place_id": key,
                "workload_id": recorded,
                "status": str(status),
                "runtime": wl.runtime,
            },
        )

    def release(self, place_id: str) -> PlaceSpawnResult:
        key = str(place_id or "").strip()
        if not key:
            return PlaceSpawnResult(state="gone", reason="empty_place_id")
        if self.engine is None:
            return PlaceSpawnResult(state="gone", reason="workload_not_tracked")
        row = _row(self.engine, key)
        if row is None:
            return PlaceSpawnResult(state="gone", reason="workload_not_tracked")
        wid = row.workload_id or key
        try:
            self.engine.stop(wid)
        except Exception as exc:
            return PlaceSpawnResult(
                state="gone",
                reason="workload_stop_error",
                handle=wid,
                payload={"error": str(exc)},
            )
        return PlaceSpawnResult(
            state="gone",
            reason="workload_released",
            handle=wid,
        )

    def _spec_from_payload(self, place_id: str, body: dict[str, Any]) -> WorkloadSpec:
        kind_raw = str(body.get("kind") or self.default_kind).lower()
        kind = WorkloadKind(kind_raw)
        argv = _argv_from_payload(body) or ()
        if kind is WorkloadKind.RUN and not argv:
            raise ValueError("kind=run requires argv/command")
        runtime = str(body.get("runtime") or body.get("placement_runtime") or self.default_runtime)
        isolation_raw = str(body.get("isolation") or "best_effort").lower()
        isolation = IsolationPolicy(isolation_raw)
        lifecycle_raw = str(body.get("lifecycle") or "lease").lower()
        lifecycle = LifecyclePolicy(lifecycle_raw)
        env = body.get("env") if isinstance(body.get("env"), dict) else {}
        return WorkloadSpec(
            kind=kind,
            isolation=isolation,
            lifecycle=lifecycle,
            command=tuple(argv) if argv else (),
            workdir=body.get("workdir"),
            env={str(k): str(v) for k, v in env.items()},
            timeout_s=body.get("timeout_s"),
            labels={
                "structure_place": place_id,
                **{str(k): str(v) for k, v in (body.get("labels") or {}).items()},
            },
            placement=WorkloadPlacement(runtime=runtime),
        )


@dataclass
class AdoptPlaceSpawn:
    """Ensure/release adopted places via an optional :class:`WorkloadEngine`.

    Does not call ``WorkloadEngine.start``. Missing handle fails closed.
    Release unbinds the book row; it does not stop a runner Palm did not start.
    """

    engine: WorkloadEngine | None = None

    def bind_engine(self, engine: WorkloadEngine | None) -> None:
        self.engine = engine

    def ensure(self, place_id: str, payload: Mapping[str, Any] | None = None) -> PlaceSpawnResult:
        key = str(place_id or "").strip()
        if not key:
            return PlaceSpawnResult(state="failed", reason="empty_place_id")
        body = dict(payload or {})

        if self.engine is None:
            return PlaceSpawnResult(
                state="failed",
                reason="workload_engine_not_bound",
                payload={"place_id": key, **body},
            )
        if not self.engine.is_initialized:
            return PlaceSpawnResult(
                state="failed",
                reason="workload_engine_not_initialized",
                payload={"place_id": key},
            )

        handle = _handle_from_payload(body)
        wid = str(body.get("workload_id") or key)
        if handle is None:
            booked = self._ready_from_book(wid)
            if booked is not None:
                return booked
            return PlaceSpawnResult(
                state="failed",
                reason="adopt_handle_missing",
                payload={"place_id": key},
            )

        owner = WorkloadOwner(
            session_id=str(body.get("session_id") or "structure"),
            lease_id=str(body.get("lease_id") or key),
            created_by_palm=False,
        )
        try:
            wl = self.engine.adopt(wid, handle, owner=owner)
        except Exception as exc:
            return PlaceSpawnResult(
                state="failed",
                reason="adopt_error",
                payload={"place_id": key, "error": str(exc)},
            )

        status = wl.status
        recorded = wl.workload_id or wid
        if status is WorkloadStatus.FAILED:
            return PlaceSpawnResult(
                state="failed",
                reason="adopt_failed",
                handle=recorded,
                payload={"place_id": key, "workload_id": recorded},
            )
        return PlaceSpawnResult(
            state="ready",
            reason="workload_adopted",
            handle=recorded,
            payload={
                "place_id": key,
                "workload_id": recorded,
                "status": str(status),
            },
        )

    def release(self, place_id: str) -> PlaceSpawnResult:
        key = str(place_id or "").strip()
        if not key:
            return PlaceSpawnResult(state="gone", reason="empty_place_id")
        if self.engine is None:
            return PlaceSpawnResult(state="gone", reason="workload_not_tracked")
        row = _row(self.engine, key)
        if row is None:
            return PlaceSpawnResult(state="gone", reason="workload_not_tracked")
        wid = row.workload_id or key
        try:
            self.engine.stop(wid)
        except Exception as exc:
            return PlaceSpawnResult(
                state="gone",
                reason="workload_stop_error",
                handle=wid,
                payload={"error": str(exc)},
            )
        return PlaceSpawnResult(
            state="gone",
            reason="workload_unbound",
            handle=wid,
        )

    def _ready_from_book(self, wid: str) -> PlaceSpawnResult | None:
        wl = _row(self.engine, wid)
        if wl is None:
            return None
        status = wl.status
        recorded = wl.workload_id or wid
        if not is_terminal(status):
            return PlaceSpawnResult(
                state="ready",
                reason="workload_already",
                handle=recorded,
                payload={
                    "place_id": recorded,
                    "workload_id": recorded,
                    "status": str(status),
                },
            )
        return None


def _handle_from_payload(body: Mapping[str, Any]) -> WorkloadHandle | None:
    """Typed handle from ensure payload. No dict | base_url coercion."""
    raw = body.get("handle")
    return raw if isinstance(raw, WorkloadHandle) else None


def adopt_prefix_spawn_port(
    engine: WorkloadEngine | None = None,
    *,
    spawn: AdoptPlaceSpawn | None = None,
) -> RegisteredPlaceSpawn:
    """Port where ``adopt:`` places bind to an existing WorkloadEngine row."""
    hands = spawn if spawn is not None else AdoptPlaceSpawn(engine=engine)
    if engine is not None:
        hands.bind_engine(engine)
    port = RegisteredPlaceSpawn()
    port.register_prefix(
        "adopt:",
        ensure=lambda pid, payload: hands.ensure(pid, payload),
        release=lambda pid: hands.release(pid),
    )
    port.register_bind(hands)
    return port


def workload_prefix_spawn_port(
    engine: WorkloadEngine | None = None,
    *,
    spawn: WorkloadPlaceSpawn | None = None,
) -> RegisteredPlaceSpawn:
    """Port where ``workload:`` places bind to WorkloadEngine (fail closed unbound)."""
    hands = spawn if spawn is not None else WorkloadPlaceSpawn(engine=engine)
    if engine is not None:
        hands.bind_engine(engine)
    port = RegisteredPlaceSpawn()
    port.register_prefix(
        "workload:",
        ensure=lambda pid, payload: hands.ensure(pid, payload),
        release=lambda pid: hands.release(pid),
    )
    port.register_bind(hands)
    port.workload_bind = hands
    return port


def combined_structure_spawn_port(
    *,
    engine: WorkloadEngine | None = None,
    os_registry: Any | None = None,
) -> RegisteredPlaceSpawn:
    """``os:`` + ``workload:`` + ``adopt:`` structure place routes on one port."""
    from palm.system.structure.place_spawn import (
        OsProcessRegistry,
        os_prefix_spawn_port,
    )

    os_port = os_prefix_spawn_port(registry=os_registry or OsProcessRegistry())
    wl_port = workload_prefix_spawn_port(engine=engine)
    ad_port = adopt_prefix_spawn_port(engine=engine)
    # Merge into one RegisteredPlaceSpawn with prefix routes + typed binds.
    combined = RegisteredPlaceSpawn()
    combined.prefix_ensures.update(os_port.prefix_ensures)
    combined.prefix_releases.update(os_port.prefix_releases)
    combined.prefix_ensures.update(wl_port.prefix_ensures)
    combined.prefix_releases.update(wl_port.prefix_releases)
    combined.prefix_ensures.update(ad_port.prefix_ensures)
    combined.prefix_releases.update(ad_port.prefix_releases)
    for hands in wl_port.book_binds():
        combined.register_bind(hands)
    for hands in ad_port.book_binds():
        combined.register_bind(hands)
    combined.workload_bind = wl_port.workload_bind
    # Residual: os registry stash for tests / shutdown (not book bind).
    os_reg = os_port.handles.get("__os_registry__")
    if os_reg is not None:
        combined.handles["__os_registry__"] = os_reg
    return combined


__all__ = [
    "AdoptPlaceSpawn",
    "WorkloadPlaceSpawn",
    "adopt_prefix_spawn_port",
    "combined_structure_spawn_port",
    "workload_prefix_spawn_port",
]
