"""0.68.10 — unused host webhook event names composted."""

from __future__ import annotations

import inspect

from bundles.standard.app.host.events import HostEventType
from bundles.standard.runtimes.cli.commands.dashboard import _event_type_styled


def test_host_event_type_has_no_webhook_names() -> None:
    assert not hasattr(HostEventType, "WEBHOOK_DELIVERED")
    assert not hasattr(HostEventType, "WEBHOOK_FAILED")
    assert HostEventType.STARTED == "host.started"
    assert HostEventType.SHUTDOWN == "host.shutdown"


def test_dashboard_does_not_style_host_webhook_events() -> None:
    src = inspect.getsource(_event_type_styled)
    assert "host.webhook" not in src
    assert "host.shutdown" in src
