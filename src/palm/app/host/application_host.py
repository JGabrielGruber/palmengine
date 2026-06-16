"""
ApplicationHost — top-level coordinator for Palm deployment roles.
"""

from __future__ import annotations

import signal
import threading
from typing import TYPE_CHECKING, Any, Self

from palm.app.app import PalmApp
from palm.app.bootstrap import host_profile_from_settings, runtime_start_options
from palm.app.host.events import HostEventType
from palm.app.host.outbox_service import OutboxBackgroundService
from palm.app.host.roles import HostProfile
from palm.app.settings import PalmSettings
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime
    from palm.core.orchestration import Job
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition


class ApplicationHost:
    """
    Coordinates Palm deployment roles on top of :class:`~palm.app.app.PalmApp`.

    Profiles select which runtimes to spawn and whether a background outbox
    processor runs on the master role::

        host = ApplicationHost(profile=HostProfile.all_in_one())
        host.start()
        job = host.submit_flow("my_flow")
        host.shutdown()

    Presets: ``all_in_one``, ``master``, ``worker``, ``server`` — or compose
    roles via :class:`~palm.app.host.roles.HostProfile`.
    """

    def __init__(
        self,
        settings: PalmSettings | None = None,
        *,
        profile: HostProfile | None = None,
        storage: StorageEngine | None = None,
    ) -> None:
        self.settings = settings or PalmSettings()
        self.profile = profile or host_profile_from_settings(self.settings)
        self._app = PalmApp(self.settings, storage=storage)
        self._event = EventEngine()
        self._outbox_service: OutboxBackgroundService | None = None
        self._started = False
        self._signal_stop = threading.Event()

    @property
    def app(self) -> PalmApp:
        """Underlying multi-runtime application."""
        return self._app

    @property
    def event(self) -> EventEngine:
        """Host-level event bus for cross-runtime coordination."""
        return self._event

    @property
    def outbox_service(self) -> OutboxBackgroundService | None:
        return self._outbox_service

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def storage(self) -> StorageEngine:
        return self._app.storage

    @property
    def instance_manager(self):
        return self._app.instance_manager

    def runtime(self, name: str | None = None) -> BaseRuntime:
        return self._app.runtime(name)

    def start(self, **options: Any) -> Self:
        """Bootstrap plugins, spawn role runtimes, and start background services."""
        if self._started:
            return self

        self._app.bootstrap()
        self._event.initialize()
        merged = runtime_start_options(self.settings, **options)
        self._spawn_runtimes(merged)
        self._app.load_definitions()

        if self.profile.master and self.profile.enable_outbox_service:
            self._start_outbox_service()

        self._event.emit(
            HostEventType.STARTED,
            roles=sorted(self.profile.roles),
            primary=self._app.primary_name,
        )
        self._started = True
        return self

    def shutdown(self) -> None:
        """Stop background services and shut down all runtimes."""
        if not self._started:
            return

        if self._outbox_service is not None:
            self._outbox_service.stop()
            self._outbox_service = None

        self._event.emit(HostEventType.SHUTDOWN, primary=self._app.primary_name)
        self._app.shutdown()
        self._event.shutdown()
        self._started = False
        self._signal_stop.set()

    def run_until_signal(self) -> None:
        """Block until SIGINT or SIGTERM (no-op if already stopped)."""
        if not self._started:
            raise RuntimeError("ApplicationHost is not started; call start() first")

        self._signal_stop.clear()

        def _handle_signal(*_: object) -> None:
            self._signal_stop.set()

        previous_int = signal.signal(signal.SIGINT, _handle_signal)
        previous_term = signal.signal(signal.SIGTERM, _handle_signal)
        try:
            self._signal_stop.wait()
        finally:
            signal.signal(signal.SIGINT, previous_int)
            signal.signal(signal.SIGTERM, previous_term)

    def submit_flow(
        self,
        ref: FlowDefinition | str,
        *,
        runtime_name: str | None = None,
        by_id: bool = False,
        job_id: str | None = None,
        state: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        return self._app.submit_flow(
            ref,
            runtime_name=runtime_name,
            by_id=by_id,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )

    def submit_process(
        self,
        ref: ProcessDefinition | str,
        *,
        runtime_name: str | None = None,
        by_id: bool = False,
        job_id: str | None = None,
        state: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job | list[Job]:
        return self._app.submit_process(
            ref,
            runtime_name=runtime_name,
            by_id=by_id,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )

    def provide_input(
        self, job_id: str, value: Any, *, runtime_name: str | None = None
    ) -> str | None:
        return self._app.provide_input(job_id, value, runtime_name=runtime_name)

    def resume_process(self, instance_id: str, *, runtime_name: str | None = None) -> Job:
        return self._app.resume_process(instance_id, runtime_name=runtime_name)

    def running_runtimes(self) -> list[str]:
        return self._app.running()

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.shutdown()

    def _spawn_runtimes(self, merged: dict[str, Any]) -> None:
        profile = self.profile
        has_primary = False

        if profile.uses_collapsed_runtime:
            runtime = self._app.create_runtime(
                "embedded",
                name="main",
                autostart=True,
                set_primary=True,
                **self._command_options(merged),
            )
            has_primary = True
            self._emit_runtime_registered("main", "embedded", runtime)
            return

        if profile.master:
            runtime = self._app.create_runtime(
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
                runtime = self._app.create_runtime(
                    "daemon",
                    name=name,
                    autostart=True,
                    set_primary=not has_primary,
                    **self._worker_options(merged),
                )
                has_primary = True
                self._emit_runtime_registered(name, "daemon", runtime)

        if profile.server:
            runtime = self._app.create_runtime(
                "server",
                name="server",
                autostart=True,
                set_primary=not has_primary,
                host=profile.server_host,
                port=profile.server_port,
                **self._worker_options(merged),
            )
            has_primary = True
            self._emit_runtime_registered("server", "server", runtime)

    def _command_options(self, merged: dict[str, Any]) -> dict[str, Any]:
        options = dict(merged)
        options.setdefault("scheduler", "inline")
        return options

    def _worker_options(self, merged: dict[str, Any]) -> dict[str, Any]:
        options = dict(merged)
        options["scheduler"] = "queued"
        return options

    def _start_outbox_service(self) -> None:
        if not self._app.storage.is_initialized:
            return
        self._outbox_service = OutboxBackgroundService(
            self._app.storage,
            self._event,
            poll_interval=self.profile.outbox_poll_interval,
        )
        self._outbox_service.start(recover=self.profile.outbox_recover_on_startup)

    def _emit_runtime_registered(self, name: str, kind: str, runtime: BaseRuntime) -> None:
        self._event.emit(
            HostEventType.RUNTIME_REGISTERED,
            name=name,
            kind=kind,
            scheduler=runtime.orchestration.scheduler.__class__.__name__,
        )


def run_host(
    profile: HostProfile | str = "all_in_one",
    *,
    settings: PalmSettings | None = None,
    **start_options: Any,
) -> None:
    """
    Start an :class:`ApplicationHost`, block on signals, then shut down.

    Library helper for standalone master/worker/server processes.
    """
    resolved = (
        profile
        if isinstance(profile, HostProfile)
        else HostProfile.from_preset(profile)
    )
    host = ApplicationHost(settings=settings, profile=resolved)
    host.start(**start_options)
    try:
        host.run_until_signal()
    finally:
        host.shutdown()