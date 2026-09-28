"""Assist sessions subdomain — open handle, verbs, handoff, invoke tree."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.operator.invoke_tree import build_invoke_tree
from services.assist._params import want_input_schema
from services.assist._view_meta import flow_id_from_view, scenario_id_from_view
from services.assist.session import AssistSession
from services.assist.sessions.handoff import resolve_handoff
from services.assist.views import resolve_view_format

if TYPE_CHECKING:
    from services.assist.service import AssistService


class AssistSessionService:
    """Drive an assist/flow instance (inspect, input, back, resume, cancel, handoff)."""

    def __init__(self, assist: AssistService) -> None:
        self._assist = assist

    def get(self, session_id: str) -> AssistSession:
        # 0.58.9: session_id may be system subject — resolve primary instance.
        instance_id = self._resolve_instance_id(session_id)
        view = self._assist.inspect.inspect_instance(instance_id)
        flow_id = flow_id_from_view(view)
        scenario_id = scenario_id_from_view(view, flow_id)
        return AssistSession(
            self._assist,
            flow_id=flow_id,
            session_id=instance_id,
            scenario_id=scenario_id,
        )

    def _product_session(self) -> Any | None:
        """Product SessionService — use private slot (``.session`` is the handle API)."""
        return getattr(self._assist, "_session", None)

    def _resolve_instance_id(self, session_or_instance: str) -> str:
        """Map system session id → continue instance; pass instance ids through."""
        product = self._product_session()
        if product is not None:
            return product.resolve_instance_id(session_or_instance)
        text = str(session_or_instance or "").strip()
        if not text.startswith("sess-"):
            return text
        try:
            runtime = self._assist.execution.flows.resolve_runtime()
            plane = getattr(runtime, "session_plane", None)
            if plane is None:
                return text
            inst = plane.resolve_continue_instance(text)
            return str(inst) if inst else text
        except Exception:
            return text

    def _gate_bound_session_owns(
        self, instance_id: str, params: dict[str, Any] | None
    ) -> None:
        """Continue attribution: SI-015 owner + 0.58.15 strict (product door)."""
        product = self._product_session()
        if product is not None:
            product.gate_bound_session_owns(instance_id, params)
            return
        params = params if params is not None else {}
        from palm.system.subsystems.planes.session import looks_like_system_session_id

        runtime = self._assist.execution.flows.resolve_runtime()
        plane = getattr(runtime, "session_plane", None)
        if plane is None:
            return
        raw = params.get("session_id")
        sid = str(raw).strip() if looks_like_system_session_id(raw) else None
        if hasattr(plane, "require_continue_attribution"):
            bound = plane.require_continue_attribution(
                str(instance_id).strip(), sid, strict=True
            )
            if bound and not looks_like_system_session_id(params.get("session_id")):
                params["session_id"] = bound
            return
        if sid is not None:
            plane.require_owned_instance(sid, str(instance_id).strip())

    def inspect(
        self,
        session_id: str,
        *,
        view_format: str = "assistant",
        include_input_schema: bool = False,
    ) -> dict[str, Any]:
        return (
            self.get(session_id)
            .context(view_format=view_format, sync_gate=True)
            .to_dict(
                view_format=view_format,
                include_input_schema=include_input_schema,
            )
        )

    def apply_verb(
        self,
        session_id: str,
        verb: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Apply a session verb and return a shaped dict (or cancel/handoff payload)."""
        params = params or {}
        view_format = resolve_view_format(params)
        include_input = want_input_schema(params)
        instance_id = self._resolve_instance_id(session_id)
        self._gate_bound_session_owns(instance_id, params)
        handle = self.get(session_id)
        if verb == "input":
            value = params.get("value", params.get("input"))
            return handle.input(
                value,
                params=params,
                view_format=view_format,
            ).to_dict(view_format=view_format, include_input_schema=include_input)
        if verb == "backtrack":
            return handle.backtrack(params.get("to_step"), view_format=view_format).to_dict(
                view_format=view_format,
                include_input_schema=include_input,
            )
        if verb == "resume":
            handle.resume()
            return handle.context(view_format=view_format, sync_gate=True).to_dict(
                view_format=view_format,
                include_input_schema=include_input,
            )
        if verb == "cancel":
            return handle.cancel()
        if verb == "handoff":
            return self.handoff(session_id)
        raise RuntimeError(f"unknown assist session verb: {verb}")

    def handoff(self, session_id: str) -> dict[str, Any]:
        return resolve_handoff(self._assist, session_id)

    def invoke_tree(self, session_id: str) -> dict[str, Any]:
        return build_invoke_tree(
            self._assist.resolve_runtime(),
            session_id,
            base_url=None,
        )


__all__ = ["AssistSessionService"]
