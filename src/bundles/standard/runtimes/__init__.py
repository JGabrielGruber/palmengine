"""
Execution runtimes — surfaces that host Palm engines.

Use ``palm.runtimes.cli:main`` as the CLI entry point. Library code should
import concrete runtimes from their subpackages (``embedded``, ``daemon``,
``server``). This package root is not a surface barrel: loading one surface
subpackage must not pull sibling surfaces (``server``, ``daemon``, ``mcp``).

System instance and ports live in ``palm.system``. Shared server transport
lives in the exposed kit :mod:`palm.kits.server`.
"""
