"""
Palm Orchestration Engine (🌴)

As of v0.3.0-dev this package has a clean core:
- `palm.core` contains only general-purpose engines (currently the Behavior Tree Engine).
- All previous wizard/orchestration implementation lives in `palm.cli.solid.legacy`
  as a deprecated reference implementation.

The public API will evolve as clean domain layers are rebuilt on top of the BT engine.
"""

__version__ = "0.3.1"

from palm.exceptions import PalmError

__all__ = [
    "__version__",
    "PalmError",
]
