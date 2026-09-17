"""Named session-metadata keys for walk writes (0.69.1).

Stamp / replace ``guidance_instance_id`` through the session plane.
Floor allow is degenerate: owner session + attached instance.
The interface type stays unnamed until José locks it.
Geometry (attach, focus, owner check) is not a walk-write verb.
"""

from __future__ import annotations

GUIDANCE_INSTANCE_ID = "guidance_instance_id"

__all__ = ["GUIDANCE_INSTANCE_ID"]
