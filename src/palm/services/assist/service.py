"""Assist service — conversational operator guidance and handoff."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.query import GetFlowQuery
from palm.common.operator.invoke_tree import build_invoke_tree
from palm.common.services.base import BaseService
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.services.assist.grammar import AssistCommandKind, parse_assist_command
from palm.services.assist.registry import list_scenario_rows, scenario_by_id
from palm.services.assist.session import AssistSession
from palm.services.assist.views import resolve_view_format
from palm.services.definitions.flows import flow_catalog_row

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime
    from palm.services.definitions.service import DefinitionService
    from palm.services.execution.service import ExecutionService
    from palm.services.system.service import SystemService


class AssistService(BaseService):
    """Meta-orchestration shell — composes definitions, execution, and system."""

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
            body = dict(params.get("body") or params)
            view_format = resolve_view_format(params)
            return self.start_scenario(parsed.scenario_id, body, view_format=view_format)

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
            ).to_dict(view_format=view_format)

        if parsed.kind == AssistCommandKind.SESSION_VERB:
            assert parsed.session_id is not None
            assert parsed.verb is not None
            view_format = resolve_view_format(params)
            handle = self.session(parsed.session_id)
            if parsed.verb == "input":
                value = params.get("value", params.get("input"))
                return handle.input(
                    value,
                    params=params,
                    view_format=view_format,
                ).to_dict(view_format=view_format)
            if parsed.verb == "backtrack":
                return handle.backtrack(params.get("to_step"), view_format=view_format).to_dict(
                    view_format=view_format
                )
            if parsed.verb == "resume":
                handle.resume()
                return handle.context(view_format=view_format, sync_gate=True).to_dict(
                    view_format=view_format
                )
            if parsed.verb == "cancel":
                return handle.cancel()
            if parsed.verb == "handoff":
                return self.handoff(parsed.session_id)

        if parsed.kind == AssistCommandKind.DOCTOR:
            return self.doctor()

        if parsed.kind == AssistCommandKind.CATALOG_FLOWS:
            return self.list_flows()

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
            view_format=view_format
        )

    def session(self, session_id: str) -> AssistSession:
        view = self._system.inspect_instance(session_id)
        flow_id = _flow_id_from_view(view)
        scenario_id = _scenario_id_from_view(view, flow_id)
        return AssistSession(
            self,
            flow_id=flow_id,
            session_id=session_id,
            scenario_id=scenario_id,
        )

    def handoff(self, session_id: str) -> dict[str, Any]:
        handle = self.session(session_id)
        ctx = handle.context()
        assist_meta = _assist_metadata(self, handle.flow_id)
        answers = _answers_from_view(ctx.detail)
        intent = answers.get("intent")
        handoff_map = assist_meta.get("handoff_map") or {}
        target = handoff_map.get(intent) if intent is not None else None
        if target is None and intent in (assist_meta.get("handoff_flows") or []):
            target = intent
        if target:
            create_params = _create_params_from_answers(assist_meta, answers)
            return {
                "handoff": {
                    "kind": "flow",
                    "flow_id": target,
                    "session_id": None,
                    "create_params": create_params,
                    "operator_hint": (
                        f"Use palm_flows_create_session or POST /v1/api/flows/{target}/create"
                    ),
                }
            }
        # 0.30.3 — typed design handoff when metadata opts in and no flow target
        design_intents = assist_meta.get("design_handoff_intents") or ()
        if intent is not None and intent in design_intents:
            return {"handoff": _design_handoff_payload(intent, answers, assist_meta)}

        default_none_hint = (
            "Assist session complete — no business flow handoff requested."
        )
        none_hints = assist_meta.get("handoff_none_hints") or {}
        operator_hint = default_none_hint
        if intent is not None and isinstance(none_hints, dict):
            mapped = none_hints.get(intent)
            if isinstance(mapped, str) and mapped.strip():
                operator_hint = mapped
        return {
            "handoff": {
                "kind": "none",
                "flow_id": None,
                "session_id": None,
                "create_params": {},
                "operator_hint": operator_hint,
            }
        }

    def doctor(self) -> dict[str, Any]:
        return self._system.doctor(self.resolve_runtime())

    def list_flows(self) -> list[dict[str, Any]]:
        return self._definitions.list_flows()

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
                {"label": "List flows", "alias": "assist/catalog/flows"},
                {"label": "List waiting sessions", "tool": "palm_system_list_waiting"},
                {
                    "label": "Propose new flow",
                    "tool": "palm_design_propose_flow",
                },
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


def _flow_id_from_view(view: dict[str, Any]) -> str | None:
    for key in ("flow_name", "flow_id"):
        value = view.get(key)
        if value is not None and str(value) not in {"", "flow"}:
            return str(value)
    progress = view.get("wizard_progress")
    if isinstance(progress, dict):
        wizard_name = progress.get("wizard_name")
        if wizard_name:
            return str(wizard_name)
    pattern = view.get("pattern")
    if isinstance(pattern, dict):
        flow = pattern.get("flow")
        if flow is not None and str(flow) not in {"", "flow"}:
            return str(flow)
    return None


def _scenario_id_from_view(view: dict[str, Any], flow_id: str | None) -> str | None:
    assist_meta = _assist_metadata_from_view(view)
    scenario_id = assist_meta.get("scenario_id")
    if scenario_id is not None:
        return str(scenario_id)
    if flow_id is not None:
        normalized = flow_id.removeprefix("flow-")
        for row in list_scenario_rows():
            registered = str(row.get("flow_id") or "")
            if registered in {flow_id, f"flow-{normalized}"} or registered.removeprefix("flow-") == normalized:
                return str(row["scenario_id"])
    return None


def _assist_metadata_from_view(view: dict[str, Any]) -> dict[str, Any]:
    pattern = view.get("pattern")
    if isinstance(pattern, dict):
        meta = pattern.get("metadata") or {}
        if isinstance(meta, dict):
            assist = meta.get("assist") or {}
            if isinstance(assist, dict):
                return assist
    return {}


def _assist_metadata(service: AssistService, flow_id: str | None) -> dict[str, Any]:
    if flow_id is None:
        return {}
    flow = service.ask(GetFlowQuery(flow_id=flow_id))
    if flow is None and not flow_id.startswith("flow-"):
        flow = service.ask(GetFlowQuery(flow_id=f"flow-{flow_id}"))
    if flow is None:
        return {}
    options = getattr(flow, "options", None) or {}
    if not isinstance(options, dict):
        return {}
    metadata = options.get("metadata") or {}
    if not isinstance(metadata, dict):
        return {}
    assist = metadata.get("assist") or {}
    return assist if isinstance(assist, dict) else {}


def _answers_from_view(view: dict[str, Any]) -> dict[str, Any]:
    answers = view.get("answers")
    if isinstance(answers, dict):
        return answers
    pattern = view.get("pattern")
    if isinstance(pattern, dict):
        nested = pattern.get("answers")
        if isinstance(nested, dict):
            return nested
    return {}


_DESIGN_ACTION_BY_INTENT: dict[str, str] = {
    "create-flow": "propose_flow",
    "improve-flow": "propose_flow",
    "propose-resource": "propose_resource",
}


def _create_params_from_answers(
    assist_meta: dict[str, Any],
    answers: dict[str, Any],
) -> dict[str, Any]:
    """Map answer keys → create_params via assist metadata (0.30.3)."""
    mapping = assist_meta.get("create_params_from_answers")
    if not isinstance(mapping, dict) or not mapping:
        return {}
    params: dict[str, Any] = {}
    for param_key, answer_key in mapping.items():
        if not isinstance(param_key, str) or not isinstance(answer_key, str):
            continue
        if answer_key in answers and answers[answer_key] is not None:
            params[param_key] = answers[answer_key]
    return params


def _design_handoff_payload(
    intent: object,
    answers: dict[str, Any],
    assist_meta: dict[str, Any],
) -> dict[str, Any]:
    """Build ``kind: design`` handoff envelope (0.30.3)."""
    intent_s = str(intent)
    none_hints = assist_meta.get("handoff_none_hints") or {}
    default_hint = (
        "Use palm_design_propose_flow / palm_design_propose_resource, then "
        "impact and commit. Treat unknown handoff kinds like none and read operator_hint."
    )
    operator_hint = default_hint
    if isinstance(none_hints, dict):
        mapped = none_hints.get(intent_s)
        if isinstance(mapped, str) and mapped.strip():
            operator_hint = mapped

    name_raw = answers.get("name_or_base")
    name = str(name_raw).strip() if name_raw is not None and str(name_raw).strip() else None

    payload: dict[str, Any] = {
        "kind": "design",
        "flow_id": None,
        "session_id": None,
        "create_params": {},
        "intent": intent_s,
        "design_action": _DESIGN_ACTION_BY_INTENT.get(intent_s, "propose_flow"),
        "operator_hint": operator_hint,
    }
    if intent_s == "improve-flow" and name:
        payload["base_flow_id"] = name
    if intent_s in {"create-flow", "propose-resource"} and name:
        payload["suggested_name"] = name
    return payload


__all__ = ["AssistService"]