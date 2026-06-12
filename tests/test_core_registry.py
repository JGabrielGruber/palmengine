"""Thread-safety and behavior tests for Palm registries."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from palm.app.registry import RuntimeHandle, RuntimeRegistry
from palm.common.plans.registry import PlanRegistry
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry
from palm.definitions import FlowDefinition
from palm.patterns import _registry as builder_registry
from palm.patterns.wizard.handler import CommitContext, CommitRegistry, CommitResult
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState


class _Alpha:
    pass


class _Beta:
    pass


def test_registry_register_get_names_clear() -> None:
    reg: Registry[object] = Registry("widget")
    reg.register("alpha", _Alpha)
    assert reg.get("alpha") is _Alpha
    assert reg.names() == ["alpha"]
    reg.clear()
    assert reg.names() == []


def test_registry_idempotent_same_implementation() -> None:
    reg: Registry[object] = Registry("widget")
    reg.register("alpha", _Alpha)
    reg.register("alpha", _Alpha)
    assert reg.get("alpha") is _Alpha
    assert reg.names() == ["alpha"]


def test_registry_overwrite_changes_implementation() -> None:
    reg: Registry[object] = Registry("widget")
    reg.register("alpha", _Alpha)
    reg.register("alpha", _Beta)
    assert reg.get("alpha") is _Beta


def test_registry_unknown_raises() -> None:
    reg: Registry[object] = Registry("widget")
    with pytest.raises(RegistryError, match="widget"):
        reg.get("missing")


def test_registry_concurrent_register_and_read() -> None:
    reg: Registry[object] = Registry("widget")
    errors: list[BaseException] = []
    barrier = threading.Barrier(16)

    def worker(index: int) -> None:
        try:
            name = f"item-{index % 8}"
            impl = _Alpha if index % 2 == 0 else _Beta
            barrier.wait(timeout=5)
            for _ in range(200):
                reg.register(name, impl)
                assert reg.get(name) in (_Alpha, _Beta)
                names = reg.names()
                assert isinstance(names, list)
        except BaseException as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(worker, i) for i in range(16)]
        for future in as_completed(futures):
            future.result()

    assert not errors
    assert len(reg.names()) == 8


def test_builder_registry_concurrent_access() -> None:
    saved = builder_registry.snapshot_builders()
    errors: list[BaseException] = []
    barrier = threading.Barrier(12)
    prefix = "concurrency-test"

    def build_a(*_args: object, **_kwargs: object) -> object:
        return object()

    def build_b(*_args: object, **_kwargs: object) -> object:
        return object()

    def worker(index: int) -> None:
        try:
            name = f"{prefix}-{index % 4}"
            fn = build_a if index % 2 == 0 else build_b
            barrier.wait(timeout=5)
            for _ in range(100):
                builder_registry.register_builder(name, fn)
                builder_registry.get_builder(name)
                builder_registry.registered_builders()
        except BaseException as exc:
            errors.append(exc)

    try:
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = [pool.submit(worker, i) for i in range(12)]
            for future in as_completed(futures):
                future.result()

        assert not errors
        registered = builder_registry.registered_builders()
        for index in range(4):
            assert f"{prefix}-{index}" in registered
    finally:
        builder_registry.restore_builders(saved)


def test_runtime_registry_concurrent_access() -> None:
    registry = RuntimeRegistry()
    errors: list[BaseException] = []
    barrier = threading.Barrier(8)
    runtimes = [EmbeddedRuntime() for _ in range(4)]

    for index, runtime in enumerate(runtimes):
        registry.register(RuntimeHandle(name=f"rt-{index}", kind="embedded", runtime=runtime))

    def reader(index: int) -> None:
        try:
            barrier.wait(timeout=5)
            for _ in range(100):
                name = f"rt-{index % 4}"
                handle = registry.get(name)
                assert handle.name == name
                assert name in registry
                registry.names()
                list(registry.items())
        except BaseException as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(reader, i) for i in range(8)]
        for future in as_completed(futures):
            future.result()

    assert not errors
    assert len(registry) == 4


def test_commit_registry_concurrent_register_and_run() -> None:
    registry = CommitRegistry()
    errors: list[BaseException] = []
    barrier = threading.Barrier(10)

    def handler_ok(context: CommitContext) -> CommitResult:
        return CommitResult.success(context.hook_name)

    for index in range(5):
        registry.register(f"hook-{index}", handler_ok)

    def worker(index: int) -> None:
        try:
            barrier.wait(timeout=5)
            for round_index in range(50):
                hook = f"hook-{round_index % 5}"
                registry.register(hook, handler_ok)
                assert registry.has(hook)
                registry.names()
                result = registry.run(
                    hook,
                    CommitContext(
                        wizard_name="w",
                        state=BlackboardState(),
                        answers={},
                        hook_name=hook,
                    ),
                )
                assert result.ok
        except BaseException as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(worker, i) for i in range(10)]
        for future in as_completed(futures):
            future.result()

    assert not errors
    assert registry.names() == [f"hook-{i}" for i in range(5)]


def test_plan_registry_concurrent_store_and_consume() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        plan = rt.executor.prepare_flow_plan(
            FlowDefinition(name="noop", pattern="wizard", options={"steps": 1}),
        )
    finally:
        rt.stop()

    registry = PlanRegistry()
    stored_ids: list[str] = []
    lock = threading.Lock()
    errors: list[BaseException] = []
    barrier = threading.Barrier(8)

    def storer(_index: int) -> None:
        try:
            barrier.wait(timeout=5)
            for _ in range(20):
                stored = registry.store(plan)
                with lock:
                    stored_ids.append(stored.plan_id)
        except BaseException as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(storer, i) for i in range(8)]
        for future in as_completed(futures):
            future.result()

    assert not errors
    assert len(stored_ids) == 160

    consumed = 0
    for plan_id in stored_ids:
        try:
            registry.consume(plan_id)
            consumed += 1
        except Exception:
            pass
    assert consumed == 160
