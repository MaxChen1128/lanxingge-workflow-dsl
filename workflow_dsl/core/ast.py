"""工作流 DSL 的抽象语法树（AST）定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class NodeDef:
    """工作流节点定义：唯一 ID、算子类型、算子参数。"""

    id: str
    op: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class Condition:
    """分支条件：对源节点输出字段做比较。"""

    field: str
    op: str  # 支持 > < >= <= == !=
    value: Any


@dataclass
class EdgeDef:
    """工作流边：从 src 到 dst；condition 非空时为条件（分支）边。"""

    src: str
    dst: str
    condition: Optional[Condition] = None


@dataclass
class WorkflowDef:
    """解析后的工作流定义（AST 根）。"""

    name: str
    nodes: dict[str, NodeDef] = field(default_factory=dict)
    edges: list[EdgeDef] = field(default_factory=list)
    start: Optional[str] = None
    end: Optional[str] = None

    def out_edges(self, node_id: str) -> list[EdgeDef]:
        return [e for e in self.edges if e.src == node_id]

    def in_degree(self, node_id: str) -> int:
        return sum(1 for e in self.edges if e.dst == node_id)
