"""
Webhook health snapshot from the host dispatcher.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from palm.common.events.external import WebhookDispatcher, WebhookTarget


@runtime_checkable
class WebhookContext(Protocol):
    """What a composition root exposes so the kit can read webhook health.

    The kit asks for a dispatcher. The host or runtime decides where it comes
    from (host install, outbox processor, or none).
    """

    @property
    def webhook_dispatcher(self) -> WebhookDispatcher | None:
        """Dispatcher this context publishes through, when one is installed."""


@dataclass(frozen=True)
class ServerWebhookBridge:
    """
    Health snapshot of a :class:`WebhookDispatcher` for server surfaces.

    Built from a :class:`WebhookContext`. The composition root supplies the
    dispatcher; this bridge only exposes target counts. Production outbox drain
    does not POST.
    """

    dispatcher: WebhookDispatcher | None = None

    @property
    def targets(self) -> tuple[WebhookTarget, ...]:
        if self.dispatcher is None:
            return ()
        return self.dispatcher.targets

    @classmethod
    def from_context(cls, ctx: WebhookContext) -> ServerWebhookBridge:
        return cls(dispatcher=ctx.webhook_dispatcher)
