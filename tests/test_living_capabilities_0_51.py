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
from palm.app.host.boot.modes import BootMode
from palm.app.host.composition import (
    ALL_SERVICES,
    DEFAULT_CAPABILITIES,
    SERVER_SURFACES,
    composition_profile_from_name,
)
from palm.app.host.roles import DeploymentProfile
from palm.app.settings import PalmSettings
from palm.core.structure import (
    CAPABILITY_COMPENSATION,
    CAPABILITY_OUTBOX,
    CAPABILITY_PROJECTIONS,
    CAPABILITY_WEBHOOK,
    CAPABILITY_WORK_DRAIN,
)


def _caps(**overrides: object) -> frozenset[str]:
    """Derived capabilities for the light test settings with explicit flag overrides."""
    settings = replace(PalmSettings.for_tests(load_examples=False), **overrides)
    return composition_profile_from_settings(settings).capabilities


# ── the derivation, pinned ───────────────────────────────────────────────────


def test_full_recovery_derives_exactly_default_capabilities() -> None:
    """full_recovery no longer seeds compensation (0.67.11 DNA). Always-on
    workloads is DEFAULT_CAPABILITIES. journal / projections / compensation /
    webhook / analytics are DNA, not composition seeds."""
    profile = composition_profile_from_settings(PalmSettings.for_tests(full_recovery=True))
    assert profile.capabilities == DEFAULT_CAPABILITIES
    assert DEFAULT_CAPABILITIES == frozenset(
        {
            "workloads",
        }
    )


def test_lean_test_settings_derive_the_always_on_capabilities() -> None:
    """for_tests default (full_recovery=False): workloads always-on.
    journal, projections, compensation, webhook, and analytics are DNA."""
    assert _caps() == frozenset({"workloads"})


def test_each_flag_toggles_exactly_its_capability() -> None:
    assert "enable_event_outbox" not in PalmSettings.__dataclass_fields__
    assert "outbox" not in _caps()
    assert "work_drain" not in _caps()
    assert "analytics" not in _caps(analytics_enabled=True)
    assert "analytics" not in _caps(analytics_enabled=False)


def test_journal_is_not_a_composition_seed() -> None:
    """journal has no enable_* flag and is not a composition seed (0.67.7 DNA + hand)."""
    assert "journal" not in _caps()
    assert "journal" not in _caps(
        analytics_enabled=False,
    )


def test_projections_is_not_a_composition_seed() -> None:
    """projections has no enable_* flag and is not a composition seed (0.67.9 DNA + hand)."""
    assert "projections" not in _caps()
    assert "projections" not in _caps(
        analytics_enabled=False,
    )


def test_compensation_is_not_a_composition_seed() -> None:
    """compensation is DNA + hand (0.67.11); not a composition seed."""
    assert "compensation" not in _caps()
    assert "compensation" not in _caps(
        analytics_enabled=False,
    )


def test_webhook_is_not_a_composition_seed() -> None:
    """webhook is DNA + hand (0.67.13); not a composition seed."""
    assert "webhook" not in _caps()
    assert "webhook" not in _caps(
        analytics_enabled=False,
    )


def test_analytics_is_not_a_composition_seed() -> None:
    """analytics is DNA + hand (0.67.16); not a composition seed."""
    assert "analytics" not in _caps()
    assert "analytics" not in _caps(
        analytics_enabled=True,
    )
    assert "analytics" not in _caps(analytics_enabled=False)


# ── behaviour preservation ───────────────────────────────────────────────────


def test_resolver_preserves_services_and_surfaces() -> None:
    """0.51.1 touches only capabilities; services/surfaces stay all_in_one's."""
    profile = composition_profile_from_settings(PalmSettings.for_tests(load_examples=False))
    assert profile.services == ALL_SERVICES == composition_profile_from_name("all_in_one").services
    assert (
        profile.surfaces == SERVER_SURFACES == composition_profile_from_name("all_in_one").surfaces
    )


def test_services_not_gated_by_capabilities_yet() -> None:
    """Service construction is settled by composition.services (0.50), not capabilities:
    a lean-capability host still builds every service."""
    host = ApplicationHost(settings=PalmSettings.for_tests(load_examples=False))
    host.start()
    try:
        # lean test settings derive {workloads} ...
        assert host.composition.capabilities == frozenset({"workloads"})
        # ... yet every service is still built (services are a separate axis)
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
    finally:
        host.shutdown()


# ── 0.51.2: the first gates read the composition, not scattered flags ─────────


def test_compensation_gate_reads_dna_not_composition() -> None:
    """RecoveryCoordinator gates compensation on DNA has_capability (0.67.11).
    Composition omit on a listed phenotype does not hide it. Lean omit is embedded DNA."""
    settings = PalmSettings.for_tests(full_recovery=True)

    listed = ApplicationHost(
        settings=settings,
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    listed.start()
    try:
        assert listed.admission.has_capability(CAPABILITY_COMPENSATION)
        assert listed._recovery.compensation is not None
    finally:
        listed.shutdown()

    lean = ApplicationHost(
        settings=settings,
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    lean.start(structure_definition_id="local.embedded")
    try:
        assert not lean.admission.has_capability(CAPABILITY_COMPENSATION)
        assert lean._recovery.compensation is None
    finally:
        lean.shutdown()


def test_analytics_gate_reads_dna_not_composition() -> None:
    """Admission gates analytics on DNA has_capability (0.67.16).
    Composition omit on a listed phenotype does not hide it.
    Lean omit is embedded DNA. Host product slot aliases the install organ (0.67.17)."""
    from palm.core.structure import CAPABILITY_ANALYTICS

    listed = ApplicationHost.for_mode(
        BootMode.cli(), settings=PalmSettings.for_tests(load_examples=False)
    )
    listed.start()
    try:
        assert listed.admission.has_capability(CAPABILITY_ANALYTICS)
        organ = listed.runtime().install.analytics
        assert organ is not None
        assert listed.analytics is organ
    finally:
        listed.shutdown()

    lean = ApplicationHost.for_mode(
        BootMode.safe(), settings=PalmSettings.for_tests(load_examples=False)
    )
    lean.start()
    try:
        assert not lean.admission.has_capability(CAPABILITY_ANALYTICS)
        assert lean.analytics is None
        assert lean.runtime().install.analytics is None
    finally:
        lean.shutdown()


def test_webhook_gate_reads_dna_not_composition() -> None:
    """RecoveryCoordinator gates webhook on DNA has_capability (0.67.13).
    URLs refine the install dispatcher (0.67.14). Do not mint a recover twin.
    Composition omit on a listed phenotype does not hide it.
    Lean omit is embedded DNA."""
    settings = replace(
        PalmSettings.for_tests(full_recovery=True),
        webhook_urls=["https://example.test/hook"],
    )

    listed = ApplicationHost.for_mode(BootMode.cli(), settings=settings)
    listed.start()
    try:
        assert listed.admission.has_capability(CAPABILITY_WEBHOOK)
        organ = listed.runtime().install.webhook
        assert organ is not None
        assert listed.webhook_dispatcher is organ
        assert listed._recovery.webhook_dispatcher is organ
        assert [t.url for t in organ.targets] == ["https://example.test/hook"]
    finally:
        listed.shutdown()

    lean = ApplicationHost.for_mode(BootMode.safe(), settings=settings)
    lean.start()
    try:
        assert not lean.admission.has_capability(CAPABILITY_WEBHOOK)
        assert lean.webhook_dispatcher is None
        assert lean._recovery.webhook_dispatcher is None
        assert lean.runtime().install.webhook is None
    finally:
        lean.shutdown()


# ── 0.51.3: available (composition) and activated (deployment) ───────────────


def test_outbox_install_follows_dna_not_composition() -> None:
    """Outbox install follows DNA list, not composition write or the old recover AND."""
    settings = PalmSettings.for_tests(full_recovery=True)
    profile = DeploymentProfile.all_in_one()

    on = ApplicationHost(
        settings=settings,
        profile=profile,
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    on.start()
    try:
        assert not on.composition.has("outbox")
        rt = on.runtime()
        definition = rt.structure.definition
        assert definition is not None
        assert definition.has_capability(CAPABILITY_OUTBOX)
        assert CAPABILITY_OUTBOX in rt.structure.materialized_capabilities
        assert "outbox" in rt.supervisor.names()
        assert "outbox" in rt.supervisor.status()["running"]
    finally:
        on.shutdown()

    off = ApplicationHost(
        settings=settings,
        profile=profile,
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    off.start(structure_definition_id="local.embedded")
    try:
        rt = off.runtime()
        definition = rt.structure.definition
        assert definition is not None
        assert not definition.has_capability(CAPABILITY_OUTBOX)
        assert CAPABILITY_OUTBOX not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "outbox" not in rt.supervisor.names()
    finally:
        off.shutdown()


def test_work_drain_settings_side_routes_through_the_capability() -> None:
    """Drain install follows DNA list, not composition write or leftover flag."""
    settings = PalmSettings.for_tests(load_examples=False)
    profile = DeploymentProfile.all_in_one()

    on = ApplicationHost(
        settings=settings,
        profile=profile,
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    on.start()
    try:
        assert not on.composition.has("work_drain")
        rt = on.runtime()
        definition = rt.structure.definition
        assert definition is not None
        assert definition.has_capability(CAPABILITY_WORK_DRAIN)
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
    finally:
        on.shutdown()

    off = ApplicationHost(
        settings=settings,
        profile=profile,
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    off.start(structure_definition_id="local.embedded")
    try:
        rt = off.runtime()
        definition = rt.structure.definition
        assert definition is not None
        assert not definition.has_capability(CAPABILITY_WORK_DRAIN)
        assert CAPABILITY_WORK_DRAIN not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "work_drain" not in rt.supervisor.names()
    finally:
        off.shutdown()


# ── 0.51.4: journal gated by the capability ──────────────────────────────────


def test_journal_gated_by_capability() -> None:
    """Journal wiring is gated by DNA ``has_capability('journal')`` (0.67.7).
    Default hosts list it on server/cli DNA; embedded omits it."""
    from palm.core.structure import CAPABILITY_JOURNAL

    default = ApplicationHost(settings=PalmSettings.for_tests(load_examples=False))
    default.start()
    try:
        assert default.admission.has_capability(CAPABILITY_JOURNAL)
        assert default.event_journal is not None
    finally:
        default.shutdown()

    lean = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    lean.start(structure_definition_id="local.embedded")
    try:
        assert lean.event_journal is None  # DNA omit → no journal
    finally:
        lean.shutdown()


# ── 0.51.5: projections are a capability (the payoff — a lean ApplicationHost) ─


def test_projections_are_a_capability_lean_host_starts_without_them() -> None:
    """The projection layer is gated by DNA has_capability('projections'). Default hosts
    list it; lean “no projections” is embedded DNA, not empty composition on a server
    shape."""
    default = ApplicationHost(settings=PalmSettings.for_tests(load_examples=False))
    default.start()
    try:
        assert default.admission.has_capability(CAPABILITY_PROJECTIONS)
        assert default._instance_projection is not None
    finally:
        default.shutdown()

    lean = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    lean.start(structure_definition_id="local.embedded")
    try:
        assert lean.is_started is True  # it assembles — the payoff of the theme
        assert not lean.admission.has_capability(CAPABILITY_PROJECTIONS)
        assert lean._instance_projection is None
        assert lean._job_board_projection is None
        assert lean._resource_projection is None
        assert lean.pattern_projection("wizard") is None
    finally:
        lean.shutdown()


def test_lean_host_serves_reads_direct_from_runtime() -> None:
    """0.51.6: a projection-less ApplicationHost serves reads via the standalone
    direct-from-runtime handlers — read-complete without a projection layer, and without
    dissolving ServerContext (see docs/SCOUT-0.51.6-serverctx-foldin.md). The reads return
    rather than raising "no handler for query"."""
    from palm.common.cqrs.query import GetJobStatusQuery, ListInstancesQuery, ListJobStatusQuery

    lean = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    lean.start(structure_definition_id="local.embedded")
    try:
        assert lean._instance_projection is None  # no projection layer ...
        # ... yet the read side works, served direct-from-runtime
        assert lean.ask(ListInstancesQuery(include_terminal=True)) == []
        assert lean.ask(ListJobStatusQuery()) == []
        assert lean.ask(GetJobStatusQuery(job_id="nope")) == {"found": False, "job_id": "nope"}
    finally:
        lean.shutdown()
