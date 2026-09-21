"""Host WorkloadRuntime — local subprocess isolation (default OFF).

Supports:
* kind=run — one-shot argv → STOPPED/FAILED
* kind=workspace / service — READY warm box; exec runs argv in workdir

Unsupported as multi-tenant isolation. Dogfood / slim Compose only.
See ADR-024 D6 · VISION-0.56 §7.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from palm.core.workload.handle import WorkloadHandle
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

_DEFAULT_TAIL = 8000


class HostWorkloadRuntime(WorkloadRuntime):
    """Run argv on the Palm host process machine via subprocess."""

    def __init__(
        self,
        *,
        name: str = "host",
        enabled: bool = False,
        work_root: Path | str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._enabled = bool(enabled)
        self._work_root = Path(work_root).resolve() if work_root else None
        self._live: dict[str, dict[str, Any]] = {}

    @classmethod
    def bind(
        cls,
        *,
        host_enabled: bool = False,
        work_root: Path | str | None = None,
    ) -> HostWorkloadRuntime:
        return cls(enabled=host_enabled, work_root=work_root)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)

    def is_enabled(self) -> bool:
        return self._enabled

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            name=self.name,
            isolation_modes=frozenset({IsolationPolicy.HOST, IsolationPolicy.BEST_EFFORT}),
            kinds=frozenset({"run", "workspace", "service"}),
            description="Full-machine subprocess (default OFF; not multi-tenant safe)",
            default_enabled=False,
            trust="host",
        )

    def health(self) -> RuntimeHealth:
        enabled = self.is_enabled()
        return RuntimeHealth(
            name=self.name,
            available=enabled,
            enabled=enabled,
            message=(
                "enabled (unsafe multi-tenant)"
                if enabled
                else "disabled (set PALM_WORKLOAD_HOST_ENABLED=1)"
            ),
            detail={"work_root": str(self._work_root) if self._work_root else None},
        )

    def start(
        self,
        workload_id: str,
        spec: WorkloadSpec,
        *,
        owner: WorkloadOwner | None = None,
    ) -> RuntimeStartOutcome:
        if not self._enabled:
            return RuntimeStartOutcome(
                status=WorkloadStatus.FAILED,
                result=WorkloadResult.fail(
                    "host runtime is disabled "
                    "(set PALM_WORKLOAD_HOST_ENABLED=1 / workload_host_enabled)",
                    runtime=self.name,
                ),
                message="host runtime disabled",
            )

        if spec.kind in (WorkloadKind.WORKSPACE, WorkloadKind.SERVICE):
            return self._start_workspace(workload_id, spec, owner=owner)

        if spec.kind is not WorkloadKind.RUN:
            return RuntimeStartOutcome(
                status=WorkloadStatus.FAILED,
                result=WorkloadResult.fail(
                    f"host runtime unsupported kind={spec.kind}",
                    runtime=self.name,
                ),
                message="unsupported kind",
            )
        if not spec.command:
            return RuntimeStartOutcome(
                status=WorkloadStatus.FAILED,
                result=WorkloadResult.fail("empty command", runtime=self.name),
            )

        workdir = self._resolve_workdir(spec, create_temp=False)
        result = self._run_argv(
            list(spec.command),
            workdir=workdir,
            env=spec.env,
            timeout_s=spec.timeout_s,
        )
        status = WorkloadStatus.STOPPED if result.success else WorkloadStatus.FAILED
        self._live[workload_id] = {
            "kind": "run",
            "result": result,
            "status": status,
            "owner": owner,
            "workdir": workdir,
            "owned_temp": False,
        }
        return RuntimeStartOutcome(status=status, result=result)

    def _start_workspace(
        self,
        workload_id: str,
        spec: WorkloadSpec,
        *,
        owner: WorkloadOwner | None,
    ) -> RuntimeStartOutcome:
        workdir, owned_temp = self._allocate_workspace_dir(spec)
        handle = WorkloadHandle(
            workload_id=workload_id,
            connection_hints={
                "runtime": self.name,
                "workdir": str(workdir),
                "kind": str(spec.kind),
            },
        )
        self._live[workload_id] = {
            "kind": "workspace",
            "status": WorkloadStatus.READY,
            "owner": owner,
            "workdir": workdir,
            "owned_temp": owned_temp,
            "env": dict(spec.env),
            "spec": spec,
            "handle": handle,
        }
        return RuntimeStartOutcome(status=WorkloadStatus.READY, handle=handle)

    def exec(
        self,
        workload_id: str,
        command: list[str] | tuple[str, ...],
        *,
        timeout_s: float | None = None,
        env: dict[str, str] | None = None,
    ) -> WorkloadResult:
        entry = self._live.get(workload_id)
        if entry is None:
            return WorkloadResult.fail("unknown host workload", runtime=self.name)
        if entry.get("kind") != "workspace":
            return WorkloadResult.fail(
                "exec only valid on workspace/service host workloads",
                runtime=self.name,
            )
        if entry.get("status") is not WorkloadStatus.READY:
            return WorkloadResult.fail(
                f"workspace not READY (status={entry.get('status')})",
                runtime=self.name,
            )
        merged_env = dict(entry.get("env") or {})
        if env:
            merged_env.update(env)
        return self._run_argv(
            list(command),
            workdir=entry.get("workdir"),
            env=merged_env,
            timeout_s=timeout_s,
        )

    def poll(self, workload_id: str) -> RuntimePollOutcome:
        entry = self._live.get(workload_id)
        if entry is None:
            return RuntimePollOutcome(
                status=WorkloadStatus.FAILED,
                message="unknown host workload",
            )
        return RuntimePollOutcome(
            status=entry["status"],
            result=entry.get("result"),
            handle=entry.get("handle"),
        )

    def stop(self, workload_id: str) -> RuntimeStopOutcome:
        entry = self._live.pop(workload_id, None)
        if entry is None:
            return RuntimeStopOutcome(status=WorkloadStatus.STOPPED)
        if entry.get("owned_temp"):
            workdir = entry.get("workdir")
            if isinstance(workdir, Path) and workdir.is_dir():
                shutil.rmtree(workdir, ignore_errors=True)
        return RuntimeStopOutcome(
            status=WorkloadStatus.STOPPED,
            result=entry.get("result"),
        )

    def _allocate_workspace_dir(self, spec: WorkloadSpec) -> tuple[Path, bool]:
        if spec.workdir:
            path = Path(spec.workdir)
            if not path.is_absolute() and self._work_root is not None:
                path = self._work_root / path
            path = path.resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path, False
        base = self._work_root if self._work_root is not None else Path(tempfile.gettempdir())
        base.mkdir(parents=True, exist_ok=True)
        path = Path(tempfile.mkdtemp(prefix="palm-host-ws-", dir=str(base)))
        return path, True

    def _resolve_workdir(
        self, spec: WorkloadSpec, *, create_temp: bool
    ) -> Path | None:
        if spec.workdir:
            path = Path(spec.workdir)
            if not path.is_absolute() and self._work_root is not None:
                path = self._work_root / path
            return path.resolve()
        if self._work_root is not None:
            return self._work_root
        if create_temp:
            return Path(tempfile.mkdtemp(prefix="palm-host-run-"))
        return None

    def _run_argv(
        self,
        argv: list[str],
        *,
        workdir: Path | None,
        env: dict[str, str] | None,
        timeout_s: float | None,
    ) -> WorkloadResult:
        full_env = os.environ.copy()
        if env:
            full_env.update({str(k): str(v) for k, v in env.items()})
        timeout = float(timeout_s) if timeout_s is not None else 3600.0
        started = time.monotonic()
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                cwd=str(workdir) if workdir is not None else None,
                env=full_env,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            return WorkloadResult(
                exit_code=124,
                stdout_tail=_tail(stdout),
                stderr_tail=_tail(stderr or f"timeout after {timeout}s"),
                duration_s=round(duration, 3),
                error=f"host run timed out after {timeout}s",
                runtime_meta={"runtime": self.name, "argv": argv},
            )
        except OSError as exc:
            return WorkloadResult.fail(str(exc), runtime=self.name)

        duration = time.monotonic() - started
        return WorkloadResult(
            exit_code=int(proc.returncode),
            stdout_tail=_tail(proc.stdout or ""),
            stderr_tail=_tail(proc.stderr or ""),
            duration_s=round(duration, 3),
            error=None if proc.returncode == 0 else f"exit {proc.returncode}",
            runtime_meta={
                "runtime": self.name,
                "argv": argv,
                "cwd": str(workdir) if workdir else None,
            },
        )


def _tail(text: str, limit: int = _DEFAULT_TAIL) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


__all__ = ["HostWorkloadRuntime"]
