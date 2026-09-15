"""0.68.12 — unused projection journal facade composted."""

from __future__ import annotations

import inspect

from palm.app.host.application_host import ApplicationHost
from palm.app.host.workplane.coordinator import WorkPlaneCoordinator
from palm.common.events import consumers as journal_consumers
from palm.common.events.external import HttpWebhookDeliverer, WebhookDispatcher
from palm.core.structure import CAPABILITY_PROJECTIONS


def test_projection_journal_facade_is_gone() -> None:
    assert not hasattr(ApplicationHost, "drain_journal_projections")
    assert not hasattr(WorkPlaneCoordinator, "drain_journal_projections")
    assert not hasattr(journal_consumers, "consume_for_projections")
    assert not hasattr(journal_consumers, "JOURNAL_CONSUMER_PROJECTIONS")
    assert not hasattr(journal_consumers, "PROJECTION_EVENT_TYPES")
    assert "projections" not in journal_consumers.DEFAULT_JOURNAL_CONSUMERS
    assert "consume_for_projections" not in inspect.getsource(journal_consumers)


def test_living_projections_and_deliverer_stay() -> None:
    assert CAPABILITY_PROJECTIONS == "projections"
    assert HttpWebhookDeliverer is not None
    assert WebhookDispatcher is not None
