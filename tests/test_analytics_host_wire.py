"""0.35.4a — AnalyticsService on ApplicationHost / ServerContext."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from bundles.standard.runtimes.server.context import ServerContext
from palm.services.analytics import AnalyticsService


def test_host_exposes_analytics() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        assert isinstance(host.analytics, AnalyticsService)
        assert isinstance(host.analytics.list_datasets(), list)


def test_server_context_standalone_and_host() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        runtime = host.app.runtime()
        standalone = ServerContext(runtime, host=None)
        assert isinstance(standalone.analytics, AnalyticsService)
        via_host = ServerContext(runtime, host=host)
        assert via_host.analytics is host.analytics
        standalone.attach_host(host)
        assert standalone.analytics is host.analytics
