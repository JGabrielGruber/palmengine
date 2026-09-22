"""0.63.19 — membership enable_* catalog (SD-021 residual cartography)."""

from __future__ import annotations

from bundles.standard.app.bootstrap import composition_profile_from_settings
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.system.structure import (
    ALWAYS_ON_MEMBERSHIP_CAPABILITIES,
    MEMBERSHIP_CAPABILITY_SEEDS,
    STRUCTURE_SEED_ENV,
    admission_inventory,
    membership_capabilities_from_settings,
)


def test_membership_capability_seeds_catalog_complete() -> None:
    caps = {row["capability"] for row in MEMBERSHIP_CAPABILITY_SEEDS}
    assert caps == set()
    assert "outbox" not in caps
    assert "work_drain" not in caps
    assert "journal" not in caps  # DNA + hand, not a composition seed
    assert "projections" not in caps  # DNA + hand (0.67.9)
    assert "compensation" not in caps  # DNA + hand (0.67.11)
    assert "webhook" not in caps  # DNA + hand (0.67.13)
    assert "analytics" not in caps  # DNA + hand (0.67.16)
    settings_fields = {row["settings"] for row in MEMBERSHIP_CAPABILITY_SEEDS}
    assert "enable_compensation" not in settings_fields
    assert "enable_webhook_dispatcher" not in settings_fields
    assert "enable_work_drain_service" not in settings_fields
    assert "analytics_enabled" not in settings_fields


def test_structure_seed_env_includes_all_membership_seeds() -> None:
    roles = {row["role"] for row in STRUCTURE_SEED_ENV}
    assert "explicit_definition_seed" in roles
    assert "membership_seed" not in roles
    assert "deployment_seed" in roles
    member_envs = {row["env"] for row in STRUCTURE_SEED_ENV if row["role"] == "membership_seed"}
    assert "PALM_ENABLE_COMPENSATION" not in member_envs
    assert "PALM_ENABLE_WORK_DRAIN_SERVICE" not in member_envs
    assert "PALM_ENABLE_EVENT_OUTBOX" not in member_envs
    assert "PALM_ENABLE_WEBHOOK_DISPATCHER" not in member_envs
    assert "PALM_ANALYTICS_ENABLED" not in member_envs
    assert "PALM_ENABLE_NEONROOT_RUNNERS" not in member_envs


def _lean_settings(**overrides: object) -> PalmSettings:
    """Explicit lean settings — avoids developer .env membership seeds."""
    base: dict[str, object] = {
        "load_example_definitions": False,
        "storage_backend": "memory",
        "rebuild_projections_on_startup": False,
        "reconcile_instances_on_startup": False,
        "analytics_enabled": True,
    }
    base.update(overrides)
    return PalmSettings(**base)  # type: ignore[arg-type]


def test_membership_capabilities_from_settings_defaults_and_flags() -> None:
    lean = _lean_settings()
    caps = membership_capabilities_from_settings(lean)
    assert ALWAYS_ON_MEMBERSHIP_CAPABILITIES <= caps
    assert "neonroot" not in caps
    assert "analytics" not in caps
    assert "compensation" not in caps
    assert "outbox" not in caps
    assert "work_drain" not in caps

    assert "enable_event_outbox" not in PalmSettings.__dataclass_fields__


def test_deployment_does_not_write_work_drain_membership() -> None:
    settings = _lean_settings()
    assert "work_drain" not in membership_capabilities_from_settings(settings)
    fed = membership_capabilities_from_settings(
        settings,
        deployment=DeploymentProfile.server_only(),
    )
    assert "work_drain" not in fed


def test_bootstrap_uses_membership_seed_map() -> None:
    settings = PalmSettings(
        load_example_definitions=False,
        storage_backend="memory",
        analytics_enabled=False,
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )
    profile = composition_profile_from_settings(settings)
    assert not profile.has("compensation")
    assert not profile.has("outbox")
    assert not profile.has("webhook")
    assert not profile.has("work_drain")
    assert not profile.has("analytics")
    # Always-on on settings-composed path (journal/projections are DNA, not composition)
    assert not profile.has("journal")
    assert not profile.has("projections")
    assert profile.has("workloads")


def test_admission_inventory_catalog_paid_env_structure() -> None:
    body = admission_inventory()
    gated_ids = {c["id"] for c in body["gated_paths"]}
    assert "env.membership_seed_catalog" in gated_ids
    pretenders = {p["id"]: p for p in body["readiness_edges"]}
    assert pretenders["env.structure_toggles"]["status"] == "paid_catalog_0_63_19"
    assert "outbox.start_option_seed" in pretenders
