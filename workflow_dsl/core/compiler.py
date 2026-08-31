"""编译器与执行引擎。

将校验通过的 ``WorkflowDef`` 编译为可执行的 DAG，并提供节点执行器（Executor）与
解释器（Interpreter）。解释器按拓扑顺序推进，依据分支条件选择下游路径，输出各节点
执行结果；运算符以 Mock 实现离线可跑，亦可替换为真实算子。
"""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from .ast import Condition, EdgeDef, WorkflowDef
from .validator import topo_order
from ..utils.logger import get_logger

logger = get_logger("dsl.compiler")

_OPS = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}



def _coerce(left: Any, right: Any):
    """数值尽量按数值比较，否则按字符串。"""
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left, right
    try:
        return float(left), float(right)
    except (TypeError, ValueError):
        return str(left), str(right)


def eval_condition(cond: Condition, output: dict) -> bool:
    """根据源节点输出评估分支条件。"""
    left = output.get(cond.field)
    if left is None:
        return False
    l, r = _coerce(left, cond.value)
    fn = _OPS.get(cond.op)
    if fn is None:
        return False
    return fn(l, r)


class NodeExecutor:
    """节点执行器：依据算子类型产出模拟输出。可被子类或注入覆盖。"""

    def __init__(self, overrides: Optional[Dict[str, dict]] = None):
        self.overrides = dict(overrides or {})

    def execute(self, node_id: str, op: str, args: dict) -> dict:
        if node_id in self.overrides:
            return dict(self.overrides[node_id])
        handler: Callable[[dict], dict] = getattr(self, f"_op_{op.lower()}", self._op_default)
        return handler(args)

    @staticmethod
    def _op_pass(args: dict) -> dict:
        return {"ok": True}

    @staticmethod
    def _op_http_get(args: dict) -> dict:
        return {"status": 200, "body": f"<mock response for {args.get('url', 'unknown')}>"}

    @staticmethod
    def _op_llm(args: dict) -> dict:
        return {"text": f"mock llm: {args.get('prompt', '')}", "score": 0.8}

    @staticmethod
    def _op_publish(args: dict) -> dict:
        return {"published": True, "channel": args.get("channel", "default")}

    @staticmethod
    def _op_human_review(args: dict) -> dict:
        return {"review": "pending"}

    @staticmethod
    def _op_default(args: dict) -> dict:
        return {"result": "ok", "args": args}


@dataclass
class ExecutableWorkflow:
    """编译后的可执行工作流。"""

    name: str
    def_: WorkflowDef
    topo: list = field(default_factory=list)

    def run(self, executor: NodeExecutor) -> dict:
        """执行工作流，返回 node_id -> 输出 的上下文。"""
        ctx: dict = {}
        current = self.def_.start
        path: list = []
        guard = set()
        while current is not None:
            if current in guard:
                logger.warning("检测到环，终止（应已被校验拦截）")
                break
            guard.add(current)
            node = self.def_.nodes[current]
            out = executor.execute(current, node.op, node.args)
            ctx[current] = out
            path.append(current)
            logger.info("exec node=%s op=%s", current, node.op)

            # 选择下游边：优先匹配的条件分支，否则普通边
            chosen: Optional[str] = None
            fallback: Optional[str] = None
            for e in self.def_.out_edges(current):
                if e.condition is not None:
                    if eval_condition(e.condition, out):
                        chosen = e.dst
                        break
                else:
                    if fallback is None:
                        fallback = e.dst
            nxt = chosen if chosen is not None else fallback
            if nxt is None:
                break
            if nxt == self.def_.end:
                # 仍执行 end 节点后退出
                current = nxt
                continue
            current = nxt

        logger.info("path=%s", " -> ".join(path))
        return ctx


def compile(wf: WorkflowDef) -> ExecutableWorkflow:
    """编译 WorkflowDef 为可执行工作流。"""
    return ExecutableWorkflow(name=wf.name, def_=wf, topo=topo_order(wf))
