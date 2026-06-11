"""Safe calculate transform — simple expressions over mapping fields."""

from __future__ import annotations

import ast
import operator
from typing import Any, ClassVar

from palm.core.transform.base_transform import BaseTransform
from palm.core.transform.context import TransformContext
from palm.core.transform.exceptions import TransformApplicationError

_OPERATORS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY: dict[type[ast.unaryop], Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculateTransform(BaseTransform):
    """
    Evaluate a safe arithmetic expression and store the result on a mapping.

    Expression variables refer to keys on the input mapping. Example::

        {"quantity": 2, "price": 10}
        expression="quantity * price", field="total"  →  {"total": 20, ...}
    """

    name: ClassVar[str] = "calculate"

    def __init__(self, *, expression: str, field: str) -> None:
        super().__init__()
        self._expression = expression
        self._field = field

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, dict):
            raise TransformApplicationError(
                f"{self.transform_name} requires a mapping, got {type(value).__name__}"
            )
        variables = {key: _coerce_number(val) for key, val in value.items()}
        result = _safe_evaluate(self._expression, variables)
        out = dict(value)
        out[self._field] = result
        return context.advance(
            self.transform_name,
            out,
            meta={"expression": self._expression, "field": self._field},
        )


def _coerce_number(value: Any) -> float | int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError as exc:
            raise TransformApplicationError(f"Cannot coerce {value!r} to number") from exc
    raise TransformApplicationError(f"Unsupported numeric operand: {type(value).__name__}")


def _safe_evaluate(expression: str, variables: dict[str, float | int]) -> float | int:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise TransformApplicationError(f"Invalid expression: {expression!r}") from exc
    return _EvalVisitor(variables).visit(tree.body)


class _EvalVisitor(ast.NodeVisitor):
    def __init__(self, variables: dict[str, float | int]) -> None:
        self._variables = variables

    def visit_BinOp(self, node: ast.BinOp) -> float | int:
        op_type = type(node.op)
        operator_fn = _OPERATORS.get(op_type)
        if operator_fn is None:
            raise TransformApplicationError(f"Unsupported operator: {op_type.__name__}")
        left = self.visit(node.left)
        right = self.visit(node.right)
        return operator_fn(left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float | int:
        operator_fn = _UNARY.get(type(node.op))
        if operator_fn is None:
            raise TransformApplicationError(f"Unsupported unary operator: {type(node.op).__name__}")
        return operator_fn(self.visit(node.operand))

    def visit_Name(self, node: ast.Name) -> float | int:
        if node.id not in self._variables:
            raise TransformApplicationError(f"Unknown variable in expression: {node.id!r}")
        return self._variables[node.id]

    def visit_Constant(self, node: ast.Constant) -> float | int:
        if isinstance(node.value, bool):
            return int(node.value)
        if isinstance(node.value, (int, float)):
            return node.value
        raise TransformApplicationError(f"Unsupported constant: {node.value!r}")

    def generic_visit(self, node: ast.AST) -> float | int:
        raise TransformApplicationError(f"Unsupported expression node: {type(node).__name__}")