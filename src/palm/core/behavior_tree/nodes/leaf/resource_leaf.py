"""
ResourceLeaf — invoke a registered resource via :class:`~palm.core.resource.ResourceEngine`.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.leaf import LeafNode
from palm.core.context import BaseState
from palm.core.resource.engine import ResourceEngine
from palm.core.resource.observability import resource_correlation
from palm.core.resource.result import ProviderResult


class ResourceLeaf(LeafNode):
    """
    Resolve and invoke a resource definition (or direct provider) on tick.

    Writes provider data to ``output_key`` (defaults to the leaf ``name``) and
    stores an audit trace at ``trace_key``. On failure, optional ``error_key``
    receives a human-readable message and the leaf returns ``PatternStatus.FAILURE``.
    """

    TRACE_KEY_PREFIX = "__bt_resource__"

    def __init__(
        self,
        name: str,
        *,
        resource_engine: ResourceEngine | None = None,
        resource_ref: str | None = None,
        provider: str | None = None,
        action: str | None = None,
        resource_id: str | None = None,
        params: dict[str, Any] | None = None,
        output_key: str | None = None,
        error_key: str | None = None,
        trace_key: str | None = None,
        step_slug: str | None = None,
        wizard_name: str | None = None,
    ) -> None:
        super().__init__(name)
        if not resource_ref and not provider:
            raise ValueError(
                f"ResourceLeaf {name!r} requires resource_ref or provider",
            )
        self._resource_engine = resource_engine
        self._resource_ref = resource_ref
        self._provider = provider
        self._action = action
        self._resource_id = resource_id
        self._params = dict(params or {})
        self._output_key = output_key or name
        self._error_key = error_key
        self._trace_key = trace_key if trace_key is not None else self.default_trace_key(name)
        self._step_slug = step_slug
        self._wizard_name = wizard_name

    @staticmethod
    def default_trace_key(name: str) -> str:
        """Return the default audit key for a resource leaf."""
        return f"{ResourceLeaf.TRACE_KEY_PREFIX}:{name}"

    @property
    def output_key(self) -> str:
        return self._output_key

    @property
    def trace_key(self) -> str:
        return self._trace_key

    def _resolved_action(self) -> str | None:
        """Return an explicit action override, or ``None`` to use the definition default."""
        return self._action

    def _resolved_target(self) -> str:
        return self._resource_ref or self._provider or self.name

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        if self._resource_engine is None:
            return self._fail(state, "ResourceEngine is not configured")
        if not self._resource_engine.is_initialized:
            self._resource_engine.initialize()

        action = self._resolved_action()
        result = self._resource_engine.invoke(
            self._resource_ref,
            provider=self._provider,
            action=action,
            resource_id=self._resource_id,
            params=self._params,
            state=state,
            correlation=resource_correlation(
                state,
                wizard=self._wizard_name,
                step_slug=self._step_slug or self.name,
            ),
        )

        resolved_action = action or result.metadata.get("action") or "fetch"
        trace: dict[str, Any] = {
            "success": result.success,
            "resource_ref": self._resource_ref,
            "provider": self._provider or result.metadata.get("provider"),
            "action": resolved_action,
            "definition_id": result.metadata.get("definition_id"),
            "definition_name": result.metadata.get("definition_name"),
            "resource_id": result.metadata.get("resource_id"),
            "output_key": self._output_key,
            "error": result.error,
            "invoke_depth": result.metadata.get("invoke_depth"),
            "invoke_chain": _invoke_chain(result),
            "parent_job_id": result.metadata.get("parent_job_id"),
            "mode": result.metadata.get("mode"),
            "wait_mode": result.metadata.get("wait_mode"),
            "waiting_for_child_wizard": result.metadata.get("waiting_for_child_wizard"),
            "child_job_id": result.metadata.get("child_job_id"),
            "child_instance_id": result.metadata.get("child_instance_id"),
        }
        if isinstance(result.data, dict):
            for key in (
                "waiting_for_child_wizard",
                "child_job_id",
                "child_instance_id",
                "child_job_href",
                "child_instance_href",
            ):
                if key in result.data:
                    trace[key] = result.data[key]
        state.set(self._trace_key, trace)

        if not result.success:
            return self._fail(state, result.error or "Resource invocation failed")

        state.set(self._output_key, result.data)
        if self._error_key:
            state.delete(self._error_key)
        if _should_wait_for_child(result):
            return PatternStatus.WAITING_FOR_CHILD
        return PatternStatus.SUCCESS

    def _fail(self, state: BaseState, message: str) -> PatternStatus:
        action_label = self._action or "invoke"
        detail = (
            f"Resource {self._resolved_target()!r} " f"(action={action_label}) failed: {message}"
        )
        if self._error_key:
            state.set(self._error_key, detail)
        return PatternStatus.FAILURE


def _should_wait_for_child(result: ProviderResult) -> bool:
    if result.metadata.get("waiting_for_child_wizard"):
        return True
    data = result.data
    return isinstance(data, dict) and bool(data.get("waiting_for_child_wizard"))


def _invoke_chain(result: Any) -> list[str] | None:
    if isinstance(result.data, dict):
        chain = result.data.get("invoke_chain")
        if isinstance(chain, list):
            return chain
    return None
