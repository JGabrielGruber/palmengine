"""
Shared fixtures for integration tests outside ``tests/core/``.

Core-only fixtures live in :mod:`tests.core.conftest` and apply under ``tests/core/``.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.core.event import EventEngine
from palm.runtimes.cli.shared.bootstrap import bootstrap_runtime, shutdown_context
from palm.runtimes.cli.shared.context import CliContext


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--fast",
        action="store_true",
        default=False,
        help="Skip tests marked @pytest.mark.slow (filesystem, multi-session, CLI main)",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow: multi-session, filesystem, or full CLI bootstrap (skip with --fast)",
    )
    config.addinivalue_line(
        "markers",
        "integration: host/CQRS path needing full recovery wiring",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not config.getoption("--fast"):
        return
    skip = pytest.mark.skip(reason="skipped in --fast mode")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def _isolate_coconut_kv_state(request: pytest.FixtureRequest) -> Iterator[None]:
    """Reset in-memory KV and palm runtime binding between coconut-related tests."""
    if "coconut" not in request.node.nodeid:
        yield
        return
    from palm.common.resource.document_storage import clear_memory_kv_store
    from palm.providers.palm.bindings.runtimes.wiring import clear_palm_runtime

    clear_memory_kv_store()
    clear_palm_runtime()
    yield
    clear_memory_kv_store()
    clear_palm_runtime()


@pytest.fixture
def event_engine() -> Iterator[EventEngine]:
    """Initialized event bus for integration tests."""
    engine = EventEngine()
    engine.initialize()
    yield engine
    engine.shutdown()


@pytest.fixture
def fast_settings() -> PalmSettings:
    """Default fast host settings — memory storage, lean recovery."""
    return PalmSettings.for_tests(load_examples=False)


@pytest.fixture
def fast_cli_settings() -> PalmSettings:
    """Fast settings with example definitions for CLI dispatch tests."""
    return PalmSettings.for_tests(load_examples=True)


@pytest.fixture
def full_recovery_settings() -> PalmSettings:
    """Settings that exercise compensation, outbox, and projection rebuild."""
    return PalmSettings.for_tests(load_examples=False, full_recovery=True)


@pytest.fixture
def settings(fast_settings: PalmSettings) -> PalmSettings:
    """Alias used across host/CQRS tests."""
    return fast_settings


@pytest.fixture
def cli_ctx(fast_cli_settings: PalmSettings) -> Iterator[CliContext]:
    """Started CLI context with fast host settings and example definitions."""
    ctx = bootstrap_runtime(settings=fast_cli_settings, show_banner=False)
    yield ctx
    shutdown_context(ctx)


class _EchoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        payload = {"path": self.path, "ok": True}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


@pytest.fixture
def http_echo_server() -> Iterator[str]:
    """Local HTTP server that echoes GET path as JSON — for REST provider tests."""
    server = HTTPServer(("127.0.0.1", 0), _EchoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()


@pytest.fixture
def rest_base_url(http_echo_server: str) -> str:
    return http_echo_server


@pytest.fixture
def host(fast_settings: PalmSettings) -> Iterator[ApplicationHost]:
    """Started collapsed ApplicationHost for integration tests."""
    application_host = ApplicationHost(
        settings=fast_settings,
        profile=HostProfile.all_in_one(),
    )
    application_host.start()
    yield application_host
    application_host.shutdown()
