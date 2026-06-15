"""Parse CSV text into a list of row mappings."""

from __future__ import annotations

import csv
import io
from typing import Any, ClassVar

from palm.common.transforms.rules._formats import ensure_text
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class CsvLoadRule(BaseTransformRule):
    """
    Parse CSV text into a list of dict rows.

    Options:

    - ``encoding`` — for bytes input (default ``utf-8``)
    - ``delimiter`` — field separator (default ``,``)
    - ``header`` — first row is header (default ``True``)
    - ``fieldnames`` — explicit column names when ``header=False``
    - ``skip_initial_space`` — strip spaces after delimiter (default ``False``)
    """

    name: ClassVar[str] = "csv_load"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> CsvLoadRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        encoding = str(options.get("encoding", "utf-8"))
        delimiter = str(options.get("delimiter", ","))
        has_header = bool(options.get("header", True))
        fieldnames_raw = options.get("fieldnames")
        fieldnames = (
            [str(item) for item in fieldnames_raw]
            if isinstance(fieldnames_raw, list)
            else None
        )
        skip_initial_space = bool(options.get("skip_initial_space", False))

        text = ensure_text(context.value, encoding=encoding, rule_name=self.rule_name)
        if not text.strip():
            return context.advance(self.rule_name, [], meta={"rows": 0})

        buffer = io.StringIO(text, newline="")
        if has_header:
            reader = csv.DictReader(
                buffer,
                delimiter=delimiter,
                skipinitialspace=skip_initial_space,
            )
            rows = [dict(row) for row in reader]
        else:
            if not fieldnames:
                raise TransformApplicationError(
                    f"{self.rule_name} requires fieldnames= when header=False",
                )
            reader = csv.DictReader(
                buffer,
                fieldnames=fieldnames,
                delimiter=delimiter,
                skipinitialspace=skip_initial_space,
            )
            rows = [dict(row) for row in reader]

        return context.advance(
            self.rule_name,
            rows,
            meta={"rows": len(rows), "header": has_header},
        )