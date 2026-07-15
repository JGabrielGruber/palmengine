"""Back-compat shim — the provider extension registry moved to
:mod:`palm.common.providers._registry` in 0.47.5 (T3 de-cycling). Import from the new home.
Retired in the final 0.47.5 step.
"""

from __future__ import annotations

from palm.common.providers._registry import *  # noqa: F403
