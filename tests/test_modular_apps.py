"""Tests for Django-style modular pattern/provider/storage apps."""

from __future__ import annotations

import importlib

import pytest

from palm.common.storage import StorageFactory
from palm.common.transforms._apps import INSTALLED_TRANSFORMS
from palm.common.transforms._apps import autoload as autoload_transforms
from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.core.transform.registry import transform_registry
from palm.patterns._apps import INSTALLED_PATTERNS
from palm.patterns._registry import get_builder, registered_builders
from palm.providers._apps import INSTALLED_PROVIDERS
from palm.storages._apps import CORE_STORAGES, INSTALLED_STORAGES, OPTIONAL_STORAGES


@pytest.fixture(autouse=True)
def _reload_apps() -> None:
    """Ensure registries are populated for isolated assertions."""
    importlib.import_module("palm.patterns")
    importlib.import_module("palm.providers")
    importlib.import_module("palm.storages")
    autoload_transforms()


def test_installed_pattern_apps_register() -> None:
    assert set(INSTALLED_PATTERNS) == {"dag", "etl", "parallel", "pipeline", "wizard"}
    for name in INSTALLED_PATTERNS:
        pattern_registry.get(name)

    assert get_builder("pipeline") is not None
    assert set(registered_builders()) == set(INSTALLED_PATTERNS)
    for name in INSTALLED_PATTERNS:
        assert get_builder(name) is not None


def test_installed_provider_apps_register() -> None:
    from palm.common.providers.app import ProviderApp
    from palm.providers._registry import get_provider_app, installed_provider_apps

    assert set(INSTALLED_PROVIDERS) == {"rest", "graphql", "postgres", "palm", "kv", "file"}
    for name in INSTALLED_PROVIDERS:
        provider_registry.get(name)

    for name in INSTALLED_PROVIDERS:
        app = get_provider_app(name)
        assert app is not None
        assert isinstance(app, ProviderApp)
        assert app.name == name
    assert {app.name for app in installed_provider_apps()} == set(INSTALLED_PROVIDERS)


def test_palm_provider_app_manifest() -> None:
    from palm.providers._registry import get_provider_app

    app = get_provider_app("palm")
    assert app is not None
    assert app.palm_layers
    assert app.actions == ("submit_flow", "submit_process", "invoke_resource", "fetch")
    assert "runtime_binding" in app.registry_hooks


def test_installed_storage_apps_register() -> None:
    assert set(INSTALLED_STORAGES) == {"memory", "postgres", "mongodb", "filesystem"}
    assert set(CORE_STORAGES) == {"memory", "filesystem"}
    assert set(OPTIONAL_STORAGES) == {"postgres", "mongodb"}
    for name in CORE_STORAGES:
        storage_registry.get(name)
    for name in OPTIONAL_STORAGES:
        StorageFactory.ensure_registered(name)
        storage_registry.get(name)


def test_installed_transform_apps_register() -> None:
    assert len(INSTALLED_TRANSFORMS) == 22
    assert "json_load" in INSTALLED_TRANSFORMS
    assert "csv_dump" in INSTALLED_TRANSFORMS
    for name in INSTALLED_TRANSFORMS:
        transform_registry.get(name)


def test_wizard_handler_exports() -> None:
    from palm.patterns.wizard import CommitRegistry
    from palm.patterns.wizard.bindings.compensation.handler import CommitRegistry as HandlerRegistry

    assert CommitRegistry is HandlerRegistry


def test_wizard_bridge_hooks_register() -> None:
    from palm.patterns._registry import (
        get_child_wait_hooks,
        get_cqrs_contributor,
        get_interactive_runtime,
        get_projection_factory,
        get_read_model_builder,
    )

    interactive = get_interactive_runtime("wizard")
    assert interactive is not None
    child_wait = get_child_wait_hooks("wizard")
    assert child_wait is not None
    read_model = get_read_model_builder("wizard")
    assert read_model is not None
    assert get_projection_factory("wizard") is not None
    assert get_cqrs_contributor("wizard") is not None


def test_pattern_app_autoload() -> None:
    from palm.common.patterns.app import PatternApp
    from palm.patterns._registry import get_pattern_app, installed_pattern_apps

    for name in INSTALLED_PATTERNS:
        app = get_pattern_app(name)
        assert app is not None
        assert isinstance(app, PatternApp)
        assert app.name == name
    assert {app.name for app in installed_pattern_apps()} == set(INSTALLED_PATTERNS)
