"""Parse simple XML text into nested mappings."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, ClassVar

from palm.common.transforms.rules._formats import ensure_text
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


def _element_to_value(
    element: ET.Element,
    *,
    attr_key: str,
    text_key: str,
) -> Any:
    children = list(element)
    attrs = dict(element.attrib) if element.attrib else {}
    text = (element.text or "").strip()

    if not children and not attrs:
        return text

    payload: dict[str, Any] = {}
    if attrs:
        payload[attr_key] = attrs
    if text:
        payload[text_key] = text

    child_counts: dict[str, int] = {}
    for child in children:
        tag = child.tag
        child_counts[tag] = child_counts.get(tag, 0) + 1

    for child in children:
        tag = child.tag
        converted = _element_to_value(child, attr_key=attr_key, text_key=text_key)
        if child_counts[tag] > 1:
            payload.setdefault(tag, [])
            if isinstance(payload[tag], list):
                payload[tag].append(converted)
        else:
            payload[tag] = converted

    return payload if payload else text


class XmlLoadRule(BaseTransformRule):
    """
    Parse XML into a nested mapping (stdlib ElementTree).

    Options: ``attr_key`` (default ``@attrs``), ``text_key`` (default ``#text``).
    """

    name: ClassVar[str] = "xml_load"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> XmlLoadRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        encoding = str(options.get("encoding", "utf-8"))
        attr_key = str(options.get("attr_key", "@attrs"))
        text_key = str(options.get("text_key", "#text"))
        text = ensure_text(context.value, encoding=encoding, rule_name=self.rule_name)
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise TransformApplicationError(
                f"{self.rule_name} invalid XML: {exc}",
            ) from exc
        tag = root.tag
        body = _element_to_value(root, attr_key=attr_key, text_key=text_key)
        result = {tag: body}
        return context.advance(
            self.rule_name,
            result,
            meta={"root": tag},
        )
