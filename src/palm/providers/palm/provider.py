"""Palm resource provider — compositional orchestration (Palm calling Palm)."""

from __future__ import annotations

import uuid
from typing import Any

from palm.core.resource import BaseProvider
from palm.core.resource.result import ProviderActionDescriptor, ProviderDescriptor, ProviderHealth, ProviderResult
from palm.providers.palm.coordinator import PalmInvokeCoordinator
from palm.providers.palm.exceptions import PalmProviderError, PalmTimeoutError
from palm.providers.palm.params import PalmInvokeParams
from palm.providers.palm.recursion import PalmRecursionError
from palm.providers.palm.target import parse_target
from palm.providers.palm.wiring import get_bound_runtime


class PalmProvider(BaseProvider):
    """Invoke Palm flows, processes, and resources locally or via Server HTTP."""

    def __init__(
        self,
        *,
        name: str,
        coordinator: PalmInvokeCoordinator | None = None,
    ) -> None:
        super().__init__(name=name)
        self._coordinator = coordinator or PalmInvokeCoordinator()

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        """Fetch a job snapshot by id (``fetch`` action alias)."""
        result = self.invoke("fetch", resource_id=resource_id, params=dict(params))
        if not result.success:
            raise RuntimeError(result.error or "fetch failed")
        return result.data

    def invoke(
        self,
        action: str,
        *,
        params: dict[str, Any] | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        invoke_params = PalmInvokeParams.from_mapping(
            params,
            resource_id=resource_id,
            **kwargs,
        )

        if action == "fetch":
            return self._fetch(action, invoke_params, resource_id=resource_id)

        try:
            target = parse_target(
                action=action,
                resource_id=resource_id,
                params=invoke_params.as_target_dict(),
            )
        except ValueError as exc:
            return self._fail(action, str(exc), resource_id=resource_id)

        try:
            payload = self._coordinator.invoke(action, target, invoke_params)
        except PalmRecursionError as exc:
            return self._fail(action, str(exc), resource_id=resource_id)
        except PalmTimeoutError as exc:
            return self._fail(action, str(exc), resource_id=resource_id)
        except PalmProviderError as exc:
            return self._fail(action, str(exc), resource_id=resource_id)

        return ProviderResult.ok(
            payload,
            action=action,
            provider=self.name,
            resource_id=resource_id or target.ref,
            mode="remote" if invoke_params.is_remote else "local",
            invoke_depth=payload.get("invoke_depth"),
            parent_job_id=invoke_params.parent_job_id,
        )

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            description="Compositional Palm orchestration — invoke flows, processes, and resources",
            actions=(
                ProviderActionDescriptor(
                    "submit_flow",
                    "Submit a child flow by name or flow:<ref>",
                ),
                ProviderActionDescriptor(
                    "submit_process",
                    "Submit a child process by name or process:<ref>",
                ),
                ProviderActionDescriptor(
                    "invoke_resource",
                    "Invoke a registered resource definition on the bound runtime",
                ),
                ProviderActionDescriptor(
                    "fetch",
                    "Fetch job status and result by job id",
                ),
            ),
        )

    def health(self) -> ProviderHealth:
        runtime = get_bound_runtime()
        if runtime is not None and runtime.is_started:
            return ProviderHealth(healthy=True, message="local runtime bound")
        return ProviderHealth(
            healthy=False,
            message="no local runtime bound; use remote_url for remote mode",
        )

    def _fetch(
        self,
        action: str,
        params: PalmInvokeParams,
        *,
        resource_id: str | None,
    ) -> ProviderResult:
        job_id = params.resolve_job_id(resource_id=resource_id)
        if not job_id:
            return self._fail(action, "fetch requires job_id or resource_id", resource_id=resource_id)
        try:
            payload = self._coordinator.fetch(params, resource_id=resource_id)
        except PalmProviderError as exc:
            return self._fail(action, str(exc), resource_id=job_id)
        return ProviderResult.ok(
            payload,
            action=action,
            provider=self.name,
            resource_id=job_id,
            mode="remote" if params.is_remote else "local",
        )

    def _fail(
        self,
        action: str,
        message: str,
        *,
        resource_id: str | None,
    ) -> ProviderResult:
        return ProviderResult.fail(
            message,
            action=action,
            provider=self.name,
            resource_id=resource_id,
        )


def new_child_job_id(prefix: str = "palm-child") -> str:
    """Generate a correlation-friendly child job id."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"