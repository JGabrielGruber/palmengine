"""Assist service — conversational operator guidance and handoff."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.query import GetFlowQuery
from palm.common.operator.invoke_tree import build_invoke_tree
from palm.common.services.base import BaseService
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.services.assist._params import want_input_schema, wizard_start_body
from palm.services.assist._view_meta import flow_id_from_view, scenario_id_from_view
from palm.services.assist.grammar import AssistCommandKind, parse_assist_command
from palm.services.assist.registry import list_scenario_rows, scenario_by_id
from palm.services.assist.session import AssistSession
from palm.services.assist.sessions.handoff import resolve_handoff
from palm.services.assist.views import resolve_view_format
from palm.services.definitions.flows import flow_catalog_row

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime
    from palm.services.definitions.service import DefinitionService
    from palm.services.execution.service import ExecutionService
    from palm.services.system.service import SystemService


class AssistService(BaseService):
    """Meta-orchestration shell — composes definitions, execution, and system.

    Layout (0.33+): presentation in ``assist.present``, profiles in
    ``assist.profiles`` (tool vs chat), handoff in ``assist.sessions``.
    Domain leaf services (scenarios / sessions / catalog) land in 0.33.1.
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
        system: SystemService,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._definitions = definitions
        self._execution = execution
        self._system = system
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver
        from palm.services.assist.views import ensure_assist_view_registration

        ensure_assist_view_registration()

    @property
    def definitions(self) -> DefinitionService:
        return self._definitions

    @property
    def execution(self) -> ExecutionService:
        return self._execution

    @property
    def system(self) -> SystemService:
        return self._system

    def dispatch(
        self,
        path: list[str] | tuple[str, ...],
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an assist command path and return the domain result."""
        params = params or {}
        parsed = parse_assist_command(path)

        if parsed.kind == AssistCommandKind.LIST_SCENARIOS:
            return list_scenario_rows()

        if parsed.kind == AssistCommandKind.DESCRIBE_SCENARIO:
            assert parsed.scenario_id is not None
            return self.describe_scenario(parsed.scenario_id)

        if parsed.kind == AssistCommandKind.START_SCENARIO:
            assert parsed.scenario_id is not None
            body = wizard_start_body(params)
            view_format = resolve_view_format(params)
            return self.start_scenario(
                parsed.scenario_id,
                body,
                view_format=view_format,
                include_input_schema=want_input_schema(params),
            )

        if parsed.kind == AssistCommandKind.SCENARIO_INSPECT:
            assert parsed.scenario_id is not None
            view_format = resolve_view_format(params)
            return self.inspect_catalog(parsed.scenario_id, view_format=view_format)

        if parsed.kind == AssistCommandKind.SESSION:
            assert parsed.session_id is not None
            view_format = resolve_view_format(params)
            return self.session(parsed.session_id).context(
                view_format=view_format,
                sync_gate=True,
            ).to_dict(
                view_format=view_format,
                include_input_schema=want_input_schema(params),
            )

        if parsed.kind == AssistCommandKind.SESSION_VERB:
            assert parsed.session_id is not None
            assert parsed.verb is not None
            view_format = resolve_view_format(params)
            include_input = want_input_schema(params)
            handle = self.session(parsed.session_id)
            if parsed.verb == "input":
                value = params.get("value", params.get("input"))
                return handle.input(
                    value,
                    params=params,
                    view_format=view_format,
                ).to_dict(view_format=view_format, include_input_schema=include_input)
            if parsed.verb == "backtrack":
                return handle.backtrack(params.get("to_step"), view_format=view_format).to_dict(
                    view_format=view_format,
                    include_input_schema=include_input,
                )
            if parsed.verb == "resume":
                handle.resume()
                return handle.context(view_format=view_format, sync_gate=True).to_dict(
                    view_format=view_format,
                    include_input_schema=include_input,
                )
            if parsed.verb == "cancel":
                return handle.cancel()
            if parsed.verb == "handoff":
                return self.handoff(parsed.session_id)

        if parsed.kind == AssistCommandKind.DOCTOR:
            return self.doctor()

        if parsed.kind == AssistCommandKind.CATALOG_FLOWS:
            return self.list_flows()

        if parsed.kind == AssistCommandKind.CATALOG_WAITING:
            limit = params.get("limit", 50)
            try:
                limit_i = int(limit) if limit is not None else 50
            except (TypeError, ValueError):
                limit_i = 50
            return self.list_waiting(limit=limit_i)

        if parsed.kind == AssistCommandKind.DISCOVER:
            query = params.get("query") or params.get("q") or params.get("value") or ""
            limit = params.get("limit", 12)
            try:
                limit_i = int(limit) if limit is not None else 12
            except (TypeError, ValueError):
                limit_i = 12
            return self.discover(str(query), limit=limit_i)

        raise RuntimeError(f"unhandled assist command: {parsed}")

    def describe_scenario(self, scenario_id: str) -> dict[str, Any]:
        contributor = scenario_by_id(scenario_id)
        if contributor is None:
            raise DefinitionNotFoundServiceError("scenario", scenario_id)
        row: dict[str, Any] = {
            "scenario_id": contributor.scenario_id,
            "flow_id": contributor.flow_id,
            "summary": contributor.summary,
            "contributor_id": contributor.contributor_id,
        }
        flow = self.ask(GetFlowQuery(flow_id=contributor.flow_id))
        if flow is not None:
            row["flow"] = flow_catalog_row(flow)
        return row

    def start_scenario(
        self,
        scenario_id: str,
        body: dict[str, Any],
        *,
        view_format: str = "assistant",
        include_input_schema: bool = False,
    ) -> dict[str, Any]:
        contributor = scenario_by_id(scenario_id)
        if contributor is None:
            raise DefinitionNotFoundServiceError("scenario", scenario_id)
        run_body = {**body, "flow_name": contributor.flow_id, "by_id": True}
        session = self._execution.flows.run_wizard(run_body)
        handle = AssistSession(
            self,
            flow_id=contributor.flow_id,
            session_id=session.session_id,
            scenario_id=scenario_id,
        )
        return handle.context(view_format=view_format, sync_gate=True).to_dict(
            view_format=view_format,
            include_input_schema=include_input_schema,
        )

    def session(self, session_id: str) -> AssistSession:
        view = self._system.inspect_instance(session_id)
        flow_id = flow_id_from_view(view)
        scenario_id = scenario_id_from_view(view, flow_id)
        return AssistSession(
            self,
            flow_id=flow_id,
            session_id=session_id,
            scenario_id=scenario_id,
        )

    def handoff(self, session_id: str) -> dict[str, Any]:
        return resolve_handoff(self, session_id)

    def doctor(self) -> dict[str, Any]:
        return self._system.doctor(self.resolve_runtime())

    def list_flows(self) -> list[dict[str, Any]]:
        return self._definitions.list_flows()

    def list_waiting(self, *, limit: int = 50) -> list[dict[str, Any]]:
        """Jobs/instances waiting for interactive input (assist-only friendly)."""
        from palm.core.orchestration import JobStatus

        rows = self._system.list_jobs(
            status=JobStatus.WAITING_FOR_INPUT.value,
            limit=limit,
        )
        out: list[dict[str, Any]] = []
        for row in rows or []:
            if hasattr(row, "to_dict"):
                out.append(row.to_dict())
            elif isinstance(row, dict):
                out.append(dict(row))
            else:
                out.append({"value": str(row)})
        return out

    def discover(self, query: str = "", *, limit: int = 12) -> dict[str, Any]:
        """Search aliases and high-value routes (0.31.4 progressive discovery)."""
        from palm.services.assist.registry import list_mcp_path_aliases
        from palm.services.design.registry import list_design_mcp_aliases

        q = (query or "").strip().lower()
        limit = max(1, min(int(limit), 40))
        hits: list[dict[str, Any]] = []

        # Curated starter hits when query empty
        starters = [
            {
                "alias": "operator-entry/start",
                "kind": "alias",
                "summary": "Operator menu — triage run/design/inspect",
                "call": 'palm_assist(alias="operator-entry/start")',
            },
            {
                "alias": "assist/catalog/flows",
                "kind": "alias",
                "summary": "List runnable flows",
                "call": 'palm_assist(alias="assist/catalog/flows")',
            },
            {
                "alias": "assist/doctor",
                "kind": "alias",
                "summary": "Engine health + resource preflight",
                "call": 'palm_assist(alias="assist/doctor")',
            },
            {
                "alias": "design/publish",
                "kind": "alias",
                "summary": "One-shot publish flow definition (params.body)",
                "call": 'palm_assist(alias="design/publish", params={body: {…}})',
            },
            {
                "kind": "params",
                "summary": "Start a flow session",
                "call": 'palm_assist(params={flow_id: "coconut-npc"})',
            },
            {
                "kind": "params",
                "summary": "Continue session with plain-string answer",
                "call": 'palm_assist(params={session_id, flow_id, value})',
            },
            {
                "kind": "resource",
                "summary": "Short progressive operator card",
                "call": "read palm://agent/card",
            },
        ]

        aliases = list_mcp_path_aliases() + list_design_mcp_aliases()
        for row in aliases:
            alias = str(row.get("alias") or "")
            path = row.get("path") or []
            blob = f"{alias} {' '.join(str(p) for p in path)}".lower()
            if q and q not in blob and not any(q in str(p).lower() for p in path):
                continue
            hits.append(
                {
                    "alias": alias,
                    "kind": "alias",
                    "path": path,
                    "call": f'palm_assist(alias="{alias}", params={{…}})',
                }
            )
            if len(hits) >= limit:
                break

        if not q:
            # Prefer curated starters first, then fill from aliases
            merged = list(starters)
            seen = {h.get("alias") or h.get("call") for h in merged}
            for h in hits:
                key = h.get("alias") or h.get("call")
                if key in seen:
                    continue
                merged.append(h)
                seen.add(key)
                if len(merged) >= limit:
                    break
            hits = merged[:limit]
        elif not hits:
            # Query matched nothing in aliases — return filtered starters by keyword
            hits = [
                s
                for s in starters
                if q in str(s).lower()
            ][:limit]
            if not hits:
                hits = starters[: min(4, limit)]

        return {
            "query": query,
            "hits": hits[:limit],
            "hit_count": len(hits[:limit]),
            "hint": (
                "Use call strings with palm_assist. "
                "Load palm://agent/card for the short guide."
            ),
        }

    def inspect_catalog(
        self,
        scenario_id: str,
        *,
        view_format: str = "assistant",
    ) -> dict[str, Any]:
        """Read-only operator catalog — no session mutation."""
        contributor = scenario_by_id(scenario_id)
        if contributor is None:
            raise DefinitionNotFoundServiceError("scenario", scenario_id)
        from palm.core.orchestration import JobStatus

        flows = self.list_flows()
        waiting = self._system.list_instances(
            status=JobStatus.WAITING_FOR_INPUT.value,
            include_terminal=False,
            limit=50,
        )
        waiting_rows: list[dict[str, Any]] = []
        for row in waiting:
            if hasattr(row, "to_dict"):
                waiting_rows.append(row.to_dict())
            elif isinstance(row, dict):
                waiting_rows.append(dict(row))
        payload: dict[str, Any] = {
            "scenario_id": scenario_id,
            "operator_mode": "inspect",
            "status": "catalog",
            "question": "Read-only operator catalog.",
            "hint": (
                "Use list flows / list waiting tools. Start a scenario only when the user asks."
            ),
            "flows": flows,
            "waiting": waiting_rows,
            "mutation": {
                "mutations_allowed": False,
                "requires_user_input": False,
                "agent_hint": "Read-only catalog — do not send value/input.",
            },
            "actions": [
                {
                    "label": "Publish new flow (one call)",
                    "alias": "design/publish",
                },
                {
                    "label": "Publish resource (one call)",
                    "alias": "design/publish-resource",
                },
                {
                    "label": "Start coconut NPC",
                    "tool": "palm_assist",
                    "params": {"flow_id": "coconut-npc"},
                },
                {"label": "List flows", "alias": "assist/catalog/flows"},
                {"label": "Doctor (resource preflight)", "alias": "assist/doctor"},
                {"label": "List waiting sessions", "alias": "assist/catalog/waiting"},
                {
                    "label": "Start operator entry",
                    "alias": "operator-entry/start",
                },
            ],
        }
        if resolve_view_format({"format": view_format}) != "assistant":
            payload["format"] = view_format
        return payload

    def invoke_tree(self, session_id: str) -> dict[str, Any]:
        return build_invoke_tree(self.resolve_runtime(), session_id, base_url=None)

    def resolve_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        if self._runtime_resolver is not None:
            return self._runtime_resolver(runtime_name)
        if self._runtime is not None:
            return self._runtime
        return self._execution.flows.resolve_runtime(runtime_name)

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        return self.resolve_runtime().wait_until_idle(timeout=timeout)


__all__ = ["AssistService"]
