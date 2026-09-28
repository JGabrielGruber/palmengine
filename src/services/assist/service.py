"""Assist service façade — scenarios, sessions, catalog (Execution-shaped)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.services.base import BaseService
from services.assist._params import want_input_schema, wizard_start_body
from services.assist.catalog.service import AssistCatalogService
from services.assist.grammar import AssistCommandKind, parse_assist_command
from services.assist.scenarios.service import AssistScenarioService
from services.assist.session import AssistSession
from services.assist.sessions.service import AssistSessionService
from services.assist.views import resolve_view_format

if TYPE_CHECKING:
    from palm.system.runtime.base import BaseRuntime
    from services.definitions.service import DefinitionService
    from services.execution.service import ExecutionService
    from services.session.service import SessionService
    from services.inspect.service import InspectService


class AssistService(BaseService):
    """Meta-orchestration façade — leaf services own domain work.

    Layout (0.33+)::

        assist.scenarios  — start / describe / inspect-catalog
        assist.sessions   — session handle, verbs, handoff
        assist.catalog    — doctor / flows / waiting / discover
        assist.present    — turn shaping
        assist.profiles   — tool vs chat

    Public methods on this class remain stable and delegate to leafs.
    See ``docs/VISION-0.33.md``.
    """

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        definitions: DefinitionService,
        execution: ExecutionService,
        inspect: InspectService | None = None,
        session: SessionService | None = None,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
        admission_source: Callable[[], Any] | Any | None = None,
        analytics: Any | None = None,
        system: InspectService | None = None,
    ) -> None:
        door = inspect if inspect is not None else system
        if door is None:
            raise TypeError("AssistService requires inspect= (or system= alias)")
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._definitions = definitions
        self._execution = execution
        self._inspect = door
        self._session = session
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver
        # 0.63.22 — published admission gate (snapshot factory or
        # object with .admission). Prefer inject over resolve_runtime dig.
        self._admission_source = admission_source
        self._analytics = analytics
        self._scenarios = AssistScenarioService(self)
        self._sessions = AssistSessionService(self)
        self._catalog = AssistCatalogService(self)
        from services.assist.views import ensure_assist_view_registration

        ensure_assist_view_registration()

    # --- leaf accessors (Execution-style) ---------------------------------

    @property
    def scenarios(self) -> AssistScenarioService:
        return self._scenarios

    @property
    def sessions(self) -> AssistSessionService:
        return self._sessions

    @property
    def catalog(self) -> AssistCatalogService:
        return self._catalog

    @property
    def definitions(self) -> DefinitionService:
        return self._definitions

    @property
    def analytics(self) -> Any | None:
        """Optional AnalyticsService (0.40.4 — open:dataset / describe)."""
        return self._analytics

    def bind_analytics(self, analytics: Any | None) -> None:
        """Attach analytics after host wiring (order-independent)."""
        self._analytics = analytics

    @property
    def execution(self) -> ExecutionService:
        return self._execution

    @property
    def inspect(self) -> InspectService:
        """Product inspect door (0.61.4 / SD-007)."""
        return self._inspect

    @property
    def system(self) -> InspectService:
        """Deprecated alias for :attr:`inspect` (SD-007 migration)."""
        return self._inspect

    @property
    def product_session(self) -> SessionService | None:
        """Product session door when host-wired (0.58.12).

        Named distinctly from :meth:`session` (AssistSession handle API) so
        the product door is never shadowed.
        """
        return self._session

    # --- path dispatch ----------------------------------------------------

    def dispatch(
        self,
        path: list[str] | tuple[str, ...],
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an assist command path and return the domain result."""
        params = params or {}
        parsed = parse_assist_command(path)

        if parsed.kind == AssistCommandKind.LIST_SCENARIOS:
            return self._scenarios.list()

        if parsed.kind == AssistCommandKind.DESCRIBE_SCENARIO:
            assert parsed.scenario_id is not None
            return self._scenarios.describe(parsed.scenario_id)

        if parsed.kind == AssistCommandKind.START_SCENARIO:
            assert parsed.scenario_id is not None
            return self._scenarios.start(
                parsed.scenario_id,
                wizard_start_body(params),
                view_format=resolve_view_format(params),
                include_input_schema=want_input_schema(params),
            )

        if parsed.kind == AssistCommandKind.SCENARIO_INSPECT:
            assert parsed.scenario_id is not None
            return self._scenarios.inspect_catalog(
                parsed.scenario_id,
                view_format=resolve_view_format(params),
            )

        if parsed.kind == AssistCommandKind.SESSION:
            assert parsed.session_id is not None
            return self._sessions.inspect(
                parsed.session_id,
                view_format=resolve_view_format(params),
                include_input_schema=want_input_schema(params),
            )

        if parsed.kind == AssistCommandKind.SESSION_VERB:
            assert parsed.session_id is not None
            assert parsed.verb is not None
            return self._sessions.apply_verb(parsed.session_id, parsed.verb, params)

        if parsed.kind == AssistCommandKind.DOCTOR:
            return self._catalog.doctor()

        if parsed.kind == AssistCommandKind.TOP:
            return self._catalog.top()

        if parsed.kind == AssistCommandKind.VITALITY:
            return self._catalog.vitality()

        if parsed.kind == AssistCommandKind.CATALOG_FLOWS:
            return self._catalog.list_flows()

        if parsed.kind == AssistCommandKind.CATALOG_WAITING:
            limit = params.get("limit", 50)
            try:
                limit_i = int(limit) if limit is not None else 50
            except (TypeError, ValueError):
                limit_i = 50
            return self._catalog.list_waiting(limit=limit_i)

        if parsed.kind == AssistCommandKind.DISCOVER:
            query = params.get("query") or params.get("q") or params.get("value") or ""
            limit = params.get("limit", 12)
            try:
                limit_i = int(limit) if limit is not None else 12
            except (TypeError, ValueError):
                limit_i = 12
            return self._catalog.discover(str(query), limit=limit_i)

        if parsed.kind == AssistCommandKind.MENU:
            section = (
                params.get("section")
                or params.get("menu")
                or params.get("value")
                or "root"
            )
            # path assist/menu/{section}
            segs = [str(s) for s in path]
            if "menu" in segs:
                idx = segs.index("menu")
                if idx + 1 < len(segs) and segs[idx + 1] not in {"", "start"}:
                    section = segs[idx + 1]
            return self._catalog.menu(
                section=str(section or "root"),
                query=str(params.get("query") or params.get("q") or ""),
                cursor=params.get("cursor"),
                limit=params.get("limit"),
            )

        if parsed.kind == AssistCommandKind.OPEN:
            return self._catalog.open(params)

        raise RuntimeError(f"unhandled assist command: {parsed}")

    # --- stable public API (delegates) ------------------------------------

    def describe_scenario(self, scenario_id: str) -> dict[str, Any]:
        return self._scenarios.describe(scenario_id)

    def start_scenario(
        self,
        scenario_id: str,
        body: dict[str, Any],
        *,
        view_format: str = "assistant",
        include_input_schema: bool = False,
    ) -> dict[str, Any]:
        return self._scenarios.start(
            scenario_id,
            body,
            view_format=view_format,
            include_input_schema=include_input_schema,
        )

    def inspect_catalog(
        self,
        scenario_id: str,
        *,
        view_format: str = "assistant",
    ) -> dict[str, Any]:
        return self._scenarios.inspect_catalog(scenario_id, view_format=view_format)

    def session(self, session_id: str) -> AssistSession:
        return self._sessions.get(session_id)

    def handoff(self, session_id: str) -> dict[str, Any]:
        return self._sessions.handoff(session_id)

    def doctor(self) -> dict[str, Any]:
        """Legacy anatomy packaging (OD-001) — prefer :meth:`top` / :meth:`vitality`."""
        return self._catalog.doctor()

    def top(self) -> dict[str, Any]:
        """Living load top via inspect → vitality projection."""
        return self._catalog.top()

    def vitality(self) -> dict[str, Any]:
        """Full vitality snapshot via inspect → projection."""
        return self._catalog.vitality()

    def list_flows(self) -> list[dict[str, Any]]:
        return self._catalog.list_flows()

    def list_waiting(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return self._catalog.list_waiting(limit=limit)

    def discover(self, query: str = "", *, limit: int = 12) -> dict[str, Any]:
        return self._catalog.discover(query, limit=limit)

    def menu(
        self,
        *,
        section: str = "root",
        query: str = "",
        cursor: object | None = None,
        limit: object | None = None,
    ) -> dict[str, Any]:
        return self._catalog.menu(
            section=section, query=query, cursor=cursor, limit=limit
        )

    def open(self, params: dict[str, Any] | None = None) -> Any:
        return self._catalog.open(params)

    def invoke_tree(self, session_id: str) -> dict[str, Any]:
        return self._sessions.invoke_tree(session_id)

    def resolve_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        if self._runtime_resolver is not None:
            return self._runtime_resolver(runtime_name)
        if self._runtime is not None:
            return self._runtime
        return self._execution.flows.resolve_runtime(runtime_name)

    def admission_gate(self) -> object:
        """Published admission source for product start/continue (0.63.22).

        Prefer the injected *admission_source* (snapshot, factory, or object
        with ``.admission``). Fallback digs the execution runtime shell only
        when packaging omitted the inject — surfaces should use host or port,
        not dig the kernel.
        """
        if self._admission_source is not None:
            return self._admission_source
        return self.resolve_runtime()

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        return self.resolve_runtime().wait_until_idle(timeout=timeout)


__all__ = ["AssistService"]
