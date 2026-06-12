"""
ServerRuntime — network-hosted Palm runtime with a minimal HTTP API.
"""

from __future__ import annotations

import signal
import threading
from typing import Any, ClassVar

from palm.common.exceptions import PlanNotFoundError
from palm.common.plans import ExecutionPlan, PlanRegistry, ProcessPlan, StoredPlan
from palm.core.orchestration import Job
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.runtimes.base import BaseRuntime
from palm.runtimes.server.auth import current_principal_id
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
        instance_manager: Any | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
    ) -> None:
        super().__init__(storage=storage, instance_manager=instance_manager)
        self._host = host
        self._port = port
        self._http_server: PalmHttpServer | None = None
        self._http_thread: threading.Thread | None = None
        self.plan_registry = PlanRegistry()

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
        if "flow" in body and isinstance(body["flow"], dict):
            flow = FlowDefinition.from_dict(body["flow"])
            return self.executor.prepare_flow_plan(flow, job_id=_optional_str(body.get("job_id")))

        if "wizard" in body:
            wizard = body["wizard"]
            if not isinstance(wizard, dict):
                raise TypeError("wizard must be an object")
            steps = wizard.get("steps")
            flow = FlowDefinition(
                name=str(wizard.get("name", "wizard")),
                pattern="wizard",
                options={"steps": int(steps)} if steps is not None else {},
            )
            return self.executor.prepare_flow_plan(flow, job_id=_optional_str(body.get("job_id")))

        if "flow_name" in body:
            return self.executor.prepare_flow_plan(
                str(body["flow_name"]),
                by_id=bool(body.get("by_id", False)),
                job_id=_optional_str(body.get("job_id")),
            )

        raise ValueError("expected 'flow', 'wizard', or 'flow_name' in request body")

    def prepare_process_from_body(self, body: dict[str, object]) -> ProcessPlan:
        """Build a process plan bundle from an HTTP-style request body."""
        if "process" in body and isinstance(body["process"], dict):
            process = ProcessDefinition.from_dict(body["process"])
            return self.executor.prepare_process_plan(
                process,
                job_id=_optional_str(body.get("job_id")),
            )

        if "process_name" in body:
            return self.executor.prepare_process_plan(
                str(body["process_name"]),
                by_id=bool(body.get("by_id", False)),
                job_id=_optional_str(body.get("job_id")),
            )

        raise ValueError("expected 'process' or 'process_name' in request body")

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


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None
