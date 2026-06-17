"""
Host role profiles — composable deployment roles for ApplicationHost.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self

HostRoleName = Literal["master", "worker", "server"]
HostProfilePreset = Literal["all_in_one", "master", "worker", "server"]


@dataclass(frozen=True)
class HostProfile:
    """
    Declares which capabilities an :class:`~palm.app.host.ApplicationHost` provides.

    Roles compose freely — e.g. master + worker in one process, or worker-only
    nodes sharing durable storage with a remote master.
    """

    master: bool = True
    worker: bool = True
    server: bool = False
    worker_count: int = 1
    server_host: str = "127.0.0.1"
    server_port: int = 8080
    enable_outbox_service: bool = True
    outbox_poll_interval: float = 0.5
    outbox_recover_on_startup: bool = True

    def __post_init__(self) -> None:
        if self.worker_count < 1:
            raise ValueError("worker_count must be >= 1")
        if not self.master and not self.worker and not self.server:
            raise ValueError("At least one host role must be enabled")

    @property
    def roles(self) -> frozenset[HostRoleName]:
        enabled: set[HostRoleName] = set()
        if self.master:
            enabled.add("master")
        if self.worker:
            enabled.add("worker")
        if self.server:
            enabled.add("server")
        return frozenset(enabled)

    @property
    def uses_collapsed_runtime(self) -> bool:
        """Single embedded runtime when master+worker without HTTP."""
        return self.master and self.worker and not self.server and self.worker_count == 1

    @classmethod
    def all_in_one(cls) -> Self:
        return cls(master=True, worker=True, server=False)

    @classmethod
    def master_only(cls) -> Self:
        return cls(master=True, worker=False, server=False)

    @classmethod
    def worker_only(cls, *, count: int = 1) -> Self:
        return cls(master=False, worker=True, worker_count=count)

    @classmethod
    def server_only(
        cls,
        *,
        host: str = "127.0.0.1",
        port: int = 8080,
    ) -> Self:
        return cls(master=False, worker=True, server=True, server_host=host, server_port=port)

    @classmethod
    def from_preset(cls, preset: HostProfilePreset | str) -> Self:
        mapping: dict[str, Self] = {
            "all_in_one": cls.all_in_one(),
            "master": cls.master_only(),
            "worker": cls.worker_only(),
            "server": cls.server_only(),
        }
        key = str(preset).lower()
        if key not in mapping:
            raise ValueError(
                f"Unknown host profile preset {preset!r}; " f"expected one of {sorted(mapping)}"
            )
        return mapping[key]

    @classmethod
    def from_roles(
        cls,
        roles: list[str] | set[str],
        *,
        worker_count: int = 1,
        server_host: str = "127.0.0.1",
        server_port: int = 8080,
        enable_outbox_service: bool = True,
        outbox_poll_interval: float = 0.5,
        outbox_recover_on_startup: bool = True,
    ) -> Self:
        normalized = {str(role).lower() for role in roles}
        return cls(
            master="master" in normalized,
            worker="worker" in normalized,
            server="server" in normalized,
            worker_count=worker_count,
            server_host=server_host,
            server_port=server_port,
            enable_outbox_service=enable_outbox_service,
            outbox_poll_interval=outbox_poll_interval,
            outbox_recover_on_startup=outbox_recover_on_startup,
        )
