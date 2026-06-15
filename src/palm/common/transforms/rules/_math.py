"""Safe arithmetic expression evaluation for transform rules."""

from __future__ import annotations

import ast
import operator
from typing import Any

from palm.core.exceptions import TransformApplicationError

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_expression(expression: str, variables: dict[str, Any]) -> Any:
    """Evaluate a simple math expression with named variables."""
    if not expression or not expression.strip():
        raise TransformApplicationError("calculate requires a non-empty expression")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise TransformApplicationError(f"calculate invalid expression: {exc}") from exc
    return _eval_node(tree.body, variables)


def _eval_node(node: ast.AST, variables: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise TransformApplicationError(f"calculate unknown variable {node.id!r}")
        return variables[node.id]
    if isinstance(node, ast.UnaryOp):
        op = _UNARYOPS.get(type(node.op))
        if op is None:
            raise TransformApplicationError("calculate unsupported unary operator")
        return op(_eval_node(node.operand, variables))
    if isinstance(node, ast.BinOp):
        op = _BINOPS.get(type(node.op))
        if op is None:
            raise TransformApplicationError("calculate unsupported binary operator")
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        return op(left, right)
    raise TransformApplicationError(
        f"calculate unsupported expression node: {type(node).__name__}",
    )