"""Parquet loader placeholder — extension point for future binary format support."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class ParquetLoadRule(BaseTransformRule):
    """
    Placeholder for Parquet ingestion.

    Parquet support requires an optional engine dependency (e.g. pyarrow/pandas).
    Register a custom rule or extend this module when binary columnar support lands.
    """

    name: ClassVar[str] = "parquet_load"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> ParquetLoadRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        raise TransformApplicationError(
            f"{self.rule_name} is not implemented yet — use json_load/csv_load or "
            "register a custom Parquet rule with pyarrow",
        )