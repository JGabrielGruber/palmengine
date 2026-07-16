"""Tests for ``palm host`` CLI subcommand."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from palm.app import DeploymentProfile
from palm.app.settings import PalmSettings
from palm.runtimes.cli.cli import _host_profile_from_invocation, main
from palm.runtimes.cli.shared.args import CliInvocation


@pytest.mark.parametrize(
    ("host_cmd", "expected_roles"),
    [
        ("all-in-one", frozenset({"master", "worker"})),
        ("all_in_one", frozenset({"master", "worker"})),
        ("master", frozenset({"master"})),
        ("worker", frozenset({"worker"})),
        ("server", frozenset({"worker", "server"})),
    ],
)
def test_host_profile_from_invocation(host_cmd: str, expected_roles: frozenset[str]) -> None:
    inv = CliInvocation(command="host", host_cmd=host_cmd)
    profile = _host_profile_from_invocation(inv)
    assert profile.roles == expected_roles


def test_host_profile_worker_count() -> None:
    inv = CliInvocation(command="host", host_cmd="worker", host_workers=3)
    profile = _host_profile_from_invocation(inv)
    assert profile.worker_count == 3


def test_host_profile_server_bind() -> None:
    inv = CliInvocation(command="host", host_cmd="server", host_bind="0.0.0.0", host_port=9000)
    profile = _host_profile_from_invocation(inv)
    assert profile.server_host == "0.0.0.0"
    assert profile.server_port == 9000


def test_host_profile_server_uses_palm_settings() -> None:
    inv = CliInvocation(command="host", host_cmd="server")
    settings = PalmSettings.for_tests()
    settings.server_host = "0.0.0.0"
    settings.server_port = 8090
    profile = _host_profile_from_invocation(inv, settings)
    assert profile.server_host == "0.0.0.0"
    assert profile.server_port == 8090


def test_host_profile_server_cli_overrides_settings() -> None:
    inv = CliInvocation(command="host", host_cmd="server", host_port=9001)
    settings = PalmSettings.for_tests()
    settings.server_port = 8090
    profile = _host_profile_from_invocation(inv, settings)
    assert profile.server_port == 9001


def test_main_host_all_in_one_starts_host() -> None:
    captured: dict[str, object] = {}

    def fake_run_host(profile: DeploymentProfile, *, settings: PalmSettings | None = None) -> None:
        captured["profile"] = profile
        captured["settings"] = settings

    with patch("palm.runtimes.cli.cli.run_host", fake_run_host):
        exit_code = main(["--storage-backend", "memory", "host", "all-in-one"])

    assert exit_code == 0
    profile = captured["profile"]
    assert isinstance(profile, DeploymentProfile)
    assert profile.roles == frozenset({"master", "worker"})


def test_main_host_master_starts_host() -> None:
    captured: dict[str, object] = {}

    def fake_run_host(profile: DeploymentProfile, *, settings: PalmSettings | None = None) -> None:
        captured["profile"] = profile

    with patch("palm.runtimes.cli.cli.run_host", fake_run_host):
        exit_code = main(["host", "master"])

    assert exit_code == 0
    profile = captured["profile"]
    assert isinstance(profile, DeploymentProfile)
    assert profile.roles == frozenset({"master"})
