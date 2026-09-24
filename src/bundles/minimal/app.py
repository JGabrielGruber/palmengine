"""Minimal application.

The :class:`~bundles.minimal.definition.MinimalDefinition` names the storage
plugin and the other modules this app installs. System start selects that
backend and calls ``plugin_install``. It does not name plugin packages.
"""

from __future__ import annotations

from bundles.minimal.bootstrap import install_modules
from bundles.minimal.definition import DEFAULT_DEFINITION, MinimalDefinition
from bundles.minimal.runtime import MinimalRuntime


class MinimalApp:
    """Start and stop one constrained system instance."""

    def __init__(
        self,
        definition: MinimalDefinition | None = None,
        *,
        modules: tuple[str, ...] | None = None,
    ) -> None:
        chosen = definition or DEFAULT_DEFINITION
        if modules is not None:
            chosen = MinimalDefinition(
                storage_backend=chosen.storage_backend,
                modules=tuple(modules),
                structure_definition_id=chosen.structure_definition_id,
            )
        self.definition = chosen
        self._runtime: MinimalRuntime | None = None

    @property
    def runtime(self) -> MinimalRuntime:
        if self._runtime is None or not self._runtime.is_started:
            raise RuntimeError("MinimalApp is not started")
        return self._runtime

    def start(self) -> MinimalRuntime:
        """Walk the system schedule. Return the running instance."""
        if self._runtime is not None and self._runtime.is_started:
            return self._runtime
        runtime = self._runtime or MinimalRuntime()
        definition = self.definition

        def _install() -> None:
            install_modules(definition.modules)

        runtime.start(
            storage_backend=definition.storage_backend,
            structure_definition_id=definition.structure_definition_id,
            plugin_install=_install,
        )
        self._runtime = runtime
        return runtime

    def stop(self) -> None:
        """Stop the system instance when it is running."""
        if self._runtime is not None and self._runtime.is_started:
            self._runtime.stop()

    def __enter__(self) -> MinimalApp:
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.stop()
