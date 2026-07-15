"""
RuntimeSpawner (T2 / 0.48.4, seam 5) — create runtimes for the host's profile.

Extracted from ``ApplicationHost._spawn_runtimes``: collapsed/master/worker/server
runtime creation and registration. Reads host state (app, profile, worker
coordinator, event bus) through a back-reference; behaviour-preserving.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.app.host.events import HostEventType

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost
    from palm.common.runtimes.base import BaseRuntime


class RuntimeSpawner:
    """Spawns the runtimes a host profile calls for."""

    def __init__(self, host: ApplicationHost) -> None:
        self._host = host

    def spawn_runtimes(self, merged: dict[str, Any]) -> None:
        host = self._host
        profile = host.profile
        has_primary = False

        if profile.uses_collapsed_runtime:
            runtime = host._app.create_runtime(
                "embedded",
                name="main",
                autostart=True,
                set_primary=True,
                **self._command_options(merged),
            )
            self._emit_runtime_registered("main", "embedded", runtime)
            return

        if profile.master:
            runtime = host._app.create_runtime(
                "embedded",
                name="command",
                autostart=True,
                set_primary=not has_primary,
                **self._command_options(merged),
            )
            has_primary = True
            self._emit_runtime_registered("command", "embedded", runtime)

        if profile.worker and not profile.server:
            for index in range(profile.worker_count):
                name = "worker" if index == 0 else f"worker-{index}"
                runtime = host._app.create_runtime(
                    "daemon",
                    name=name,
                    autostart=True,
                    set_primary=not has_primary,
                    **self._worker_options(merged),
                )
                has_primary = True
                self._emit_runtime_registered(name, "daemon", runtime)

        if profile.server:
            options = self._worker_options(merged)
            options["http"] = False
            runtime = host._app.create_runtime(
                "server",
                name="server",
                autostart=True,
                set_primary=not has_primary,
                host=profile.server_host,
                port=profile.server_port,
                **options,
            )
            self._emit_runtime_registered("server", "server", runtime)

    def _command_options(self, merged: dict[str, Any]) -> dict[str, Any]:
        options = dict(merged)
        options.setdefault("scheduler", "inline")
        return options

    def _worker_options(self, merged: dict[str, Any]) -> dict[str, Any]:
        options = dict(merged)
        options["scheduler"] = "queued"
        return options

    def _emit_runtime_registered(self, name: str, kind: str, runtime: BaseRuntime) -> None:
        host = self._host
        if host._worker_coordinator is not None:
            host._worker_coordinator.note_runtime(name, kind)
        host._event.emit(
            HostEventType.RUNTIME_REGISTERED,
            name=name,
            kind=kind,
            scheduler=runtime.orchestration.scheduler.__class__.__name__,
        )


__all__ = ["RuntimeSpawner"]
