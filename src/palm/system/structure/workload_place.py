"""Workload place spawn — structure hands against WorkloadEngine (0.63.16).

``workload:`` places are structure bodies in the place registry. Not product job
path. Fail closed when no engine is bound. Default kind is *workspace* (warm
body) so ensure does not require a one-shot command.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from palm.core.workload.handle import WorkloadHandle
from palm.core.workload.owner import WorkloadOwner
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


def _row(engine: Any, place_id: str) -> Any | None:
    """Read the workload book by place id. Place id is the workload id."""
    if engine is None:
        return None
    get = getattr(engine, "get", None)
    if not callable(get):
        return None
    try:
        return get(place_id)
    except Exception:
        return None


@dataclass
class WorkloadPlaceSpawn:
    """Ensure/release structure places via an optional :class:`WorkloadEngine`."""

    engine: Any | None = None
    default_runtime: str = "local"
    default_kind: str = "workspace"

    def bind_engine(self, engine: Any | None) -> None:
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
        if not getattr(self.engine, "is_initialized", False):
            return PlaceSpawnResult(
                state="failed",
                reason="workload_engine_not_initialized",
                payload={"place_id": key},
            )

        existing = _row(self.engine, str(body.get("workload_id") or key))
        if existing is not None:
            status = getattr(existing, "status", None)
            wid = getattr(existing, "workload_id", None) or key
            if status is not None and not is_terminal(status):
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

        status = getattr(wl, "status", None)
        recorded = getattr(wl, "workload_id", None) or wid
        if status is WorkloadStatus.FAILED:
            return PlaceSpawnResult(
                state="failed",
                reason="workload_failed",
                handle=recorded,
                payload={
                    "place_id": key,
                    "workload_id": recorded,
                    "status": str(status),
                    "message": getattr(wl, "message", None)
                    or getattr(getattr(wl, "result", None), "message", None),
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
                "runtime": getattr(wl, "runtime", None),
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
        wid = getattr(row, "workload_id", None) or key
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

    engine: Any | None = None

    def bind_engine(self, engine: Any | None) -> None:
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
        if not getattr(self.engine, "is_initialized", False):
            return PlaceSpawnResult(
                state="failed",
                reason="workload_engine_not_initialized",
                payload={"place_id": key},
            )

        handle = _handle_from_payload(key, body)
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

        status = getattr(wl, "status", None)
        recorded = getattr(wl, "workload_id", None) or wid
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
        wid = getattr(row, "workload_id", None) or key
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
        status = getattr(wl, "status", None)
        recorded = getattr(wl, "workload_id", None) or wid
        if status is not None and not is_terminal(status):
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


def _handle_from_payload(place_id: str, body: dict[str, Any]) -> WorkloadHandle | None:
    raw = body.get("handle")
    if isinstance(raw, WorkloadHandle):
        return raw
    if isinstance(raw, dict):
        data = dict(raw)
        data.setdefault("workload_id", place_id)
        try:
            return WorkloadHandle.from_dict(data)
        except Exception:
            return None
    url = body.get("base_url")
    if url:
        return WorkloadHandle(workload_id=place_id, base_url=str(url))
    return None


def adopt_prefix_spawn_port(
    engine: Any | None = None,
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
    port.handles["__adopt_spawn__"] = hands
    return port


def workload_prefix_spawn_port(
    engine: Any | None = None,
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
    port.handles["__workload_spawn__"] = hands  # type: ignore[index]
    return port


def combined_structure_spawn_port(
    *,
    engine: Any | None = None,
    os_registry: Any | None = None,
) -> RegisteredPlaceSpawn:
    """``os:`` + ``workload:`` structure place routes on one port."""
    from palm.system.structure.place_spawn import (
        OsProcessRegistry,
        os_prefix_spawn_port,
    )

    os_port = os_prefix_spawn_port(registry=os_registry or OsProcessRegistry())
    wl_port = workload_prefix_spawn_port(engine=engine)
    ad_port = adopt_prefix_spawn_port(engine=engine)
    # Merge into one RegisteredPlaceSpawn with prefix routes.
    combined = RegisteredPlaceSpawn()
    combined.prefix_ensures.update(os_port.prefix_ensures)
    combined.prefix_releases.update(os_port.prefix_releases)
    combined.prefix_ensures.update(wl_port.prefix_ensures)
    combined.prefix_releases.update(wl_port.prefix_releases)
    combined.prefix_ensures.update(ad_port.prefix_ensures)
    combined.prefix_releases.update(ad_port.prefix_releases)
    os_reg = os_port.handles.get("__os_registry__")
    wl_hands = wl_port.handles.get("__workload_spawn__")
    ad_hands = ad_port.handles.get("__adopt_spawn__")
    if os_reg is not None:
        combined.handles["__os_registry__"] = os_reg
    if wl_hands is not None:
        combined.handles["__workload_spawn__"] = wl_hands
    if ad_hands is not None:
        combined.handles["__adopt_spawn__"] = ad_hands
    return combined


__all__ = [
    "AdoptPlaceSpawn",
    "WorkloadPlaceSpawn",
    "adopt_prefix_spawn_port",
    "combined_structure_spawn_port",
    "workload_prefix_spawn_port",
]
