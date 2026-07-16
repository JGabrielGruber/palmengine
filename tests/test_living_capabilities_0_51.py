"""Living Capabilities (0.51.1) — the resolver derives capabilities from settings.

Derived, **not yet gating**: 0.51.1 makes ``composition_profile_from_settings`` compute
``capabilities`` from the ``enable_*`` flags, pinned against today's effective wiring,
*before* any host machinery reads them (0.51.2+ switches each gate to
``composition.has(...)``). These tests are the safety net for that transition — they lock
the derivation so a later gate can't silently change what a shape wires. See VISION-0.51 /
ADR-020.
"""

from __future__ import annotations

from dataclasses import replace

from palm.app import ApplicationHost
from palm.app.bootstrap import composition_profile_from_settings
from palm.app.host.composition import (
    ALL_SERVICES,
    DEFAULT_CAPABILITIES,
    SERVER_SURFACES,
)
from palm.app.host.composition import CompositionProfile as CP
from palm.app.host.roles import DeploymentProfile
from palm.app.settings import PalmSettings


def _caps(**overrides: object) -> frozenset[str]:
    """Derived capabilities for the light test settings with explicit flag overrides."""
    settings = PalmSettings.for_tests(load_examples=False).model_copy(update=overrides)
    return composition_profile_from_settings(settings).capabilities


# ── the derivation, pinned ───────────────────────────────────────────────────


def test_full_recovery_derives_exactly_default_capabilities() -> None:
    """full_recovery turns on compensation + outbox; with analytics + always-on journal
    that is exactly DEFAULT_CAPABILITIES — the production-default shape."""
    profile = composition_profile_from_settings(PalmSettings.for_tests(full_recovery=True))
    assert profile.capabilities == DEFAULT_CAPABILITIES
    assert DEFAULT_CAPABILITIES == frozenset({"outbox", "compensation", "journal", "analytics"})


def test_lean_test_settings_derive_journal_and_analytics_only() -> None:
    """for_tests default (full_recovery=False): compensation + outbox off, analytics on,
    journal always available."""
    assert _caps() == frozenset({"journal", "analytics"})


def test_each_flag_toggles_exactly_its_capability() -> None:
    assert "compensation" in _caps(enable_compensation=True)
    assert "compensation" not in _caps(enable_compensation=False)
    assert "outbox" in _caps(enable_event_outbox=True)
    assert "outbox" not in _caps(enable_event_outbox=False)
    assert "webhook" in _caps(enable_webhook_dispatcher=True)
    assert "webhook" not in _caps(enable_webhook_dispatcher=False)
    assert "work_drain" in _caps(enable_work_drain_service=True)
    assert "work_drain" not in _caps(enable_work_drain_service=False)
    assert "analytics" in _caps(analytics_enabled=True)
    assert "analytics" not in _caps(analytics_enabled=False)


def test_journal_is_always_available_no_flag() -> None:
    """journal has no enable_* flag — it is wired on infra-readiness, so it is always
    part of a settings-derived composition."""
    assert "journal" in _caps()
    assert "journal" in _caps(
        enable_compensation=False,
        enable_event_outbox=False,
        analytics_enabled=False,
    )


# ── behaviour preservation ───────────────────────────────────────────────────


def test_resolver_preserves_services_and_surfaces() -> None:
    """0.51.1 touches only capabilities; services/surfaces stay all_in_one's."""
    profile = composition_profile_from_settings(PalmSettings.for_tests(load_examples=False))
    assert profile.services == ALL_SERVICES == CP.all_in_one().services
    assert profile.surfaces == SERVER_SURFACES == CP.all_in_one().surfaces


def test_services_not_gated_by_capabilities_yet() -> None:
    """Service construction is settled by composition.services (0.50), not capabilities:
    a lean-capability host still builds every service."""
    host = ApplicationHost(settings=PalmSettings.for_tests(load_examples=False))
    host.start()
    try:
        # lean test settings derive only {journal, analytics} ...
        assert host.composition.capabilities == frozenset({"journal", "analytics"})
        # ... yet every service is still built (services are a separate axis)
        for name in ("system", "definitions", "execution", "assist", "design", "analytics"):
            assert getattr(host, name) is not None
    finally:
        host.shutdown()


# ── 0.51.2: the first gates read the composition, not scattered flags ─────────


def test_compensation_gate_reads_composition_not_settings() -> None:
    """RecoveryCoordinator gates compensation on composition.has('compensation'); an
    explicit composition wins over settings.enable_compensation (which full_recovery sets)."""
    settings = PalmSettings.for_tests(full_recovery=True)  # enable_compensation=True

    with_cap = ApplicationHost(
        settings=settings,
        composition=replace(CP.all_in_one(), capabilities=frozenset({"compensation"})),
    )
    with_cap.start()
    try:
        assert with_cap._recovery.compensation is not None
    finally:
        with_cap.shutdown()

    without_cap = ApplicationHost(
        settings=settings,  # settings still enable compensation ...
        composition=replace(CP.all_in_one(), capabilities=frozenset()),  # ... composition omits it
    )
    without_cap.start()
    try:
        assert without_cap._recovery.compensation is None  # capability axis wins
    finally:
        without_cap.shutdown()


def test_webhook_gate_reads_composition_not_settings() -> None:
    """The webhook dispatcher is gated by composition.has('webhook'); settings.webhook_urls
    still configure it (refine, not bypass). Composition omitting 'webhook' wins over
    settings.enable_webhook_dispatcher."""
    settings = PalmSettings.for_tests(full_recovery=True).model_copy(
        update={
            "enable_webhook_dispatcher": True,
            "webhook_urls": ["https://example.test/hook"],
        }
    )

    with_cap = ApplicationHost(
        settings=settings,
        composition=replace(CP.all_in_one(), capabilities=frozenset({"webhook"})),
    )
    with_cap.start()
    try:
        assert with_cap._recovery._build_webhook_dispatcher() is not None
    finally:
        with_cap.shutdown()

    without_cap = ApplicationHost(
        settings=settings,  # settings still enable the dispatcher + provide urls ...
        composition=replace(CP.all_in_one(), capabilities=frozenset()),  # ... composition omits it
    )
    without_cap.start()
    try:
        assert without_cap._recovery._build_webhook_dispatcher() is None  # capability axis wins
    finally:
        without_cap.shutdown()


# ── 0.51.3: available (composition) and activated (deployment) ───────────────


def test_outbox_drainer_is_available_times_activated() -> None:
    """The outbox drainer is composition.has('outbox') AND the deployment role (master +
    enable_outbox_service). A composition omitting 'outbox' stops the drainer even on a
    master that would otherwise activate it."""
    settings = PalmSettings.for_tests(full_recovery=True)  # enable_event_outbox → has('outbox')
    master = DeploymentProfile.all_in_one()  # master=True, enable_outbox_service=True

    with_cap = ApplicationHost(
        settings=settings,
        profile=master,
        composition=replace(CP.all_in_one(), capabilities=frozenset({"outbox"})),
    )
    with_cap.start()
    try:
        assert with_cap.outbox_service is not None  # available AND activated
    finally:
        with_cap.shutdown()

    without_cap = ApplicationHost(
        settings=settings,
        profile=master,  # role would activate ...
        composition=replace(CP.all_in_one(), capabilities=frozenset()),  # ... but not available
    )
    without_cap.start()
    try:
        assert without_cap.outbox_service is None  # don't drain an outbox you don't have
    finally:
        without_cap.shutdown()


def test_work_drain_settings_side_routes_through_the_capability() -> None:
    """work_drain keeps its 0.44.1 OR semantics (either source enables it), but the
    settings side now routes through composition.has('work_drain'): an explicit composition
    declaring it enables the drain even when the deployment profile does not activate it."""
    settings = PalmSettings.for_tests(load_examples=False)  # enable_work_drain_service False
    profile = DeploymentProfile.all_in_one()  # enable_work_drain_service False

    on = ApplicationHost(
        settings=settings,
        profile=profile,
        composition=replace(CP.all_in_one(), capabilities=frozenset({"work_drain"})),
    )
    on.start()
    try:
        assert on._work_drain_background_enabled() is True  # capability side of the OR
    finally:
        on.shutdown()

    off = ApplicationHost(
        settings=settings,
        profile=profile,
        composition=replace(CP.all_in_one(), capabilities=frozenset()),
    )
    off.start()
    try:
        assert off._work_drain_background_enabled() is False  # neither source enables it
    finally:
        off.shutdown()


# ── 0.51.4: journal gated by the capability ──────────────────────────────────


def test_journal_gated_by_capability() -> None:
    """Journal wiring is gated by composition.has('journal'). The resolver always derives
    it (no settings flag), so default hosts keep their journal; an explicit lean
    composition that omits it wires none."""
    default = ApplicationHost(settings=PalmSettings.for_tests(load_examples=False))
    default.start()
    try:
        assert "journal" in default.composition.capabilities
        assert default.event_journal is not None
    finally:
        default.shutdown()

    lean = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        composition=replace(CP.all_in_one(), capabilities=frozenset()),
    )
    lean.start()
    try:
        assert lean.event_journal is None  # capability omitted → no journal
    finally:
        lean.shutdown()
