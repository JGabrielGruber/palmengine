"""Tests for production-grade EventEngine."""

from __future__ import annotations

import asyncio

import pytest

from palm.core.event import Event, EventContext, EventEngine, HandlerError


def test_emit_delivers_to_typed_and_wildcard_handlers() -> None:
    received: list[str] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("job.submitted", lambda e: received.append(f"typed:{e.type}"))
    engine.subscribe("*", lambda e: received.append(f"wild:{e.type}"))

    engine.emit("job.submitted", job_id="j-1")

    assert received == ["typed:job.submitted", "wild:job.submitted"]
    engine.shutdown()


def test_subscribe_returns_unsubscribe_handle() -> None:
    received: list[str] = []
    engine = EventEngine()
    engine.initialize()
    sub = engine.subscribe("*", lambda e: received.append(e.type))
    engine.emit("a")
    sub.unsubscribe()
    engine.emit("b")
    assert received == ["a"]
    engine.shutdown()


def test_context_propagation_and_enriched_payload() -> None:
    captured: list[dict] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda e: captured.append(e.enriched_payload()))

    ctx = EventContext(job_id="job-1", instance_id="inst-1", trace_id="trace-9")
    engine.emit("job.status_changed", context=ctx, status="RUNNING")

    assert captured[0]["job_id"] == "job-1"
    assert captured[0]["instance_id"] == "inst-1"
    assert captured[0]["trace_id"] == "trace-9"
    assert captured[0]["status"] == "RUNNING"
    engine.shutdown()


def test_bind_context_merges_implicit_context() -> None:
    outer = EventContext(job_id="job-1")
    inner = EventContext(instance_id="inst-1")
    captured: list[EventContext | None] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda e: captured.append(e.context))

    with engine.bind_context(outer):
        engine.emit("a", context=inner)

    assert captured[0] is not None
    assert captured[0].job_id == "job-1"
    assert captured[0].instance_id == "inst-1"
    engine.shutdown()


def test_handler_errors_are_isolated_by_default() -> None:
    received: list[str] = []
    engine = EventEngine()
    engine.initialize()

    def boom(_event: Event) -> None:
        raise RuntimeError("handler failed")

    engine.subscribe("*", boom)
    engine.subscribe("*", lambda e: received.append(e.type))

    result = engine.emit("test.event")

    assert received == ["test.event"]
    assert result.handler_errors is not None
    assert len(result.handler_errors) == 1
    assert isinstance(result.handler_errors[0], HandlerError)
    engine.shutdown()


def test_interceptor_skipped_for_outbox_replay() -> None:
    intercepted: list[str] = []
    engine = EventEngine()
    engine.initialize()
    engine.add_interceptor(lambda e: intercepted.append(e.type))

    event = Event(type="job.completed", payload={"job_id": "j-1"})
    engine.publish(event)
    engine.publish(event, source="outbox")

    assert intercepted == ["job.completed"]
    engine.shutdown()


def test_async_handlers_can_be_drained() -> None:
    received: list[str] = []
    engine = EventEngine()
    engine.initialize()

    async def async_handler(event: Event) -> None:
        received.append(event.type)

    engine.subscribe("*", async_handler)
    engine.emit("async.event")
    count = asyncio.run(engine.drain_async_handlers())

    assert count == 1
    assert received == ["async.event"]
    engine.shutdown()


@pytest.mark.asyncio
async def test_async_handler_auto_drains_on_running_loop() -> None:
    received: list[str] = []
    engine = EventEngine()
    engine.initialize()

    async def async_handler(event: Event) -> None:
        received.append(event.type)

    engine.subscribe("*", async_handler)
    engine.emit("loop.event")
    await asyncio.sleep(0)
    assert received == ["loop.event"]
    engine.shutdown()