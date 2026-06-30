"""Tests for BaseService."""

from __future__ import annotations

from dataclasses import dataclass

from palm.common.cqrs import CommandBus, QueryBus
from palm.common.cqrs.command import Command
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.services.base import BaseService
from palm.common.services.errors import ServiceValidationError
from palm.core.context.state_schema import DictStateSchema


@dataclass(frozen=True)
class _Cmd(Command):
    name: str


def test_base_service_rejects_invalid_command() -> None:
    bus = CommandBus()
    registry = CqrsSchemaRegistry()
    registry.register_command(
        _Cmd,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"name": {"type": "string", "minLength": 1}},
                "required": ["name"],
            }
        ),
    )
    svc = BaseService(commands=bus, queries=QueryBus(), schemas=registry)

    class _Handler:
        def handle(self, command: Command) -> str:
            return "ok"

    bus.register(_Cmd, _Handler())

    try:
        svc.dispatch(_Cmd(name=""))
        raise AssertionError("expected ServiceValidationError")
    except ServiceValidationError as exc:
        assert exc.result.ok is False
        assert exc.cqrs_type is _Cmd
