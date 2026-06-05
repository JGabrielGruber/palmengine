"""
Tests for the shared Event + EventBus at palm.core.events (used by orchestration).
"""

from __future__ import annotations

from palm.core.events import Event, EventBus


def test_eventbus_basic_publish_and_subscribe() -> None:
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe("test.event", received.append)

    bus.publish_named("test.event", {"a": 1})

    assert len(received) == 1
    assert received[0].name == "test.event"
    assert received[0].payload["a"] == 1


def test_eventbus_handler_error_is_isolated() -> None:
    bus = EventBus()
    received: list[Event] = []

    def bad_handler(_: Event) -> None:
        raise RuntimeError("boom")

    def good_handler(e: Event) -> None:
        received.append(e)

    bus.subscribe("evt", bad_handler)
    bus.subscribe("evt", good_handler)

    bus.publish_named("evt", {})

    assert len(received) == 1  # good handler still ran


def test_eventbus_unsubscribe() -> None:
    bus = EventBus()
    calls = []
    h = lambda e: calls.append(1)  # noqa: E731
    bus.subscribe("x", h)
    bus.publish_named("x", {})
    bus.unsubscribe("x", h)
    bus.publish_named("x", {})
    assert len(calls) == 1
