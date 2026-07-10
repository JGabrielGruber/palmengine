"""Provider execution service — invoke surface (distinct from flows)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.operator.resource_remediation import enrich_provider_result
from palm.common.services.base import BaseService
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.core.resource.result import ProviderResult
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


class ProviderExecutionService(BaseService):
    """One-shot provider invocation via the hosting runtime ResourceEngine."""

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
        definitions: Any | None = None,
        event_engine: Any | None = None,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver
        self._definitions = definitions
        self._event_engine = event_engine

    def resolve_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        if self._runtime_resolver is not None:
            return self._runtime_resolver(runtime_name)
        if self._runtime is None:
            raise RuntimeError("ProviderExecutionService has no bound runtime")
        return self._runtime

    def invoke(
        self,
        resource_ref: str,
        *,
        provider: str | None = None,
        action: str | None = None,
        params: dict[str, Any] | None = None,
        state: Any = None,
        resource_id: str | None = None,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Invoke a resource definition and return a provider result envelope."""
        resource_ref = str(resource_ref or "").strip()
        if not resource_ref:
            raise ValueError("resource_ref is required")

        if provider and self._definitions is not None:
            try:
                described = self._definitions.get_resource(resource_ref)
            except DefinitionNotFoundServiceError:
                pass
            else:
                described_provider = str(described.get("provider") or "")
                if described_provider and described_provider != provider:
                    raise ValueError(
                        f"resource {resource_ref!r} is owned by provider "
                        f"{described_provider!r}, not {provider!r}"
                    )

        runtime = self.resolve_runtime(runtime_name)
        engine = runtime.resource
        if not engine.is_initialized:
            engine.initialize()

        result = engine.invoke(
            resource_ref,
            provider=provider,
            action=action,
            params=params,
            state=_resolve_state(state),
            resource_id=resource_id,
        )
        body = enrich_provider_result(_provider_result_body(result))
        self._emit_resource_changed(resource_ref, action=action, body=body, result=result)
        return body

    def _emit_resource_changed(
        self,
        resource_ref: str,
        *,
        action: str | None,
        body: dict[str, Any],
        result: ProviderResult,
    ) -> None:
        if self._event_engine is None or not body.get("success"):
            return
        meta = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
        resolved = str(
            action or meta.get("action") or result.metadata.get("action") or ""
        ).lower()
        if resolved not in _MUTATING_ACTIONS:
            return
        if not getattr(self._event_engine, "is_initialized", True):
            try:
                self._event_engine.initialize()
            except Exception:
                return
        try:
            self._event_engine.emit(
                "resource.changed",
                resource_ref=resource_ref,
                action=resolved,
                resource_id=meta.get("resource_id") or result.metadata.get("resource_id"),
                provider=meta.get("provider") or result.metadata.get("provider"),
                definition_name=meta.get("definition_name")
                or result.metadata.get("definition_name"),
            )
        except Exception:
            return


_MUTATING_ACTIONS = frozenset(
    {"put", "delete", "write", "create", "update", "upsert", "remove"}
)


def _resolve_state(raw: Any) -> BlackboardState | None:
    if raw is None:
        return None
    if isinstance(raw, BlackboardState):
        return raw
    if isinstance(raw, dict):
        return BlackboardState(raw)
    return None


def _provider_result_body(result: ProviderResult) -> dict[str, Any]:
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "metadata": dict(result.metadata),
    }


__all__ = ["ProviderExecutionService"]