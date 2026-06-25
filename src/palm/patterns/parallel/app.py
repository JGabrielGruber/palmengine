"""Parallel pattern app manifest."""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


class ParallelApp(PatternApp):
    name = "parallel"
    label = "Parallel branch execution"


parallel_app = ParallelApp()

__all__ = ["ParallelApp", "parallel_app"]