"""ETL pattern app manifest."""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


class EtlApp(PatternApp):
    name = "etl"
    label = "Extract-transform-load pipeline"


etl_app = EtlApp()

__all__ = ["EtlApp", "etl_app"]