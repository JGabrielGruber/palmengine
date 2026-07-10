"""0.35.1 — parse metadata.analytics exposure."""

from __future__ import annotations

import pytest

from palm.services.analytics.exposure import (
    AnalyticsExposure,
    is_analytics_published,
    parse_analytics_exposure,
)


def test_missing_metadata_unpublished() -> None:
    exp = parse_analytics_exposure(None)
    assert exp == AnalyticsExposure()
    assert exp.published is False
    assert is_analytics_published(None) is False


def test_missing_analytics_block() -> None:
    exp = parse_analytics_exposure({"description": "ops only"})
    assert exp.published is False
    assert exp.kind == "fact"


def test_full_published_fact() -> None:
    exp = parse_analytics_exposure(
        {
            "analytics": {
                "published": True,
                "kind": "fact",
                "derived_from": [],
                "default_profile": "table",
                "row_path": "items",
                "refresh": {"pipeline_flow_id": "materialize-sales"},
            }
        }
    )
    assert exp.published is True
    assert exp.kind == "fact"
    assert exp.row_path == "items"
    assert exp.default_profile == "table"
    assert exp.refresh["pipeline_flow_id"] == "materialize-sales"
    assert is_analytics_published({"analytics": {"published": True}}) is True


def test_view_with_lineage() -> None:
    exp = parse_analytics_exposure(
        {
            "analytics": {
                "published": True,
                "kind": "view",
                "derived_from": ["sales-facts-daily", "dim-region"],
                "default_profile": "series",
            }
        }
    )
    assert exp.kind == "view"
    assert exp.derived_from == ("sales-facts-daily", "dim-region")
    assert exp.default_profile == "series"


def test_unknown_keys_ignored_and_recorded() -> None:
    exp = parse_analytics_exposure(
        {"analytics": {"published": True, "extra_future": 1, "publshed": True}}
    )
    assert exp.published is True
    assert "extra_future" in exp.unknown_keys
    assert "publshed" in exp.unknown_keys


def test_invalid_types_lenient() -> None:
    exp = parse_analytics_exposure(
        {
            "analytics": {
                "published": "yes",
                "kind": "cube",
                "derived_from": "not-a-list",
                "default_profile": "heatmap",
                "row_path": 12,
            }
        }
    )
    assert exp.published is False
    assert exp.kind == "fact"
    assert exp.derived_from == ()
    assert exp.default_profile == "table"
    assert exp.row_path is None


def test_strict_raises_on_bad_types() -> None:
    with pytest.raises(ValueError, match="published"):
        parse_analytics_exposure({"analytics": {"published": "yes"}}, strict=True)
    with pytest.raises(ValueError, match="kind"):
        parse_analytics_exposure({"analytics": {"kind": "cube"}}, strict=True)
    with pytest.raises(ValueError, match="object"):
        parse_analytics_exposure({"analytics": "nope"}, strict=True)


def test_non_dict_analytics_lenient() -> None:
    assert parse_analytics_exposure({"analytics": []}).published is False


def test_to_dict_omits_empties() -> None:
    exp = parse_analytics_exposure({"analytics": {"published": True, "kind": "view"}})
    d = exp.to_dict()
    assert d["published"] is True
    assert d["kind"] == "view"
    assert "row_path" not in d
    assert "refresh" not in d


def test_parse_virtual_view_source_and_transform() -> None:
    exp = parse_analytics_exposure(
        {
            "analytics": {
                "published": True,
                "kind": "view",
                "source": "palm-todos",
                "materialize": False,
                "transform": {"op": "count_by", "field": "priority"},
            }
        }
    )
    assert exp.published is True
    assert exp.source == "palm-todos"
    assert exp.materialize is False
    assert exp.is_virtual is True
    assert exp.transform == {"op": "count_by", "field": "priority"}


def test_source_without_materialize_defaults_virtual() -> None:
    exp = parse_analytics_exposure(
        {
            "analytics": {
                "published": True,
                "source": "palm-todos",
                "transform": {"op": "count_by", "field": "priority"},
            }
        }
    )
    assert exp.materialize is False
    assert exp.is_virtual is True


def test_materialize_defaults_true_without_source() -> None:
    exp = parse_analytics_exposure(
        {"analytics": {"published": True, "kind": "view", "derived_from": ["palm-todos"]}}
    )
    assert exp.source is None
    assert exp.materialize is True
    assert exp.is_virtual is False
