"""Serialize row mappings to CSV text."""

from __future__ import annotations

import csv
import io
from typing import Any, ClassVar

from palm.common.transforms.rules._helpers import require_list
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class CsvDumpRule(BaseTransformRule):
    """
    Serialize a list of mappings to CSV text.

    Options:

    - ``delimiter`` — field separator (default ``,``)
    - ``header`` — write header row from keys (default ``True``)
    - ``fieldnames`` — explicit column order; inferred from first row when omitted
    - ``lineterminator`` — row terminator (default ``\\n``)
    - ``extrasaction`` — ``raise`` (default) or ``ignore`` for unknown keys
    """

    name: ClassVar[str] = "csv_dump"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    @classmethod
    def from_options(cls, **options: Any) -> CsvDumpRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        rows = require_list(context.value, self.rule_name)
        if rows and not all(isinstance(row, dict) for row in rows):
            raise TransformApplicationError(
                f"{self.rule_name} requires a list of mappings",
            )

        delimiter = str(options.get("delimiter", ","))
        write_header = bool(options.get("header", True))
        lineterminator = str(options.get("lineterminator", "\n"))
        extrasaction = str(options.get("extrasaction", "raise"))

        fieldnames_raw = options.get("fieldnames")
        fieldnames: list[str] | None = None
        if isinstance(fieldnames_raw, list):
            fieldnames = [str(item) for item in fieldnames_raw]
        elif rows:
            keys: list[str] = []
            seen: set[str] = set()
            for row in rows:
                for key in row:
                    key_str = str(key)
                    if key_str not in seen:
                        seen.add(key_str)
                        keys.append(key_str)
            fieldnames = keys

        buffer = io.StringIO(newline="")
        if not fieldnames:
            return context.advance(self.rule_name, "", meta={"rows": 0})

        writer = csv.DictWriter(
            buffer,
            fieldnames=fieldnames,
            delimiter=delimiter,
            lineterminator=lineterminator,
            extrasaction=extrasaction,
        )
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

        return context.advance(
            self.rule_name,
            buffer.getvalue(),
            meta={"rows": len(rows), "columns": len(fieldnames)},
        )