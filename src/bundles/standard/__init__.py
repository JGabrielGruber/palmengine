"""
Palm Engine — lightweight orchestration for multi-step transactional workflows.

The ``engine`` package is organized in layers and depends on ``palm`` package:

- ``engine.app`` — :class:`~engine.app.host.ApplicationHost` (recommended), :class:`~engine.app.PalmKernel` (infra)
- ``engine.patterns`` / ``engine.providers`` / ``engine.storages`` — extensible plugin apps (truthful install sets)
- ``engine.runtimes`` — CLI, embedded, server, and daemon surfaces
"""