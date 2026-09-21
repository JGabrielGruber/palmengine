"""BI-003 residual — product packaging parity across composition roots.

Pins that host full, host lean, host-less ServerContext, and host-attached
ServerContext share the same product-identity steps after ``build_all``
(assist↔analytics, design CQRS path, settings-aware analytics).
"""

from __future__ import annotations

from dataclasses import replace

from palm.app.host.application_host import ApplicationHost
from palm.app.host.composition import CompositionProfile, composition_profile_from_name
from palm.app.host.roles import DeploymentProfile
from palm.app.host.services.packaging import apply_product_packaging, bag_from_built
from palm.app.settings import PalmSettings
from palm.runtimes.server.context import ServerContext
from palm.runtimes.server.runtime import ServerRuntime
from palm.services.analytics import AnalyticsService
from palm.services.assist import AssistService
from palm.services.inspect import InspectService


def _assert_product_doors(ctx: ServerContext | ApplicationHost) -> None:
    assert isinstance(ctx.inspect, InspectService)
    assert isinstance(ctx.assist, AssistService)
    assert isinstance(ctx.analytics, AnalyticsService)
    assert isinstance(ctx.definitions, object)
    assert isinstance(ctx.execution, object)
    assert isinstance(ctx.design, object)
    # Shared packaging: assist must see analytics after bind.
    assert ctx.assist.analytics is ctx.analytics


def test_bag_from_built_maps_slots() -> None:
    bag = bag_from_built({"inspect": "i", "assist": "a", "analytics": "x"})
    assert bag.inspect == "i"
    assert bag.assist == "a"
    assert bag.analytics == "x"
    assert bag.session is None


def test_host_full_product_packaging() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        _assert_product_doors(host)
        assert host.schemas is not None


def test_host_lean_product_packaging() -> None:
    """Lean host: DNA omit still builds other product services.

    Lean omit is embedded DNA (0.67.9). Analytics leftover (0.67.17): DNA omit
    drops the host slot even when composition.services includes analytics.
    """
    composition = CompositionProfile(
        services=composition_profile_from_name("all_in_one").services,
        surfaces=(),
        capabilities=frozenset(),
    )
    settings = replace(
        PalmSettings.for_tests(),
        structure_definition_id="local.embedded",
    )
    with ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        composition=composition,
    ) as host:
        assert isinstance(host.inspect, InspectService)
        assert isinstance(host.assist, AssistService)
        assert isinstance(host.definitions, object)
        assert isinstance(host.execution, object)
        assert isinstance(host.design, object)
        assert host.analytics is None
        assert host.assist.analytics is None
        assert not host.composition.has("projections")
        assert not host.admission.has_capability("projections")
        assert not host.admission.has_capability("analytics")


def test_hostless_server_context_product_packaging() -> None:
    settings = replace(PalmSettings.for_tests(), analytics_default_limit=42)
    runtime = ServerRuntime(host="127.0.0.1", port=0)
    runtime.start(http=False)
    try:
        ctx = ServerContext(runtime, host=None, settings=settings)
        _assert_product_doors(ctx)
        assert ctx.settings.analytics_default_limit == 42
        assert ctx.analytics._default_limit == 42  # settings-aware packaging
        assert ctx.runtime is runtime
        assert ctx.host is None
        assert isinstance(ctx.wait_until_idle(timeout=0.1), bool)
    finally:
        runtime.stop()


def test_host_attached_server_context_shares_host_services() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        runtime = host.app.runtime()
        ctx = ServerContext(runtime, host=host)
        assert ctx.assist is host.assist
        assert ctx.analytics is host.analytics
        assert ctx.assist.analytics is host.analytics
        assert ctx.runtime is runtime
        assert ctx.settings is host.settings


def test_standalone_then_attach_host_switches_doors() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        runtime = host.app.runtime()
        standalone = ServerContext(runtime, host=None, settings=PalmSettings.for_tests())
        _assert_product_doors(standalone)
        assert standalone.assist is not host.assist
        standalone.attach_host(host)
        assert standalone.assist is host.assist
        assert standalone.analytics is host.analytics


def test_apply_product_packaging_binds_analytics() -> None:
    """Unit: packaging helper binds without full runtime when doubles are enough."""
    from palm.common.cqrs.bus import CommandBus, QueryBus

    class _Assist:
        def __init__(self) -> None:
            self._analytics = None

        @property
        def analytics(self) -> object | None:
            return self._analytics

        def bind_analytics(self, analytics: object | None) -> None:
            self._analytics = analytics

    assist = _Assist()
    analytics = object()
    built = {
        "assist": assist,
        "analytics": analytics,
        "design": None,
        "execution": None,
    }
    bag = apply_product_packaging(
        built,
        command_bus=CommandBus(),
        query_bus=QueryBus(),
        repository=object(),
        instance_manager=object(),
        storage=None,
    )
    assert bag.assist is assist
    assert assist.analytics is analytics
