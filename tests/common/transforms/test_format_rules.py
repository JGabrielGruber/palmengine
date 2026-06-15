"""Tests for serialization transform rules (JSON, CSV, TOML, XML)."""

from __future__ import annotations

import pytest

from palm.common.transforms import TransformExecutor, autoload
from palm.core import TransformApplicationError
from palm.core.transform.registry import transform_registry


@pytest.fixture
def executor() -> TransformExecutor:
    transform_registry.clear()
    autoload()
    return TransformExecutor()


def test_json_load_and_dump_roundtrip(executor: TransformExecutor) -> None:
    raw = '{"users": [{"name": "Ada", "active": true}]}'
    loaded = executor.apply("json_load", raw)
    assert loaded.value == {"users": [{"name": "Ada", "active": True}]}

    dumped = executor.apply("json_dump", loaded.value, indent=2, sort_keys=True)
    assert '"name": "Ada"' in dumped.value
    assert executor.apply("json_load", dumped.value).value == loaded.value


def test_json_load_invalid_reports_position(executor: TransformExecutor) -> None:
    with pytest.raises(TransformApplicationError, match="invalid JSON"):
        executor.apply("json_load", '{"broken":')


def test_csv_load_with_header(executor: TransformExecutor) -> None:
    text = "name,score\nAda,98\nGrace,95\n"
    result = executor.apply("csv_load", text)
    assert result.value == [{"name": "Ada", "score": "98"}, {"name": "Grace", "score": "95"}]


def test_csv_load_without_header_requires_fieldnames(executor: TransformExecutor) -> None:
    with pytest.raises(TransformApplicationError, match="fieldnames"):
        executor.apply("csv_load", "Ada,98\n", header=False)


def test_csv_dump_and_load_roundtrip(executor: TransformExecutor) -> None:
    rows = [{"name": "Ada", "score": "98"}, {"name": "Grace", "score": "95"}]
    dumped = executor.apply("csv_dump", rows, fieldnames=["name", "score"])
    assert dumped.value.splitlines()[0] == "name,score"
    loaded = executor.apply("csv_load", dumped.value)
    assert loaded.value == rows


def test_toml_load(executor: TransformExecutor) -> None:
    text = 'title = "demo"\n[owner]\nname = "Ada"\n'
    result = executor.apply("toml_load", text)
    assert result.value["title"] == "demo"
    assert result.value["owner"]["name"] == "Ada"


def test_xml_load_simple(executor: TransformExecutor) -> None:
    text = '<order id="1"><item sku="widget"/></order>'
    result = executor.apply("xml_load", text)
    assert "order" in result.value


def test_parquet_load_stub(executor: TransformExecutor) -> None:
    with pytest.raises(TransformApplicationError, match="not implemented"):
        executor.apply("parquet_load", b"PAR1")


def test_yaml_roundtrip(executor: TransformExecutor) -> None:
    pytest.importorskip("yaml")
    data = {"title": "demo", "tags": ["etl", "palm"]}
    dumped = executor.apply("yaml_dump", data, default_flow_style=False)
    loaded = executor.apply("yaml_load", dumped.value)
    assert loaded.value == data


def test_yaml_load_without_pyyaml(executor: TransformExecutor, monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "yaml":
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    with pytest.raises(TransformApplicationError, match="PyYAML"):
        executor.apply("yaml_load", "title: demo\n")