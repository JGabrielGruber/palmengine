"""Local WorkloadRuntime — Palm's always-on trusted process runner.

Unlike **host** (default OFF, full-machine, multi-tenant unsafe), **local** is:

* always enabled
* constrained under a Palm-managed work root when provided
* isolation ``best_effort`` only (not claimed hermetic)

This makes WorkloadEngine real without NeonRoot CLI or host opt-in.
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


class LocalWorkloadRuntime(WorkloadRuntime):
    """Palm-managed subprocess runner (default ON)."""

    def __init__(
        self,
        *,
        name: str = "local",
        work_root: Path | str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._work_root = Path(work_root).resolve() if work_root else None
        self._live: dict[str, dict[str, Any]] = {}

    @classmethod
    def bind(
        cls,
        *,
        host_enabled: bool = False,
        work_root: Path | str | None = None,
    ) -> LocalWorkloadRuntime:
        del host_enabled
        root = Path(work_root) / "workloads" if work_root is not None else None
        return cls(work_root=root)

    def is_enabled(self) -> bool:
        return True

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            name=self.name,
            isolation_modes=frozenset({IsolationPolicy.BEST_EFFORT}),
            kinds=frozenset({"run", "workspace", "service"}),
            description=(
                "Palm-local process runner (always on; work under palm data_dir when set)"
            ),
            default_enabled=True,
            trust="local",
        )

    def health(self) -> RuntimeHealth:
        root = self._work_root
        detail: dict[str, Any] = {}
        if root is not None:
            detail["work_root"] = str(root)
            try:
                root.mkdir(parents=True, exist_ok=True)
                writable = os.access(root, os.W_OK)
            except OSError as exc:
                return RuntimeHealth(
                    name=self.name,
                    available=False,
                    enabled=True,
                    message=f"work_root not usable: {exc}",
                    detail=detail,
                )
            if not writable:
                return RuntimeHealth(
                    name=self.name,
                    available=False,
                    enabled=True,
                    message="work_root not writable",
                    detail=detail,
                )
        return RuntimeHealth(
            name=self.name,
            available=True,
            enabled=True,
            message="ready",
            detail=detail,
        )

    def start(
        self,
        workload_id: str,
        spec: WorkloadSpec,
        *,
        owner: WorkloadOwner | None = None,
    ) -> RuntimeStartOutcome:
        if spec.isolation is IsolationPolicy.HERMETIC:
            return RuntimeStartOutcome(
                status=WorkloadStatus.FAILED,
                result=WorkloadResult.fail(
                    "local runtime cannot honor isolation=hermetic "
                    "(use neonroot or peer)",
                    runtime=self.name,
                ),
                message="hermetic not supported on local",
            )
        if spec.isolation is IsolationPolicy.HOST:
            return RuntimeStartOutcome(
                status=WorkloadStatus.FAILED,
                result=WorkloadResult.fail(
                    "local runtime uses best_effort only; "
                    "use host runtime (opt-in) for isolation=host",
                    runtime=self.name,
                ),
                message="host isolation not supported on local",
            )

        if spec.kind in (WorkloadKind.WORKSPACE, WorkloadKind.SERVICE):
            return self._start_workspace(workload_id, spec, owner=owner)

        if spec.kind is not WorkloadKind.RUN:
            return RuntimeStartOutcome(
                status=WorkloadStatus.FAILED,
                result=WorkloadResult.fail(
                    f"local runtime unsupported kind={spec.kind}",
                    runtime=self.name,
                ),
            )
        if not spec.command:
            return RuntimeStartOutcome(
                status=WorkloadStatus.FAILED,
                result=WorkloadResult.fail("empty command", runtime=self.name),
            )

        workdir = self._resolve_workdir(spec, create_temp=True)
        result = self._run_argv(
            list(spec.command),
            workdir=workdir,
            env=spec.env,
            timeout_s=spec.timeout_s,
        )
        status = WorkloadStatus.STOPPED if result.success else WorkloadStatus.FAILED
        owned = workdir is not None and self._is_under_root(workdir)
        self._live[workload_id] = {
            "kind": "run",
            "result": result,
            "status": status,
            "owner": owner,
            "workdir": workdir,
            "owned_temp": owned and not (spec.workdir),
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
            return WorkloadResult.fail("unknown local workload", runtime=self.name)
        if entry.get("kind") != "workspace":
            return WorkloadResult.fail(
                "exec only valid on workspace/service",
                runtime=self.name,
            )
        merged = dict(entry.get("env") or {})
        if env:
            merged.update(env)
        return self._run_argv(
            list(command),
            workdir=entry.get("workdir"),
            env=merged,
            timeout_s=timeout_s,
        )

    def poll(self, workload_id: str) -> RuntimePollOutcome:
        entry = self._live.get(workload_id)
        if entry is None:
            return RuntimePollOutcome(
                status=WorkloadStatus.FAILED,
                message="unknown local workload",
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
            if self._work_root is not None and not self._is_under_root(path):
                # Force under palm root
                path = self._work_root / "ws" / path.name
            path.mkdir(parents=True, exist_ok=True)
            return path, False
        base = self._work_root if self._work_root is not None else Path(tempfile.gettempdir())
        base = base / "palm-local"
        base.mkdir(parents=True, exist_ok=True)
        path = Path(tempfile.mkdtemp(prefix="ws-", dir=str(base)))
        return path, True

    def _resolve_workdir(
        self, spec: WorkloadSpec, *, create_temp: bool
    ) -> Path | None:
        if spec.workdir:
            path = Path(spec.workdir)
            if not path.is_absolute() and self._work_root is not None:
                path = self._work_root / path
            path = path.resolve()
            if self._work_root is not None and not self._is_under_root(path):
                path = (self._work_root / "run" / path.name).resolve()
                path.mkdir(parents=True, exist_ok=True)
            return path
        if self._work_root is not None:
            d = self._work_root / "run"
            d.mkdir(parents=True, exist_ok=True)
            if create_temp:
                return Path(tempfile.mkdtemp(prefix="run-", dir=str(d)))
            return d
        if create_temp:
            return Path(tempfile.mkdtemp(prefix="palm-local-run-"))
        return None

    def _is_under_root(self, path: Path) -> bool:
        if self._work_root is None:
            return True
        try:
            path.resolve().relative_to(self._work_root.resolve())
            return True
        except ValueError:
            return False

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
                error=f"local run timed out after {timeout}s",
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


__all__ = ["LocalWorkloadRuntime"]
