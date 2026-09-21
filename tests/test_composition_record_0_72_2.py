"""0.72.2 — the host builds CompositionProfile from a saved record.

Preset classmethods are not the path. Package names stay off this record (0.72.3).
"""

from __future__ import annotations

import pytest

from palm.app.bootstrap import composition_profile_from_settings
from palm.app.host.application_host import ApplicationHost
from palm.app.host.boot.modes import BootMode
from palm.app.host.composition import (
    COMPOSITION_RECORDS,
    CompositionProfile,
    composition_profile_from_name,
    composition_record,
)
from palm.app.host.roles import DeploymentProfile
from palm.app.settings import PalmSettings

_PRESET_NAMES = ("all_in_one", "server", "embedded", "worker", "cli", "mcp")


def test_saved_records_name_the_shipped_shapes() -> None:
    assert tuple(row.name for row in COMPOSITION_RECORDS) == _PRESET_NAMES
    assert len({row.name for row in COMPOSITION_RECORDS}) == len(COMPOSITION_RECORDS)


def test_preset_methods_are_not_on_the_profile() -> None:
    for name in _PRESET_NAMES:
        assert not hasattr(CompositionProfile, name)


def test_from_record_builds_the_embedded_shape() -> None:
    record = composition_record("embedded")
    profile = CompositionProfile.from_record(record)
    assert profile.services == ("inspect", "session", "definitions", "execution")
    assert profile.surfaces == ()
    assert profile.capabilities == frozenset()
    assert profile == composition_profile_from_name("embedded")


def test_unknown_record_name_fails() -> None:
    with pytest.raises(ValueError, match="Unknown composition record"):
        composition_record("nope")


def test_settings_resolver_builds_from_the_all_in_one_record() -> None:
    record = composition_record("all_in_one")
    profile = composition_profile_from_settings(PalmSettings.for_tests(load_examples=False))
    assert profile.services == record.services
    assert profile.surfaces == record.surfaces
    assert profile.capabilities == frozenset({"workloads"})


@pytest.mark.parametrize(
    ("mode_name", "record_name"),
    [
        ("safe", "embedded"),
        ("test", "embedded"),
        ("dev", "all_in_one"),
        ("prod", "server"),
        ("cli", "cli"),
        ("mcp", "mcp"),
        ("worker", "worker"),
        ("server", "server"),
        ("all_in_one", "all_in_one"),
    ],
)
def test_boot_mode_builds_from_the_saved_record(mode_name: str, record_name: str) -> None:
    assert getattr(BootMode, mode_name)().composition == composition_profile_from_name(record_name)


def test_host_without_mode_builds_server_worker_cli_from_records() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    cases = (
        (DeploymentProfile.server_only(port=0), "server"),
        (DeploymentProfile.worker_only(), "worker"),
        (DeploymentProfile.master_only(), "cli"),
    )
    for profile, record_name in cases:
        host = ApplicationHost(settings=settings, profile=profile)
        assert host.boot_mode is None
        assert host.composition == composition_profile_from_name(record_name)


def test_host_all_in_one_builds_from_settings_and_the_record() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    record = composition_record("all_in_one")
    built = composition_profile_from_settings(settings, deployment=host.profile)
    assert host.composition.services == record.services
    assert host.composition.surfaces == record.surfaces
    assert host.composition == built
