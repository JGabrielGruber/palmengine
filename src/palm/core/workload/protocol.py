"""WorkloadRuntime — base adapter contract (pure core Protocol/ABC).

Concrete adapters (host, neonroot, ssh, palm, …) live in ``palm.runners`` and
register into the core registry at bootstrap. Core never imports those packages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from palm.core.workload.handle import WorkloadHandle
from palm.core.workload.owner import WorkloadOwner
from palm.core.workload.result import WorkloadResult
from palm.core.workload.spec import IsolationPolicy, WorkloadSpec
from palm.core.workload.status import WorkloadStatus


@dataclass(frozen=True, slots=True)
class RuntimeCapabilities:
    """What a runtime can honor (doctor + placement)."""

    name: str
    isolation_modes: frozenset[IsolationPolicy]
    kinds: frozenset[str]
    description: str = ""
    default_enabled: bool = False
    #: Trust class for doctor / placement (local always-on vs host opt-in vs external CLI)
    trust: str = "external"  # local | host | hermetic | mesh | external

    def supports_isolation(self, isolation: IsolationPolicy) -> bool:
        return isolation in self.isolation_modes


@dataclass(frozen=True, slots=True)
class RuntimeHealth:
    """Standard runner probe — every WorkloadRuntime reports this shape."""

    name: str
    available: bool
    enabled: bool
    message: str = ""
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "name": self.name,
            "available": self.available,
            "enabled": self.enabled,
            "message": self.message,
        }
        if self.detail:
            out["detail"] = dict(self.detail)
        return out


@dataclass(frozen=True, slots=True)
class RuntimeStartOutcome:
    """Result of runtime.start — engine maps this onto Workload status."""

    status: WorkloadStatus
    handle: WorkloadHandle | None = None
    result: WorkloadResult | None = None
    message: str | None = None
    runtime_meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RuntimePollOutcome:
    """Result of runtime.poll / status refresh."""

    status: WorkloadStatus
    result: WorkloadResult | None = None
    handle: WorkloadHandle | None = None
    message: str | None = None
    runtime_meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RuntimeStopOutcome:
    """Result of runtime.stop — stop is idempotent at the engine layer."""

    status: WorkloadStatus
    result: WorkloadResult | None = None
    message: str | None = None
    leaked: bool = False
    runtime_meta: dict[str, Any] = field(default_factory=dict)


class WorkloadRuntime(ABC):
    """Adapter that maps WorkloadSpec to a concrete isolation backend."""

    def __init__(self, *, name: str) -> None:
        self.name = name

    @classmethod
    def bind(
        cls,
        *,
        host_enabled: bool = False,
        work_root: Path | str | None = None,
    ) -> WorkloadRuntime:
        """Build one instance for the engine.

        The workload plane walks the registry and calls this. A runner that
        needs ``host_enabled`` or ``work_root`` overrides this method.
        """
        del host_enabled, work_root
        return cls()

    @abstractmethod
    def capabilities(self) -> RuntimeCapabilities:
        """Return isolation modes and kinds this runtime can honor."""

    def is_enabled(self) -> bool:
        """Whether this runtime instance may accept starts (host default off)."""
        return True

    def health(self) -> RuntimeHealth:
        """Probe runner readiness (doctor / placement). Override for CLI checks."""
        enabled = self.is_enabled()
        return RuntimeHealth(
            name=self.name,
            available=enabled,
            enabled=enabled,
            message="enabled" if enabled else "disabled",
        )

    @abstractmethod
    def start(
        self,
        workload_id: str,
        spec: WorkloadSpec,
        *,
        owner: WorkloadOwner | None = None,
    ) -> RuntimeStartOutcome:
        """Allocate and start. May complete a run synchronously (STOPPED/FAILED)."""

    @abstractmethod
    def poll(self, workload_id: str) -> RuntimePollOutcome:
        """Refresh status for an active allocation."""

    @abstractmethod
    def stop(self, workload_id: str) -> RuntimeStopOutcome:
        """Stop best-effort. Must be safe to call when already terminal."""

    def exec(
        self,
        workload_id: str,
        command: list[str] | tuple[str, ...],
        *,
        timeout_s: float | None = None,
        env: dict[str, str] | None = None,
    ) -> WorkloadResult:
        """Run argv on a READY workspace/service. Override when supported."""
        return WorkloadResult.fail(
            f"Runtime {self.name!r} does not support exec",
            runtime=self.name,
        )
