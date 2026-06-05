"""
Concrete behavior patterns — wizard, DAG, and ETL.

Import submodules to register patterns with ``pattern_registry``.
"""

from palm.patterns import dag, etl, wizard

__all__ = ["wizard", "dag", "etl"]
