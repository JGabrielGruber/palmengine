"""Back-compat shim — the pattern extension registry moved to
:mod:`palm.common.patterns._registry` in 0.47.5 (T3 de-cycling), so that ``common`` reads
it as a *sibling* instead of reaching *up* into ``patterns``. Import from the new home.
This shim keeps existing producers/consumers working during the incremental migration and
is retired in the final 0.47.5 step.
"""

from __future__ import annotations

from palm.common.patterns._registry import *  # noqa: F403
