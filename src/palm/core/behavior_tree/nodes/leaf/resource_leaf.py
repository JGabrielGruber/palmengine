"""
ResourceLeaf — invoke a registered resource via :class:`~palm.core.resource.ResourceEngine`.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.leaf import LeafNode
from palm.core.context import BaseState
from palm.core.resource.engine import ResourceEngine


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

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        if self._resource_engine is None:
            return self._fail(state, "ResourceEngine is not configured")
        if not self._resource_engine.is_initialized:
            self._resource_engine.initialize()

        result = self._resource_engine.invoke(
            self._resource_ref,
            provider=self._provider,
            action=self._action,
            resource_id=self._resource_id,
            params=self._params,
            state=state,
        )

        trace: dict[str, Any] = {
            "success": result.success,
            "resource_ref": self._resource_ref,
            "provider": result.metadata.get("provider"),
            "action": result.metadata.get("action"),
            "definition_id": result.metadata.get("definition_id"),
            "definition_name": result.metadata.get("definition_name"),
            "resource_id": result.metadata.get("resource_id"),
            "output_key": self._output_key,
            "error": result.error,
        }
        state.set(self._trace_key, trace)

        if not result.success:
            return self._fail(state, result.error or "Resource invocation failed")

        state.set(self._output_key, result.data)
        if self._error_key:
            state.delete(self._error_key)
        return PatternStatus.SUCCESS

    def _fail(self, state: BaseState, message: str) -> PatternStatus:
        detail = f"Resource {self.name!r} failed: {message}"
        if self._error_key:
            state.set(self._error_key, detail)
        return PatternStatus.FAILURE