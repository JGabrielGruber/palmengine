"""CompositionProfile skeleton (0.50.1).

Pins the profile against what ApplicationHost builds *today* so a preset can't
silently drift from reality — especially ``all_in_one.services`` vs the actual
``CORE_SERVICE_PROVIDERS``. The profile is declared here but not yet wired
(0.50.2+ makes the host assemble from it); these tests are the safety net for
that transition. See VISION-0.50 / ADR-019.
"""

from __future__ import annotations

import palm.app
from palm.app.bootstrap import composition_profile_from_settings
from palm.app.host.composition import (
    ALL_SERVICES,
    CORE_SERVICES,
    SERVER_SURFACES,
)
from palm.app.host.composition import (
    CompositionProfile as CP,
)
from palm.app.host.services.providers import CORE_SERVICE_PROVIDERS
from palm.app.settings import PalmSettings


def test_composition_profile_is_public_api() -> None:
    """Exported from `palm.app` (and `palm.app.host`) like DeploymentProfile."""
    assert palm.app.CompositionProfile is CP
    assert "CompositionProfile" in palm.app.__all__


def test_all_in_one_services_match_what_host_builds_today() -> None:
    """The default composition must equal the services the host actually constructs."""
    built = tuple(provider.name for provider in CORE_SERVICE_PROVIDERS)
    assert CP.all_in_one().services == built
    assert ALL_SERVICES == built  # the constant is the single source of truth


def test_default_resolver_is_all_in_one_today() -> None:
    """0.50.1: the resolver returns the current default composition (no behavior change)."""
    profile = composition_profile_from_settings(PalmSettings.for_tests(load_examples=False))
    assert profile == CP.all_in_one()


def test_presets_declare_the_shapes_palm_ships() -> None:
    # server exposes all its surfaces + webhook; all_in_one exposes none
    assert CP.server().surfaces == SERVER_SURFACES
    assert CP.all_in_one().surfaces == ()
    assert CP.server().has("webhook")
    assert not CP.all_in_one().has("webhook")

    # embedded (palmengine-django) is minimal: core services, no surfaces, no background
    embedded = CP.embedded()
    assert embedded.services == CORE_SERVICES
    assert embedded.surfaces == ()
    assert embedded.capabilities == frozenset()
    assert not embedded.has("work_drain")

    # worker is headless execution + drain; mcp exposes only the mcp surface
    assert CP.worker().services == ("execution",)
    assert CP.worker().has("work_drain")
    assert CP.mcp().surfaces == ("mcp",)


def test_profile_is_frozen_and_hashable() -> None:
    a, b = CP.all_in_one(), CP.all_in_one()
    assert a == b
    assert hash(a) == hash(b)  # frozen dataclass — usable as a key / in a set
    assert a is not b


def test_helpers() -> None:
    server = CP.server()
    assert server.exposes("rest") and not server.exposes("nope")
    assert server.has("compensation") and not server.has("nope")
