"""
Backward-compatibility shim — wizard options moved to ``palm.patterns.wizard.options``.
"""

from __future__ import annotations

from palm.patterns.wizard.options import parse_wizard_flow_options, wizard_metadata_from_flow

__all__ = ["parse_wizard_flow_options", "wizard_metadata_from_flow"]