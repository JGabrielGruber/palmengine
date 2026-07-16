"""0.42.3 — native PalmEventsWebSocketClient against /ws/v1/events."""

from __future__ import annotations

import threading
import time

from palm.app.host.application_host import ApplicationHost
from palm.app.host.roles import DeploymentProfile
from palm.app.settings import PalmSettings
from palm.providers.palm.events_ws import (
    PalmEventsWebSocketClient,
    http_base_to_ws_url,
)


def test_http_base_to_ws_url() -> None:
    assert http_base_to_ws_url("http://127.0.0.1:8080") == "ws://127.0.0.1:8080/ws/v1/events"
    assert http_base_to_ws_url("https://b.example") == "wss://b.example/ws/v1/events"


def _host_base_url(host: ApplicationHost) -> str:
    app = host.app
    reg = app._runtimes
    handle = reg.get("server")
    rt = handle.runtime
    url = getattr(rt, "base_url", None)
    assert url, "server runtime has no base_url"
    return str(url)


def test_events_ws_subscribe_and_live() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    with ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.server_only(host="127.0.0.1", port=0),
    ) as host:
        base = _host_base_url(host)
        assert host.event is not None

        client = PalmEventsWebSocketClient(base, subject="dev")
        try:
            hello = client.connect()
            assert hello.get("channel") == "events"
            sub = client.subscribe(types=["resource.changed"], since_offset=0)
            assert sub.get("op") == "subscribed"

            def _emit() -> None:
                time.sleep(0.2)
                host.event.emit(
                    "resource.changed",
                    resource_ref="palm-todos",
                    action="put",
                )

            threading.Thread(target=_emit, daemon=True).start()
            hit = client.wait_for(
                lambda e: e.get("type") == "resource.changed"
                and (e.get("payload") or {}).get("resource_ref") == "palm-todos",
                timeout=8.0,
            )
            assert hit.get("op") == "event"
            assert hit.get("type") == "resource.changed"
        finally:
            client.close()
