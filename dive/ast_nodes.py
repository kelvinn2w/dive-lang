"""Dive dilinin AST (Abstract Syntax Tree) qovşaqları."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Node:
    line: int = 0


# ---- ifadələr (expressions) ----


@dataclass
class NumberLit(Node):
    value: object = 0


@dataclass
class StringLit(Node):
    value: str = ""


@dataclass
class BoolLit(Node):
    value: bool = False


@dataclass
class NoneLit(Node):
    pass


@dataclass
class Identifier(Node):
    name: str = ""


@dataclass
class ListLit(Node):
    elements: List[Node] = field(default_factory=list)


@dataclass
class DictLit(Node):
    pairs: List[Tuple[Node, Node]] = field(default_factory=list)


@dataclass
class BinaryOp(Node):
    op: str = ""
    left: Optional[Node] = None
    right: Optional[Node] = None


@dataclass
class UnaryOp(Node):
    op: str = ""
    operand: Optional[Node] = None


@dataclass
class LogicalOp(Node):
    op: str = ""  # "and" | "or"
    left: Optional[Node] = None
    right: Optional[Node] = None


@dataclass
class Compare(Node):
    """Birdən çox müqayisə: a < b < c"""

    left: Optional[Node] = None
    ops: List[str] = field(default_factory=list)
    comparators: List[Node] = field(default_factory=list)


@dataclass
class Call(Node):
    func: Optional[Node] = None
    args: List[Node] = field(default_factory=list)
    kwargs: List[Tuple[str, Node]] = field(default_factory=list)


@dataclass
class Attribute(Node):
    obj: Optional[Node] = None
    name: str = ""


@dataclass
class Subscript(Node):
    obj: Optional[Node] = None
    index: Optional[Node] = None


@dataclass
class Slice(Node):
    start: Optional[Node] = None
    stop: Optional[Node] = None
    step: Optional[Node] = None


@dataclass
class Lambda(Node):
    params: List[str] = field(default_factory=list)
    body: Optional[Node] = None


# ---- ifadələr (statements) ----


@dataclass
class Program(Node):
    body: List[Node] = field(default_factory=list)


@dataclass
class ExpressionStmt(Node):
    expr: Optional[Node] = None


@dataclass
class Assign(Node):
    targets: List[Node] = field(default_factory=list)
    value: Optional[Node] = None


@dataclass
class AugAssign(Node):
    target: Optional[Node] = None
    op: str = ""  # "+=" və s.
    value: Optional[Node] = None


@dataclass
class If(Node):
    condition: Optional[Node] = None
    then_body: List[Node] = field(default_factory=list)
    elif_clauses: List[Tuple[Node, List[Node]]] = field(default_factory=list)
    else_body: List[Node] = field(default_factory=list)


@dataclass
class While(Node):
    condition: Optional[Node] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class For(Node):
    var: str = ""
    iterable: Optional[Node] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class Param(Node):
    name: str = ""
    default: Optional[Node] = None


@dataclass
class FunctionDef(Node):
    name: str = ""
    params: List[Param] = field(default_factory=list)
    body: List[Node] = field(default_factory=list)


@dataclass
class ClassDef(Node):
    name: str = ""
    bases: List[Node] = field(default_factory=list)
    body: List[Node] = field(default_factory=list)


@dataclass
class Return(Node):
    value: Optional[Node] = None


@dataclass
class Break(Node):
    pass


@dataclass
class Continue(Node):
    pass


@dataclass
class Pass(Node):
    pass


@dataclass
class Throw(Node):
    value: Optional[Node] = None


@dataclass
class CatchClause(Node):
    var: Optional[str] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class Try(Node):
    body: List[Node] = field(default_factory=list)
    catches: List[CatchClause] = field(default_factory=list)
    finally_body: List[Node] = field(default_factory=list)


@dataclass
class Import(Node):
    target: str = ""  # ya path "fayl.dive", ya da "math"
    alias: Optional[str] = None
    is_path: bool = False  # `import "..."` formatı
