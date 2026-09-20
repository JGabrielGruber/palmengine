"""WorkloadEngine — pure lifecycle: place/start/exec/status/stop.

No neonroot/docker/k8s/SSH clients. Runtimes resolve from the core registry
or injected instances. Optional event publisher is injected (same pattern as
ResourceEngine) so core stays free of outer Palm packages.
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable, Mapping
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.workload.events import (
    WORKLOAD_EVENT_FAILED,
    WORKLOAD_EVENT_READY,
    WORKLOAD_EVENT_STARTED,
    WORKLOAD_EVENT_STOPPED,
)
from palm.core.workload.exceptions import (
    WorkloadNotFoundError,
    WorkloadPlacementError,
    WorkloadPolicyError,
    WorkloadSpecError,
    WorkloadStateError,
)
from palm.core.workload.handle import WorkloadHandle
from palm.core.workload.owner import WorkloadOwner
from palm.core.workload.protocol import WorkloadRuntime
from palm.core.workload.record import Workload
from palm.core.workload.registry import workload_runtime_registry
from palm.core.workload.result import WorkloadResult
from palm.core.workload.spec import (
    IsolationPolicy,
    LifecyclePolicy,
    WorkloadKind,
    WorkloadSpec,
)
from palm.core.workload.status import (
    WorkloadStatus,
    can_transition,
    is_exec_allowed,
    is_terminal,
)

EventPublisher = Callable[[str, dict[str, Any]], None]
RuntimeFactory = Callable[[str], WorkloadRuntime]


class WorkloadEngine(BasePalmEngine):
    """In-memory workload lifecycle engine (durable projection later in service)."""

    def __init__(self) -> None:
        super().__init__(name="workload")
        self._lock = threading.RLock()
        self._workloads: dict[str, Workload] = {}
        self._idempotency: dict[str, str] = {}  # owner+key → workload_id
        self._runtimes: dict[str, WorkloadRuntime] = {}
        self._publish_event: EventPublisher | None = None
        self._runtime_factory: RuntimeFactory | None = None
        self._default_runtime: str | None = None

    def _do_initialize(self, **options: Any) -> None:
        self._publish_event = options.get("publish_event")
        self._runtime_factory = options.get("runtime_factory")
        self._default_runtime = options.get("default_runtime")
        # Optional pre-bound runtime instances (tests / host wiring)
        bound = options.get("runtimes") or {}
        if isinstance(bound, dict):
            for name, runtime in bound.items():
                if not isinstance(runtime, WorkloadRuntime):
                    raise TypeError(
                        f"runtimes[{name!r}] must be a WorkloadRuntime, got {type(runtime)}"
                    )
                self._runtimes[str(name)] = runtime

    def _do_shutdown(self) -> None:
        with self._lock:
            # Best-effort stop of non-terminal workloads Palm still tracks
            for wl in list(self._workloads.values()):
                if not is_terminal(wl.status):
                    try:
                        self._stop_unlocked(wl.workload_id)
                    except Exception:
                        pass
            self._workloads.clear()
            self._idempotency.clear()
            self._runtimes.clear()
            self._publish_event = None
            self._runtime_factory = None

    # --- runtime resolution -------------------------------------------------

    def register_runtime(self, runtime: WorkloadRuntime) -> None:
        """Bind a live runtime instance (also used by tests)."""
        with self._lock:
            self._runtimes[runtime.name] = runtime

    def _resolve_runtime(self, name: str) -> WorkloadRuntime:
        if name in self._runtimes:
            return self._runtimes[name]
        if self._runtime_factory is not None:
            runtime = self._runtime_factory(name)
            self._runtimes[name] = runtime
            return runtime
        cls = workload_runtime_registry.get(name)
        runtime = cls(name=name)
        self._runtimes[name] = runtime
        return runtime

    def _select_runtime_name(self, spec: WorkloadSpec) -> str:
        """Minimal pure-core placement: honor explicit runtime; fail closed."""
        placement = spec.placement
        if placement.runtime:
            name = placement.runtime
            if name in placement.reject_runtimes:
                raise WorkloadPlacementError(
                    f"Requested runtime {name!r} is in reject_runtimes"
                )
            return name
        if self._default_runtime:
            if self._default_runtime in placement.reject_runtimes:
                raise WorkloadPlacementError(
                    f"Default runtime {self._default_runtime!r} is rejected by Spec"
                )
            return self._default_runtime
        raise WorkloadPlacementError(
            "No runtime selected: set placement.runtime or engine default_runtime"
        )

    def _enforce_isolation_policy(
        self, spec: WorkloadSpec, runtime: WorkloadRuntime
    ) -> None:
        caps = runtime.capabilities()
        if not caps.supports_isolation(spec.isolation):
            raise WorkloadPolicyError(
                f"Runtime {runtime.name!r} does not support isolation={spec.isolation!s}; "
                f"supports {[str(m) for m in sorted(caps.isolation_modes, key=str)]}"
            )
        # Hard rule: hermetic must never land on host runtime (VISION §13 / ADR-024)
        if (
            spec.isolation is IsolationPolicy.HERMETIC
            and runtime.name == "host"
        ):
            raise WorkloadPolicyError(
                "Hermetic isolation cannot select host runtime"
            )

    # --- public API ---------------------------------------------------------

    def start(
        self,
        spec: WorkloadSpec,
        *,
        owner: WorkloadOwner | None = None,
        workload_id: str | None = None,
        idempotency_key: str | None = None,
        host_id: str | None = None,
    ) -> Workload:
        """Validate Spec, place runtime, start allocation. Returns live Workload snapshot."""
        if not self.is_initialized:
            raise WorkloadStateError("WorkloadEngine is not initialized")

        owner = owner or WorkloadOwner()
        with self._lock:
            if idempotency_key:
                idem_id = self._idempotency_lookup(owner, idempotency_key)
                if idem_id is not None:
                    return self._workloads[idem_id].snapshot()

            runtime_name = self._select_runtime_name(spec)
            runtime = self._resolve_runtime(runtime_name)
            if not runtime.is_enabled():
                raise WorkloadPolicyError(
                    f"Runtime {runtime_name!r} is disabled "
                    f"(host runtime requires workload_host_enabled / PALM_WORKLOAD_HOST_ENABLED)"
                )
            self._enforce_isolation_policy(spec, runtime)

            wid = workload_id or str(uuid.uuid4())
            if wid in self._workloads:
                raise WorkloadStateError(f"Workload id {wid!r} already exists")

            wl = Workload(
                workload_id=wid,
                spec=spec,
                status=WorkloadStatus.PENDING,
                runtime=runtime_name,
                owner=owner,
                host_id=host_id or spec.placement.host_id,
                idempotency_key=idempotency_key,
            )
            self._workloads[wid] = wl
            if idempotency_key:
                self._idempotency[self._idempotency_index(owner, idempotency_key)] = wid

            self._transition(wl, WorkloadStatus.STARTING)
            self._emit(WORKLOAD_EVENT_STARTED, wl)

            try:
                outcome = runtime.start(wid, spec, owner=owner)
            except Exception as exc:
                self._transition(wl, WorkloadStatus.FAILED, message=str(exc))
                wl.result = WorkloadResult.fail(str(exc), runtime=runtime_name)
                self._emit(WORKLOAD_EVENT_FAILED, wl)
                return wl.snapshot()

            self._apply_start_outcome(wl, outcome)
            return wl.snapshot()

    def adopt(
        self,
        workload_id: str,
        handle: WorkloadHandle | dict[str, Any] | str | None = None,
        *,
        spec: WorkloadSpec | None = None,
        owner: WorkloadOwner | None = None,
        host_id: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> Workload:
        """Adopt an existing running body into the workload book as READY.

        Does not start a runner. Requires non-empty workload_id and a valid handle
        (at least base_url or connection hints). Release of an adopted workload unbinds.
        """
        if not self.is_initialized:
            raise WorkloadStateError("WorkloadEngine is not initialized")

        wid = str(workload_id or "").strip()
        if not wid:
            raise WorkloadSpecError("workload_id must not be empty")

        if handle is None:
            raise WorkloadSpecError("handle is required to adopt a workload")

        if isinstance(handle, WorkloadHandle):
            handle_obj = handle
        elif isinstance(handle, dict):
            h_dict = dict(handle)
            if "workload_id" not in h_dict:
                h_dict["workload_id"] = wid
            handle_obj = WorkloadHandle.from_dict(h_dict)
        elif isinstance(handle, str):
            handle_obj = WorkloadHandle(workload_id=wid, base_url=handle)
        else:
            raise WorkloadSpecError(f"Unsupported handle type: {type(handle)}")

        if not handle_obj.base_url and not handle_obj.endpoints and not handle_obj.connection_hints:
            raise WorkloadSpecError("handle must provide base_url or connection hints")

        with self._lock:
            if wid in self._workloads:
                existing = self._workloads[wid]
                if existing.runtime == "adopted" and existing.status is WorkloadStatus.READY:
                    existing.handle = handle_obj
                    existing.touch()
                    return existing.snapshot()
                raise WorkloadStateError(f"Workload id {wid!r} already exists")

            if spec is None:
                spec_labels = {"adopted": "true"}
                if labels:
                    spec_labels.update({str(k): str(v) for k, v in labels.items()})
                spec = WorkloadSpec(
                    kind=WorkloadKind.SERVICE,
                    isolation=IsolationPolicy.BEST_EFFORT,
                    lifecycle=LifecyclePolicy.LEASE,
                    labels=spec_labels,
                )

            owner = owner or WorkloadOwner()
            wl = Workload(
                workload_id=wid,
                spec=spec,
                status=WorkloadStatus.READY,
                runtime="adopted",
                owner=owner,
                handle=handle_obj,
                host_id=host_id or spec.placement.host_id,
            )
            self._workloads[wid] = wl
            self._emit(WORKLOAD_EVENT_READY, wl)
            return wl.snapshot()

    def exec(
        self,
        workload_id: str,
        command: list[str] | tuple[str, ...],
        *,
        timeout_s: float | None = None,
        env: dict[str, str] | None = None,
    ) -> WorkloadResult:
        """Execute argv on a READY workspace/service."""
        if not self.is_initialized:
            raise WorkloadStateError("WorkloadEngine is not initialized")
        if not command:
            raise WorkloadStateError("exec requires a non-empty argv command")
        if isinstance(command, str):
            raise WorkloadStateError("command must be an argv list, not a shell string")

        with self._lock:
            wl = self._require(workload_id)
            if not is_exec_allowed(wl.status):
                raise WorkloadStateError(
                    f"exec only allowed when READY (current={wl.status})"
                )
            if wl.runtime == "adopted":
                raise WorkloadStateError("exec is not valid on adopted workloads")
            if wl.spec.kind is WorkloadKind.RUN:
                raise WorkloadStateError("exec is not valid on kind=run workloads")

            runtime = self._resolve_runtime(wl.runtime)
            # Optional RUNNING while exec is in flight (for long polls)
            prior = wl.status
            self._transition(wl, WorkloadStatus.RUNNING)
            try:
                result = runtime.exec(
                    workload_id,
                    tuple(str(c) for c in command),
                    timeout_s=timeout_s,
                    env=env,
                )
            except Exception as exc:
                self._transition(wl, WorkloadStatus.FAILED, message=str(exc))
                wl.result = WorkloadResult.fail(str(exc), runtime=wl.runtime)
                self._emit(WORKLOAD_EVENT_FAILED, wl)
                return wl.result

            wl.result = result
            if result.success:
                self._transition(wl, prior)  # back to READY
            else:
                # Non-zero exit does not destroy the workspace; return to READY
                self._transition(wl, WorkloadStatus.READY, message=result.error)
            return result

    def status(self, workload_id: str, *, refresh: bool = False) -> Workload:
        """Return workload snapshot; optionally poll the runtime."""
        if not self.is_initialized:
            raise WorkloadStateError("WorkloadEngine is not initialized")
        with self._lock:
            wl = self._require(workload_id)
            if refresh and not is_terminal(wl.status):
                if wl.runtime == "adopted":
                    return wl.snapshot()
                runtime = self._resolve_runtime(wl.runtime)
                try:
                    outcome = runtime.poll(workload_id)
                except Exception as exc:
                    self._transition(wl, WorkloadStatus.FAILED, message=str(exc))
                    wl.result = WorkloadResult.fail(str(exc), runtime=wl.runtime)
                    self._emit(WORKLOAD_EVENT_FAILED, wl)
                else:
                    self._apply_poll_outcome(wl, outcome)
            return wl.snapshot()

    def stop(self, workload_id: str) -> Workload:
        """Idempotent stop. Terminal workloads return as-is."""
        if not self.is_initialized:
            raise WorkloadStateError("WorkloadEngine is not initialized")
        with self._lock:
            return self._stop_unlocked(workload_id)

    def get(self, workload_id: str) -> Workload:
        """Return snapshot without refreshing runtime."""
        if not self.is_initialized:
            raise WorkloadStateError("WorkloadEngine is not initialized")
        with self._lock:
            return self._require(workload_id).snapshot()

    def list(
        self,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        session_id: str | None = None,
        status: WorkloadStatus | None = None,
        runtime: str | None = None,
    ) -> list[Workload]:
        """Filter tracked workloads (in-memory index)."""
        if not self.is_initialized:
            raise WorkloadStateError("WorkloadEngine is not initialized")
        with self._lock:
            out: list[Workload] = []
            for wl in self._workloads.values():
                if status is not None and wl.status is not status:
                    continue
                if runtime is not None and wl.runtime != runtime:
                    continue
                if job_id is not None or instance_id is not None or session_id is not None:
                    if not wl.owner.matches(
                        job_id=job_id,
                        instance_id=instance_id,
                        session_id=session_id,
                    ):
                        continue
                out.append(wl.snapshot())
            return out

    def stop_owned(
        self,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        session_id: str | None = None,
    ) -> list[Workload]:
        """Stop all non-terminal workloads matching owner filters (cancel path)."""
        if not self.is_initialized:
            raise WorkloadStateError("WorkloadEngine is not initialized")
        with self._lock:
            targets = [
                wl.workload_id
                for wl in self._workloads.values()
                if not is_terminal(wl.status)
                and wl.owner.matches(
                    job_id=job_id,
                    instance_id=instance_id,
                    session_id=session_id,
                )
            ]
            return [self._stop_unlocked(wid) for wid in targets]

    def runtimes(self) -> list[dict[str, Any]]:
        """Doctor-oriented view of bound + registered runtimes (incl. health)."""
        with self._lock:
            names = set(self._runtimes) | set(workload_runtime_registry.names())
            rows: list[dict[str, Any]] = []
            for name in sorted(names):
                try:
                    rt = self._resolve_runtime(name)
                    caps = rt.capabilities()
                    health = rt.health()
                    rows.append(
                        {
                            "name": name,
                            "bound": name in self._runtimes,
                            "enabled": rt.is_enabled(),
                            "isolation_modes": [
                                str(m) for m in sorted(caps.isolation_modes, key=str)
                            ],
                            "kinds": sorted(caps.kinds),
                            "default_enabled": caps.default_enabled,
                            "trust": caps.trust,
                            "description": caps.description,
                            "health": health.to_dict(),
                        }
                    )
                except Exception as exc:
                    rows.append({"name": name, "error": str(exc)})
            return rows

    def doctor(self) -> dict[str, Any]:
        """Structured workload-plane doctor snapshot (engine + runners)."""
        if not self.is_initialized:
            return {
                "engine_initialized": False,
                "active_workloads": 0,
                "runtimes": [],
                "issues": ["WorkloadEngine is not initialized"],
            }
        rows = self.runtimes()
        issues: list[str] = []
        enabled_any = False
        for row in rows:
            if row.get("error"):
                issues.append(f"runtime {row.get('name')}: {row['error']}")
                continue
            health = row.get("health") or {}
            if row.get("enabled"):
                enabled_any = True
            if row.get("enabled") and not health.get("available"):
                issues.append(
                    f"runtime {row.get('name')!r} is enabled but unavailable: "
                    f"{health.get('message') or 'unknown'}"
                )
            if row.get("name") == "host" and row.get("enabled"):
                issues.append(
                    "host WorkloadRuntime is ENABLED — not multi-tenant safe "
                    "(PALM_WORKLOAD_HOST_ENABLED)"
                )
        if not enabled_any:
            issues.append("no WorkloadRuntime is enabled")
        with self._lock:
            active = sum(
                1 for wl in self._workloads.values() if not is_terminal(wl.status)
            )
            total = len(self._workloads)
        return {
            "engine_initialized": True,
            "default_runtime": self._default_runtime,
            "active_workloads": active,
            "tracked_workloads": total,
            "runtimes": rows,
            "issues": issues,
            "note": (
                "local = always-on Palm process runner; host = opt-in unsafe; "
                "neonroot = hermetic external CLI"
            ),
        }

    # --- internals ----------------------------------------------------------

    def _require(self, workload_id: str) -> Workload:
        try:
            return self._workloads[workload_id]
        except KeyError as exc:
            raise WorkloadNotFoundError(f"Unknown workload {workload_id!r}") from exc

    def _stop_unlocked(self, workload_id: str) -> Workload:
        wl = self._require(workload_id)
        if is_terminal(wl.status):
            return wl.snapshot()

        if wl.runtime == "adopted":
            self._transition(wl, WorkloadStatus.STOPPED, message="adopt_unbound")
            self._emit(WORKLOAD_EVENT_STOPPED, wl)
            return wl.snapshot()

        self._transition(wl, WorkloadStatus.STOPPING)
        runtime = self._resolve_runtime(wl.runtime)
        try:
            outcome = runtime.stop(workload_id)
        except Exception as exc:
            wl.leak_recorded = True
            self._transition(wl, WorkloadStatus.FAILED, message=str(exc))
            wl.result = WorkloadResult.fail(str(exc), runtime=wl.runtime)
            self._emit(WORKLOAD_EVENT_FAILED, wl)
            return wl.snapshot()

        if outcome.leaked:
            wl.leak_recorded = True
        if outcome.result is not None:
            wl.result = outcome.result
        if outcome.runtime_meta:
            wl.runtime_meta.update(outcome.runtime_meta)

        target = outcome.status
        if target not in (WorkloadStatus.STOPPED, WorkloadStatus.FAILED):
            target = WorkloadStatus.STOPPED
        self._transition(wl, target, message=outcome.message)
        if wl.status is WorkloadStatus.FAILED:
            self._emit(WORKLOAD_EVENT_FAILED, wl)
        else:
            self._emit(WORKLOAD_EVENT_STOPPED, wl)
        return wl.snapshot()

    def _apply_start_outcome(self, wl: Workload, outcome: Any) -> None:
        if outcome.handle is not None:
            wl.handle = outcome.handle
        if outcome.result is not None:
            wl.result = outcome.result
        if outcome.runtime_meta:
            wl.runtime_meta.update(outcome.runtime_meta)
        status = outcome.status
        if not can_transition(wl.status, status) and status is not wl.status:
            # Runtime returned illegal status — fail closed
            self._transition(
                wl,
                WorkloadStatus.FAILED,
                message=f"Runtime returned illegal status {status} from STARTING",
            )
            self._emit(WORKLOAD_EVENT_FAILED, wl)
            return
        self._transition(wl, status, message=outcome.message)
        if status is WorkloadStatus.READY:
            self._emit(WORKLOAD_EVENT_READY, wl)
        elif status is WorkloadStatus.FAILED:
            self._emit(WORKLOAD_EVENT_FAILED, wl)
        elif status is WorkloadStatus.STOPPED:
            self._emit(WORKLOAD_EVENT_STOPPED, wl)
        elif status is WorkloadStatus.RUNNING:
            # still live; started already emitted
            pass

    def _apply_poll_outcome(self, wl: Workload, outcome: Any) -> None:
        if outcome.handle is not None:
            wl.handle = outcome.handle
        if outcome.result is not None:
            wl.result = outcome.result
        if outcome.runtime_meta:
            wl.runtime_meta.update(outcome.runtime_meta)
        status = outcome.status
        if status is wl.status:
            wl.touch()
            return
        if not can_transition(wl.status, status):
            self._transition(
                wl,
                WorkloadStatus.FAILED,
                message=f"Illegal poll transition {wl.status} → {status}",
            )
            self._emit(WORKLOAD_EVENT_FAILED, wl)
            return
        self._transition(wl, status, message=outcome.message)
        if status is WorkloadStatus.READY:
            self._emit(WORKLOAD_EVENT_READY, wl)
        elif status is WorkloadStatus.FAILED:
            self._emit(WORKLOAD_EVENT_FAILED, wl)
        elif status is WorkloadStatus.STOPPED:
            self._emit(WORKLOAD_EVENT_STOPPED, wl)

    def _transition(
        self,
        wl: Workload,
        next_status: WorkloadStatus,
        *,
        message: str | None = None,
    ) -> None:
        if wl.status is next_status:
            if message is not None:
                wl.message = message
            wl.touch()
            return
        if not can_transition(wl.status, next_status):
            raise WorkloadStateError(
                f"Illegal status transition {wl.status} → {next_status} "
                f"for workload {wl.workload_id!r}"
            )
        wl.status = next_status
        if message is not None:
            wl.message = message
        wl.touch()

    def _emit(self, event_type: str, wl: Workload) -> None:
        if self._publish_event is None:
            return
        payload: dict[str, Any] = {
            "workload_id": wl.workload_id,
            "status": str(wl.status),
            "runtime": wl.runtime,
            "kind": str(wl.spec.kind),
            "owner": wl.owner.to_dict(),
            "labels": dict(wl.spec.labels),
        }
        if wl.host_id is not None:
            payload["host_id"] = wl.host_id
        if wl.result is not None:
            payload["exit_code"] = wl.result.exit_code
            if wl.result.artifact_refs:
                payload["artifact_refs"] = list(wl.result.artifact_refs)
        try:
            self._publish_event(event_type, payload)
        except Exception:
            # Observability must not break lifecycle
            pass

    @staticmethod
    def _idempotency_index(owner: WorkloadOwner, key: str) -> str:
        parts = [
            owner.job_id or "",
            owner.instance_id or "",
            owner.session_id or "",
            owner.lease_id or "",
            key,
        ]
        return "|".join(parts)

    def _idempotency_lookup(
        self, owner: WorkloadOwner, key: str
    ) -> str | None:
        return self._idempotency.get(self._idempotency_index(owner, key))
