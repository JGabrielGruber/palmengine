"""CompositionProfile skeleton (0.50.1).

Pins the profile against what ApplicationHost builds *today* so a preset can't
silently drift from reality — especially ``all_in_one.services`` vs the actual
``CORE_SERVICE_PROVIDERS``. The profile is declared here but not yet wired
(0.50.2+ makes the host assemble from it); these tests are the safety net for
that transition. See VISION-0.50 / ADR-019.
"""

from __future__ import annotations

import bundles.standard.app
from bundles.standard.app import ApplicationHost
from bundles.standard.app.bootstrap import composition_profile_from_settings
from bundles.standard.app.host.composition import (
    ALL_SERVICES,
    CORE_SERVICES,
    SERVER_SURFACES,
    composition_profile_from_name,
)
from bundles.standard.app.host.composition import (
    CompositionProfile as CP,
)
from bundles.standard.app.host.services.providers import CORE_SERVICE_PROVIDERS
from bundles.standard.app.settings import PalmSettings


def test_composition_profile_is_public_api() -> None:
    """Exported from `bundles.standard.app` (and `bundles.standard.app.host`) like DeploymentProfile."""
    assert bundles.standard.app.CompositionProfile is CP
    assert "CompositionProfile" in bundles.standard.app.__all__


def test_all_in_one_services_match_what_host_builds_today() -> None:
    """The default composition must equal the services the host actually constructs."""
    built = tuple(provider.name for provider in CORE_SERVICE_PROVIDERS)
    assert composition_profile_from_name("all_in_one").services == built
    assert ALL_SERVICES == built  # the constant is the single source of truth


def test_default_resolver_matches_all_in_one_services_and_surfaces() -> None:
    """0.51.1: the resolver now *derives* capabilities from settings, but services and
    surfaces still match all_in_one (their behaviour was settled in 0.50 — preserved).
    Capability derivation itself is pinned in test_living_capabilities_0_51.py."""
    profile = composition_profile_from_settings(PalmSettings.for_tests(load_examples=False))
    assert profile.services == composition_profile_from_name("all_in_one").services
    assert profile.surfaces == composition_profile_from_name("all_in_one").surfaces


def test_presets_declare_the_shapes_palm_ships() -> None:
    # all_in_one has every surface available (the server deployment mounts them).
    # webhook membership is DNA (0.67.13), not a composition preset.
    assert composition_profile_from_name("server").surfaces == SERVER_SURFACES
    assert composition_profile_from_name("all_in_one").surfaces == SERVER_SURFACES
    assert not composition_profile_from_name("server").has("webhook")
    assert not composition_profile_from_name("all_in_one").has("webhook")

    # embedded (palmengine-django) is minimal: core services, no surfaces, no background
    embedded = composition_profile_from_name("embedded")
    assert embedded.services == CORE_SERVICES
    assert embedded.surfaces == ()
    assert embedded.capabilities == frozenset()
    assert not embedded.has("work_drain")

    # worker is headless execution; drain/outbox membership is DNA, not composition
    assert composition_profile_from_name("worker").services == ("execution",)
    assert not composition_profile_from_name("worker").has("outbox")
    assert not composition_profile_from_name("worker").has("work_drain")
    assert not composition_profile_from_name("cli").has("work_drain")
    assert not composition_profile_from_name("all_in_one").has("work_drain")
    assert not composition_profile_from_name("server").has("work_drain")
    assert composition_profile_from_name("mcp").surfaces == ("mcp",)


def test_profile_is_frozen_and_hashable() -> None:
    a, b = composition_profile_from_name("all_in_one"), composition_profile_from_name("all_in_one")
    assert a == b
    assert hash(a) == hash(b)  # frozen dataclass — usable as a key / in a set
    assert a is not b


def test_helpers() -> None:
    server = composition_profile_from_name("server")
    assert server.exposes("rest") and not server.exposes("nope")
    assert server.has("workloads") and not server.has("nope")
    assert not server.has("analytics")


# ── 0.50.2: the host reads its composition ───────────────────────────────────


def test_host_default_composition_builds_all_services() -> None:
    """Behavior-preserving: the default host still builds every service."""
    host = ApplicationHost(settings=PalmSettings.for_tests(load_examples=False))
    host.start()
    try:
        assert host.composition.services == composition_profile_from_name("all_in_one").services
        for name in (
            "inspect",
            "session",
            "definitions",
            "execution",
            "assist",
            "design",
            "analytics",
        ):
            assert getattr(host, name) is not None
        # SD-007 migration alias
        assert host.system is host.inspect
    finally:
        host.shutdown()


def test_host_embedded_composition_builds_core_only() -> None:
    """The embedded/lib shape is now real: core services only, and it starts clean."""
    host = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        composition=composition_profile_from_name("embedded"),
    )
    host.start()
    try:
        assert host.composition.services == (
            "inspect",
            "session",
            "definitions",
            "execution",
        )
        assert host.inspect is not None
        assert host.system is host.inspect
        assert host.session is not None
        assert host.definitions is not None
        assert host.execution is not None
        assert host.assist is None
        assert host.design is None
        # 0.67.17: host.analytics is the install organ. Embedded composition
        # infers cli DNA, which lists analytics; product service is still omitted.
        from palm.services.analytics import AnalyticsService

        assert host.analytics is host.runtime().install.analytics
        assert host.analytics is not None
        assert not isinstance(host.analytics, AnalyticsService)
    finally:
        host.shutdown()


# ── 0.50.3: surfaces driven by the profile ───────────────────────────────────


def test_default_surfaces_respects_composition_filter() -> None:
    """`only` (a composition's surfaces) narrows what the server mounts; None = all."""
    from bundles.standard.runtimes.server import ServerRuntime
    from bundles.standard.runtimes.server.context import ServerContext
    from bundles.standard.runtimes.server.surfaces import default_surfaces

    ctx = ServerContext(ServerRuntime())
    full = default_surfaces(ctx)  # None → all (rest + 4)
    assert len(full) == 5

    filtered = default_surfaces(ctx, only=("rest", "mcp"))
    assert len(filtered) == 2  # rest + mcp only

    # all_in_one mounts everything (server-deploy behaviour-preserving)
    assert (
        len(default_surfaces(ctx, only=composition_profile_from_name("all_in_one").surfaces)) == 5
    )


# ── host query flats (grouping objects composted 0.68.15) ────────────────────


def test_host_query_flats_list_without_grouping_objects() -> None:
    """CLI query surface is the flat methods; grouping objects are gone."""
    host = ApplicationHost(settings=PalmSettings.for_tests(load_examples=False))
    host.start()
    try:
        assert not hasattr(host, "instances")
        assert not hasattr(host, "jobs")
        assert not hasattr(host, "wizards")
        assert host.list_instance_views(include_terminal=False) == []
        assert host.list_job_views() == []
        assert host.list_wizard_progress_views() == []
        assert host.get_instance_view("nope") is None
    finally:
        host.shutdown()
