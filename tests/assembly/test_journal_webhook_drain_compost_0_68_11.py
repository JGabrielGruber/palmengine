"""0.68.11 — unused webhook journal facade composted."""

from __future__ import annotations

import inspect

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.workplane.coordinator import WorkPlaneCoordinator
from palm.common.events import consumers as journal_consumers
from palm.common.events.external import HttpWebhookDeliverer, WebhookDispatcher


def test_webhook_journal_facade_is_gone() -> None:
    assert not hasattr(ApplicationHost, "drain_journal_webhooks")
    assert not hasattr(WorkPlaneCoordinator, "drain_journal_webhooks")
    assert not hasattr(journal_consumers, "consume_for_webhooks")
    assert not hasattr(journal_consumers, "JOURNAL_CONSUMER_WEBHOOKS")
    assert not hasattr(journal_consumers, "WEBHOOK_EVENT_TYPES")
    assert "webhooks" not in journal_consumers.DEFAULT_JOURNAL_CONSUMERS
    assert "consume_for_webhooks" not in inspect.getsource(journal_consumers)


def test_deliverer_stays() -> None:
    assert HttpWebhookDeliverer is not None
    assert WebhookDispatcher is not None
