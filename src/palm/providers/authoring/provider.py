"""Authoring provider — resource invoke walks palm.kits.authoring."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider
from palm.core.resource.result import (
    ProviderActionDescriptor,
    ProviderDescriptor,
    ProviderHealth,
    ProviderResult,
)
from palm.kits.authoring import bound


class AuthoringProvider(BaseProvider):
    """Commit a flow body through the bound authoring adapter."""

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        raise RuntimeError("authoring provider has no fetch; use action commit")

    def invoke(
        self,
        action: str,
        *,
        params: dict[str, Any] | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        action_s = str(action or "").strip()
        if action_s != "commit":
            return ProviderResult.fail(
                f"Unsupported action {action_s!r}",
                action=action_s,
                provider=self.name,
                resource_id=resource_id,
            )
        body = dict(params or {}).get("body")
        if not isinstance(body, dict):
            return ProviderResult.fail(
                "commit requires params.body as a mapping",
                action=action_s,
                provider=self.name,
                resource_id=resource_id,
            )
        try:
            published = bound().commit(body)
        except Exception as exc:
            return ProviderResult.fail(
                str(exc),
                action=action_s,
                provider=self.name,
                resource_id=resource_id,
            )
        return ProviderResult.ok(
            published,
            action=action_s,
            provider=self.name,
            resource_id=resource_id or published.get("name"),
        )

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            description="Catalog commit through the authoring adapter",
            actions=(
                ProviderActionDescriptor(
                    "commit",
                    "Walk land/commit with params.body as a catalog mapping",
                ),
            ),
        )

    def health(self) -> ProviderHealth:
        return ProviderHealth(healthy=True, message="authoring provider ready")


__all__ = ["AuthoringProvider"]
