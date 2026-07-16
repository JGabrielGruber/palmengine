"""0.44.1 — server host profile enables background work drain by default."""

from __future__ import annotations

from palm.app import ApplicationHost, PalmSettings
from palm.app.host.roles import DeploymentProfile


def test_server_profile_starts_work_drain_without_env() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    assert settings.enable_work_drain_service is False
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.server_only(port=0),
    )
    host.start()
    try:
        assert host.profile.enable_work_drain_service is True
        assert host._work_drain_background_enabled() is True
        assert host.work_drain is not None
        assert host.work_drain.is_running is True
    finally:
        host.shutdown()


def test_all_in_one_profile_does_not_auto_drain() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        assert host.profile.enable_work_drain_service is False
        assert host._work_drain_background_enabled() is False
        assert host.work_drain is not None
        assert host.work_drain.is_running is False
    finally:
        host.shutdown()