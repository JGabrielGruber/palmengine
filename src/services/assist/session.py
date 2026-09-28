"""Assist session handles — thin shell over flow sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.core.orchestration import JobStatus
from services.assist.schemas import AssistSessionContext, build_assist_session_context
from services.execution.flows.schemas import SessionContext

if TYPE_CHECKING:
    from services.assist.service import AssistService


class AssistSession:
    """Stateful handle for one assist scenario session."""

    def __init__(
        self,
        assist: AssistService,
        *,
        flow_id: str | None,
        session_id: str,
        scenario_id: str | None = None,
    ) -> None:
        self._assist = assist
        self.flow_id = flow_id
        self.session_id = session_id
        self.scenario_id = scenario_id

    def context(self, *, view_format: str = "assistant", sync_gate: bool = False) -> AssistSessionContext:
        """Assist-enriched session view shaped for ``view_format`` on ``to_dict()``."""
        flow_ctx = self._flow_session().context(sync_gate=sync_gate)
        view = dict(flow_ctx.detail if flow_ctx.detail else flow_ctx.to_dict())
        metadata = self._assist.execution.flows.get_instance_metadata(self.session_id)
        operator_mode = metadata.get("operator_mode")
        if operator_mode:
            view["operator_mode"] = operator_mode
        # 0.58.9 vocabulary: view.session_id = system subject; instance_id = continue.
        # Product handle self.session_id is still the instance id (SI-001 internal).
        view["instance_id"] = self.session_id
        system_sid = metadata.get("session_id")
        if (
            system_sid
            and str(system_sid).strip()
            and str(system_sid).strip() != self.session_id
        ):
            view["session_id"] = str(system_sid).strip()
        else:
            # Do not claim the instance is the system session.
            view.pop("session_id", None)
        compact = compact_wizard_inspect(view)
        handoff_ready = _handoff_ready(flow_ctx)
        ctx = build_assist_session_context(
            session_id=self.session_id,
            flow_id=self.flow_id or flow_ctx.flow_id,
            view=view,
            scenario_id=self.scenario_id,
            operator_hint=compact.get("operator_hint"),
            handoff_ready=handoff_ready,
        )
        ctx.invoke_tree = _safe_invoke_tree(self._assist, self.session_id)
        gate = metadata.get("mutation_gate")
        ctx.stored_mutation_gate = gate if isinstance(gate, dict) else None
        return ctx

    def input(
        self,
        value: Any,
        *,
        params: dict[str, Any] | None = None,
        view_format: str = "assistant",
    ) -> AssistSessionContext:
        """Deliver interactive input (product continue).

        **0.63.29:** requires admission via published ``admission_gate()``
        (published admission — same law as start / provide_input).
        """
        from palm.common.operator.flows_session_input import flatten_session_read_model
        from palm.common.operator.input_coercion import resolve_mcp_wizard_input
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self._assist.admission_gate())
        merged = dict(params or {})
        if "value" not in merged and "input" not in merged:
            merged["value"] = value
        inspect = flatten_session_read_model(self._flow_session().context())
        resolved = resolve_mcp_wizard_input(
            input=merged.get("input"),
            value=merged.get("value"),
            wizard_view=inspect,
        )
        self._flow_session().input(resolved, params=merged)
        return self.context(view_format=view_format, sync_gate=True)

    def backtrack(self, to_step: str | None = None, *, view_format: str = "assistant") -> AssistSessionContext:
        """Backtrack an interactive flow (product continue).

        **0.63.29:** requires admission via published ``admission_gate()``.
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self._assist.admission_gate())
        self._flow_session().backtrack(to_step)
        return self.context(view_format=view_format)

    def resume(self) -> AssistSession:
        """Re-drive a waiting interactive session (product continue).

        **0.63.29:** requires admission via published ``admission_gate()``.
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self._assist.admission_gate())
        self._flow_session().resume()
        return self

    def cancel(self) -> dict[str, Any]:
        """Cancel the backing job — control path (not a business path that needs admission).

        Stays available when admission is closed so operators can stop work
        (named residual under SD-020, same spirit as stop_workload).
        """
        return self._flow_session().cancel()

    def _flow_session(self) -> Any:
        return self._assist.execution.flows.session(self.flow_id, self.session_id)


def _safe_invoke_tree(assist: Any, session_id: str) -> dict[str, Any] | None:
    try:
        return assist.invoke_tree(session_id)
    except Exception:
        return None


def _handoff_ready(flow_ctx: SessionContext) -> bool:
    status = flow_ctx.status
    if status == JobStatus.SUCCEEDED.value:
        return True
    prompt = flow_ctx.detail.get("prompt") if flow_ctx.detail else None
    if isinstance(prompt, dict) and prompt.get("step_kind") == "summary":
        return True
    return False


__all__ = ["AssistSession"]