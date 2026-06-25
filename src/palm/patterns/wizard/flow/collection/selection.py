"""
Collection item selection — compact previews and flexible lookup for edit/remove.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from palm.patterns.wizard.flow.collection.config import CollectionFieldConfig

CollectionSelectAction = Literal["edit", "remove"]

PREVIEW_MAX_LENGTH = 40
CANCEL_INPUTS = frozenset({"cancel", "back", "c", "quit"})


def default_label_field(
    item_fields: tuple[CollectionFieldConfig, ...],
    explicit: str | None = None,
) -> str:
    """Resolve the field used to label items in menus and selection prompts."""
    if explicit:
        return explicit
    for field in item_fields:
        if field.required and field.field_type == "text":
            return field.slug
    for preferred in ("title", "name"):
        if any(field.slug == preferred for field in item_fields):
            return preferred
    if item_fields:
        return item_fields[0].slug
    return "title"


def item_label_value(item: dict[str, Any], label_field: str, *, index: int) -> str:
    """Return the display label for one collection item."""
    raw = item.get(label_field)
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    for fallback in ("title", "name"):
        if fallback != label_field:
            value = item.get(fallback)
            if value is not None and str(value).strip():
                return str(value).strip()
    return f"Item {index + 1}"


def truncate_preview(text: str, *, max_length: int = PREVIEW_MAX_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1]}…"


def format_item_preview(
    item: dict[str, Any],
    *,
    index: int,
    label_field: str,
    item_fields: tuple[CollectionFieldConfig, ...] | None = None,
) -> str:
    """Compact one-line preview for item selection lists."""
    label = truncate_preview(item_label_value(item, label_field, index=index))
    suffixes: list[str] = []
    if item_fields:
        for field in item_fields:
            if field.slug == label_field:
                continue
            value = item.get(field.slug)
            if value is None or value == "":
                continue
            if field.field_type == "choice":
                suffixes.append(f"[{value}]")
            elif "date" in field.slug:
                suffixes.append(f"due {value}")
    if suffixes:
        return f"{label} {' '.join(suffixes)}"
    return label


def format_numbered_item_list(
    items: list[dict[str, Any]],
    *,
    label_field: str,
    item_fields: tuple[CollectionFieldConfig, ...] | None = None,
) -> str:
    lines = [
        f"{index}. {format_item_preview(item, index=index - 1, label_field=label_field, item_fields=item_fields)}"
        for index, item in enumerate(items, start=1)
    ]
    return "\n".join(lines)


def item_selection_prompt(action: CollectionSelectAction) -> str:
    verb = "edit" if action == "edit" else "remove"
    return f"Which item to {verb}? " f"(enter number, partial {verb} label, or 'cancel')"


def item_selection_error(
    raw: Any,
    items: list[dict[str, Any]],
    *,
    label_field: str,
    action: CollectionSelectAction,
    item_fields: tuple[CollectionFieldConfig, ...] | None = None,
) -> str:
    verb = "edit" if action == "edit" else "remove"
    listing = format_numbered_item_list(
        items,
        label_field=label_field,
        item_fields=item_fields,
    )
    return (
        f"Could not find an item to {verb} from {raw!r}. "
        f"Enter a number (1-{len(items)}), a matching label, or 'cancel':\n"
        f"{listing}"
    )


def is_cancel_input(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in CANCEL_INPUTS
    return False


def resolve_item_index(
    value: Any,
    items: list[dict[str, Any]],
    *,
    label_field: str,
) -> int | None:
    """Resolve user input to a zero-based item index."""
    if not items:
        return None

    labels = [item_label_value(item, label_field, index=index) for index, item in enumerate(items)]

    if isinstance(value, int) and not isinstance(value, bool):
        if 1 <= value <= len(items):
            return value - 1
        return None

    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    if text.isdigit():
        index = int(text)
        if 1 <= index <= len(items):
            return index - 1
        return None

    if text in labels:
        return labels.index(text)

    lowered = text.lower()
    case_insensitive = [index for index, label in enumerate(labels) if label.lower() == lowered]
    if len(case_insensitive) == 1:
        return case_insensitive[0]

    prefix_matches = [
        index for index, label in enumerate(labels) if label.lower().startswith(lowered)
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    substring_matches = [index for index, label in enumerate(labels) if lowered in label.lower()]
    if len(substring_matches) == 1:
        return substring_matches[0]

    return None
