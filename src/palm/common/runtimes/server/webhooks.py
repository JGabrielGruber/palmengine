"""
Webhook integration — connect server lifecycle to outbox-driven dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from palm.common.events.external import WebhookDispatcher, WebhookTarget

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


@dataclass
class ServerWebhookBridge:
    """
    Optional bridge between a server context and a :class:`WebhookDispatcher`.

    When an :class:`~palm.app.host.ApplicationHost` owns the dispatcher via
    :class:`~palm.app.host.outbox_service.OutboxBackgroundService`, the server
    surface reads it from the host. Standalone servers can attach a dispatcher
    directly for outbound notifications.
    """

    dispatcher: WebhookDispatcher | None = None
    _targets: list[WebhookTarget] = field(default_factory=list)

    @property
    def targets(self) -> tuple[WebhookTarget, ...]:
        if self.dispatcher is not None:
            return self.dispatcher.targets
        return tuple(self._targets)

    def configure(
        self,
        *,
        dispatcher: WebhookDispatcher | None = None,
        targets: list[WebhookTarget] | None = None,
    ) -> None:
        if dispatcher is not None:
            self.dispatcher = dispatcher
        if targets is not None:
            self._targets = list(targets)
            if self.dispatcher is None and self._targets:
                self.dispatcher = WebhookDispatcher(self._targets)

    @classmethod
    def from_context(cls, ctx: ServerContext) -> ServerWebhookBridge:
        host = ctx.host
        if host is not None and host.webhook_dispatcher is not None:
            return cls(dispatcher=host.webhook_dispatcher)
        runtime = ctx.runtime
        processor = runtime.outbox_processor
        if processor is not None and hasattr(processor, "external_dispatcher"):
            external = processor.external_dispatcher
            if isinstance(external, WebhookDispatcher):
                return cls(dispatcher=external)
        return cls()