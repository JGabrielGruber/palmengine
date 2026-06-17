"""
ServerRuntime — network-hosted Palm runtime with extensible server surfaces.
"""

from __future__ import annotations

import signal
import threading
from typing import TYPE_CHECKING, Any, ClassVar

from palm.common.exceptions import PlanNotFoundError
from palm.common.plans import ExecutionPlan, ProcessPlan, StoredPlan
from palm.common.runtimes.base import BaseRuntime
from palm.common.runtimes.server.middleware import current_principal_id
from palm.common.runtimes.server.plans import prepare_flow_from_body, prepare_process_from_body
from palm.common.runtimes.server.transport import BaseTransport
from palm.common.runtimes.server.webhooks import ServerWebhookBridge
from palm.common.runtimes.wiring import SchedulerPolicy
from palm.core.orchestration import Job
from palm.runtimes.server.factory import create_app
from palm.runtimes.server.transport import DEFAULT_TRANSPORT, create_transport

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost
    from palm.common.runtimes.server.app import ServerApp


class ServerRuntime(BaseRuntime):
    """
    Long-lived runtime exposing Palm over registered server surfaces.

    Defaults to :class:`~palm.common.runtimes.schedulers.queued.QueuedScheduler` so
    request handlers return promptly while a worker thread drives jobs.
    """

    runtime_name: ClassVar[str] = "ServerRuntime"
    default_scheduler_policy: ClassVar[SchedulerPolicy] = "queued"

    def __init__(
        self,
        *,
        storage: Any | None = None,
        instance_manager: Any | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
        host_bridge: ApplicationHost | None = None,
    ) -> None:
        super().__init__(storage=storage, instance_manager=instance_manager)
        self._host = host
        self._port = port
        self._host_bridge = host_bridge
        self._transport: BaseTransport | None = None
        self.plan_registry = self._new_plan_registry()
        self._server_app: ServerApp | None = None
        self.webhook_bridge = ServerWebhookBridge()

    @property
    def host(self) -> str:
        if self._transport is not None:
            return self._transport.host
        return self._host

    @property
    def port(self) -> int:
        if self._transport is not None:
            return self._transport.port
        return self._port

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def server_app(self) -> ServerApp | None:
        return self._server_app

    @property
    def transport(self) -> BaseTransport | None:
        return self._transport

    def attach_host(self, host: ApplicationHost) -> None:
        """Bind an ApplicationHost for CQRS, projections, and webhook dispatch."""
        self._host_bridge = host
        if self._server_app is not None:
            self._server_app.context.attach_host(host)
            self._server_app.webhook_bridge = ServerWebhookBridge.from_context(self._server_app.context)

    def start_http(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        transport: str | BaseTransport | None = None,
    ) -> None:
        """Start the network transport after ApplicationHost CQRS wiring."""
        self._start_transport(
            host=str(host or self._host),
            port=int(port if port is not None else self._port),
            transport=transport,
        )

    def start(self, **options: Any) -> None:
        super().start(**options)
        if options.get("http", True):
            self._start_transport(
                host=str(options.get("host", self._host)),
                port=int(options.get("port", self._port)),
                transport=options.get("transport"),
            )

    def stop(self) -> None:
        self._stop_transport()
        super().stop()

    def store_plan(self, plan: ExecutionPlan) -> StoredPlan:
        """Stage a prepared plan for deferred HTTP or batch submission."""
        self._require_started()
        return self.plan_registry.store(plan, principal_id=current_principal_id(self))

    def store_process_plan(self, bundle: ProcessPlan) -> list[StoredPlan]:
        """Stage every plan in a :class:`~palm.common.plans.process_plan.ProcessPlan`."""
        return [self.store_plan(plan) for plan in bundle.plans]

    def submit_stored_plan(self, plan_id: str) -> Job:
        """Consume a staged plan and submit it to orchestration."""
        self._require_started()
        try:
            plan = self.plan_registry.consume(plan_id)
        except PlanNotFoundError as exc:
            raise exc
        return self.executor.submit_plan(plan)

    def submit_stored_plans(self, plan_ids: list[str]) -> list[Job]:
        """Consume and submit multiple staged plans in order."""
        return [self.submit_stored_plan(plan_id) for plan_id in plan_ids]

    def prepare_flow_from_body(self, body: dict[str, object]) -> ExecutionPlan:
        """Build a flow plan from an HTTP-style request body."""
        self._require_started()
        return prepare_flow_from_body(self, body)

    def prepare_process_from_body(self, body: dict[str, object]) -> ProcessPlan:
        """Build a process plan bundle from an HTTP-style request body."""
        self._require_started()
        return prepare_process_from_body(self, body)

    def _start_transport(
        self,
        *,
        host: str,
        port: int,
        transport: str | BaseTransport | None,
    ) -> None:
        if self._transport is not None:
            return
        self._host = host
        self._port = port
        self._server_app = create_app(self, host=self._host_bridge)

        if isinstance(transport, BaseTransport):
            bound = transport
        else:
            name = str(transport or DEFAULT_TRANSPORT)
            bound = create_transport(name, self._server_app, host=host, port=port)

        bound.start()
        self._transport = bound

    def _stop_transport(self) -> None:
        transport = self._transport
        if transport is None:
            return
        transport.stop()
        self._transport = None
        self._server_app = None

    @staticmethod
    def _new_plan_registry() -> Any:
        from palm.common.plans import PlanRegistry

        return PlanRegistry()


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