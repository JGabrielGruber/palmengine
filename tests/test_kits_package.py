"""Smoke tests for plugins.kits install truth."""

from __future__ import annotations


def test_installed_kits_include_server() -> None:
    import plugins.kits as kits
    from plugins.kits import INSTALLED_KITS, get_kit, list_kits

    assert "server" in INSTALLED_KITS
    assert not hasattr(kits, "CORE_KITS")
    # Surface kit registers on import (not core bootstrap autoload).
    import plugins.kits.server  # noqa: F401

    info = get_kit("server")
    assert info is not None
    assert info.module == "plugins.kits.server"
    names = {k.name for k in list_kits()}
    assert "server" in names


def test_server_kit_protocol_exports() -> None:
    from plugins.kits.server import ServerRequest, ServerResponse, TransportApp, transport_registry

    assert ServerRequest is not None
    assert ServerResponse is not None
    assert TransportApp is not None
    assert transport_registry is not None


def test_transport_registry_binds_kit_contract() -> None:
    from plugins.kits.server.protocol import ServerRequest, ServerResponse
    from plugins.kits.server.transport import TransportApp, TransportRegistry

    class _App:
        def dispatch(self, request: ServerRequest) -> ServerResponse:
            return ServerResponse(status=204, body={"path": request.path})

        async def dispatch_async(self, request: ServerRequest) -> ServerResponse:
            return self.dispatch(request)

    app = _App()
    assert isinstance(app, TransportApp)
    seen: dict[str, object] = {}

    class _Wire:
        name = "probe"

        def __init__(self, host: str, port: int) -> None:
            self.host = host
            self.port = port

        def start(self, *, blocking: bool = False) -> None:
            return None

        def stop(self) -> None:
            return None

    def factory(bound: TransportApp, host: str, port: int) -> _Wire:
        seen["app"] = bound
        return _Wire(host, port)

    registry = TransportRegistry()
    registry.register("probe", factory)
    made = registry.create("probe", app, host="127.0.0.1", port=9)
    assert made.name == "probe"
    assert made.host == "127.0.0.1"
    assert seen["app"] is app


def test_common_runtimes_no_longer_hosts_server_kit() -> None:
    import importlib.util

    assert importlib.util.find_spec("palm.common.runtimes") is None
