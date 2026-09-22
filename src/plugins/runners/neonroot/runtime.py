"""NeonRoot WorkloadRuntime — hermetic isolation via NeonRoot CLI.

Maps portable WorkloadSpec → SpawnRequest (spec_map) → CLI. Sole NeonRoot path.
"""

from __future__ import annotations

from typing import Any

from palm.core.workload.owner import WorkloadOwner
from palm.core.workload.protocol import (
    RuntimeCapabilities,
    RuntimeHealth,
    RuntimePollOutcome,
    RuntimeStartOutcome,
    RuntimeStopOutcome,
    WorkloadRuntime,
)
from palm.core.workload.result import WorkloadResult
from palm.core.workload.spec import IsolationPolicy, WorkloadKind, WorkloadSpec
from palm.core.workload.status import WorkloadStatus
from plugins.runners.neonroot.spec_map import spawn_request_from_spec


class NeonrootWorkloadRuntime(WorkloadRuntime):
    """Hermetic one-shot runs through ``neonroot spawn``."""

    def __init__(self, *, name: str = "neonroot") -> None:
        super().__init__(name=name)
        self._live: dict[str, dict[str, Any]] = {}

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            name=self.name,
            isolation_modes=frozenset(
                {
                    IsolationPolicy.HERMETIC,
                    IsolationPolicy.BEST_EFFORT,
                }
            ),
            kinds=frozenset({"run"}),
            description="NeonRoot CLI hermetic spawn (image + argv)",
            default_enabled=True,
            trust="hermetic",
        )

    def is_enabled(self) -> bool:
        return True

    def health(self) -> RuntimeHealth:
        from plugins.runners.neonroot.cli import probe_neonroot

        probe = probe_neonroot()
        return RuntimeHealth(
            name=self.name,
            available=bool(probe.available),
            enabled=True,
            message=probe.version or probe.error or ("ready" if probe.available else "missing"),
            detail={
                "path": probe.path,
                "version": probe.version,
                "error": probe.error,
            },
        )

    def start(
        self,
        workload_id: str,
        spec: WorkloadSpec,
        *,
        owner: WorkloadOwner | None = None,
    ) -> RuntimeStartOutcome:
        if spec.kind is not WorkloadKind.RUN:
            msg = (
                f"neonroot runtime supports kind=run only (got kind={spec.kind}); "
                "warm workspace lands in a later 0.56 slice"
            )
            return self._fail(msg, error_class="unsupported_kind")

        health = self.health()
        if not health.available:
            msg = health.message or "neonroot CLI not available"
            return self._fail(msg, error_class="runtime_unavailable", detail=health.detail)

        try:
            req = spawn_request_from_spec(spec)
        except ValueError as exc:
            return self._fail(str(exc), error_class="invalid_spec")

        from plugins.runners.neonroot.spawn import resolve_repo_root, run_spawn_request

        try:
            payload = run_spawn_request(req, repo_root=resolve_repo_root())
        except (ValueError, RuntimeError) as exc:
            return self._fail(str(exc), error_class="start_failed")
        except Exception as exc:
            return self._fail(f"neonroot spawn failed: {exc}", error_class="start_failed")

        result = _payload_to_result(payload, runtime=self.name)
        if payload.get("timed_out") or payload.get("exit_code") is None:
            status = WorkloadStatus.FAILED
        elif int(payload.get("exit_code", 1)) != 0:
            status = WorkloadStatus.FAILED
        else:
            status = WorkloadStatus.STOPPED

        self._live[workload_id] = {
            "result": result,
            "status": status,
            "owner": owner,
            "payload": payload,
        }
        return RuntimeStartOutcome(
            status=status,
            result=result,
            message=result.error if status is WorkloadStatus.FAILED else None,
            runtime_meta={
                "neonroot": payload.get("neonroot"),
                "image": req.image,
                "error_class": payload.get("error_class"),
            },
        )

    def poll(self, workload_id: str) -> RuntimePollOutcome:
        entry = self._live.get(workload_id)
        if entry is None:
            return RuntimePollOutcome(
                status=WorkloadStatus.FAILED,
                message="unknown neonroot workload",
            )
        return RuntimePollOutcome(
            status=entry["status"],
            result=entry.get("result"),
        )

    def stop(self, workload_id: str) -> RuntimeStopOutcome:
        entry = self._live.pop(workload_id, None)
        if entry is None:
            return RuntimeStopOutcome(status=WorkloadStatus.STOPPED)
        return RuntimeStopOutcome(
            status=entry.get("status", WorkloadStatus.STOPPED),
            result=entry.get("result"),
        )

    def _fail(
        self,
        message: str,
        *,
        error_class: str,
        detail: dict[str, Any] | None = None,
    ) -> RuntimeStartOutcome:
        meta: dict[str, Any] = {"runtime": self.name, "error_class": error_class}
        if detail:
            meta["detail"] = dict(detail)
        return RuntimeStartOutcome(
            status=WorkloadStatus.FAILED,
            result=WorkloadResult.fail(message, runtime=self.name, error_class=error_class),
            message=message,
            runtime_meta=meta,
        )


def _payload_to_result(payload: dict[str, Any], *, runtime: str) -> WorkloadResult:
    exit_code = payload.get("exit_code")
    error_class = payload.get("error_class")
    if exit_code is None:
        return WorkloadResult.fail(
            str(payload.get("error") or "spawn produced no exit code"),
            exit_code=1,
            stdout_tail=str(payload.get("stdout_tail") or ""),
            stderr_tail=str(payload.get("stderr_tail") or ""),
            runtime=runtime,
            duration_s=payload.get("duration_s"),
            error_class=error_class or "start_failed",
        )
    code = int(exit_code)
    meta: dict[str, Any] = {"runtime": runtime, "image": payload.get("image")}
    if error_class:
        meta["error_class"] = error_class
    if code != 0:
        return WorkloadResult(
            exit_code=code,
            stdout_tail=str(payload.get("stdout_tail") or ""),
            stderr_tail=str(payload.get("stderr_tail") or ""),
            duration_s=(
                float(payload["duration_s"])
                if payload.get("duration_s") is not None
                else None
            ),
            error=str(payload.get("error") or f"exit {code}"),
            runtime_meta=meta,
        )
    return WorkloadResult.ok(
        exit_code=0,
        stdout_tail=str(payload.get("stdout_tail") or ""),
        stderr_tail=str(payload.get("stderr_tail") or ""),
        duration_s=(
            float(payload["duration_s"]) if payload.get("duration_s") is not None else None
        ),
        **meta,
    )


__all__ = ["NeonrootWorkloadRuntime"]
