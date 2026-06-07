"""
ServerRuntime — network-hosted Palm runtime with a minimal HTTP API.
"""

from __future__ import annotations

import signal
import threading
from typing import Any, ClassVar

from palm.runtimes.base import BaseRuntime
from palm.runtimes.server.http import PalmHttpServer, serve_runtime
from palm.runtimes.wiring import SchedulerPolicy


class ServerRuntime(BaseRuntime):
    """
    Long-lived runtime exposing jobs over HTTP.

    Defaults to :class:`~palm.runtimes.schedulers.queued.QueuedScheduler` so
    request handlers return promptly while a worker thread drives jobs.
    """

    runtime_name: ClassVar[str] = "ServerRuntime"
    default_scheduler_policy: ClassVar[SchedulerPolicy] = "queued"

    def __init__(
        self,
        *,
        storage: Any | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
    ) -> None:
        super().__init__(storage=storage)
        self._host = host
        self._port = port
        self._http_server: PalmHttpServer | None = None
        self._http_thread: threading.Thread | None = None

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        if self._http_server is not None:
            return int(self._http_server.server_address[1])
        return self._port

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self, **options: Any) -> None:
        super().start(**options)
        if options.get("http", True):
            self._start_http(
                host=str(options.get("host", self._host)),
                port=int(options.get("port", self._port)),
            )

    def stop(self) -> None:
        self._stop_http()
        super().stop()

    def _start_http(self, *, host: str, port: int) -> None:
        if self._http_server is not None:
            return
        self._host = host
        self._port = port
        server = serve_runtime(self, host=host, port=port)
        thread = threading.Thread(
            target=server.serve_forever,
            name="ServerRuntime-HTTP",
            daemon=True,
        )
        thread.start()
        self._http_server = server
        self._http_thread = thread

    def _stop_http(self) -> None:
        server = self._http_server
        if server is None:
            return
        server.shutdown()
        thread = self._http_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
        self._http_server = None
        self._http_thread = None


def run_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    **options: Any,
) -> None:
    """
    Start a server runtime and block until interrupted by SIGINT/SIGTERM.

    Options are forwarded to :meth:`ServerRuntime.start`.
    """
    storage = options.pop("storage", None)
    runtime = ServerRuntime(storage=storage, host=host, port=port)
    runtime.start(host=host, port=port, **options)

    stopped = threading.Event()

    def _stop(*_: object) -> None:
        stopped.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    stopped.wait()
    runtime.stop()