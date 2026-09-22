"""0.63.12 — run_host / deployment profile seeds DNA without BootMode."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import LOCAL_ALL_IN_ONE_ID, LOCAL_SERVER_ID, LOCAL_WORKER_ID
from palm.system.log import reset_system_log_for_tests
from palm.system.structure import boot_mode_name_for_deployment


def test_deployment_to_seed_names() -> None:
    assert boot_mode_name_for_deployment(DeploymentProfile.server_only()) == "server"
    assert boot_mode_name_for_deployment(DeploymentProfile.worker_only()) == "worker"
    assert boot_mode_name_for_deployment(DeploymentProfile.all_in_one()) == "all_in_one"
    assert boot_mode_name_for_deployment(DeploymentProfile.master_only()) == "cli"


def test_host_server_profile_seeds_local_server() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.server_only(port=0),
    )
    host.start()
    try:
        assert host.boot_mode is None
        assert host.admission.definition_id == LOCAL_SERVER_ID
        assert host.admission.may_run_business is True
    finally:
        host.shutdown()


def test_host_worker_profile_seeds_local_worker() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.worker_only(),
    )
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_WORKER_ID
    finally:
        host.shutdown()


def test_host_all_in_one_profile_seeds_all_in_one() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_ALL_IN_ONE_ID
    finally:
        host.shutdown()
