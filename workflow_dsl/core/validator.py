"""静态校验器。

对解析后的 ``WorkflowDef`` 做静态检查：节点/边引用完整性、环检测（拓扑排序）、
起止可达性。校验通过后方可编译执行。
"""

from __future__ import annotations

from .ast import WorkflowDef


class ValidationError(Exception):
    """校验未通过。"""


def validate(wf: WorkflowDef) -> None:
    """校验工作流；通过返回 None，失败抛出 ValidationError。"""
    if not wf.nodes:
        raise ValidationError("工作流没有任何节点")

    # 1) 边引用的节点必须已定义
    for e in wf.edges:
        if e.src not in wf.nodes:
            raise ValidationError(f"边起点未定义：{e.src}")
        if e.dst not in wf.nodes:
            raise ValidationError(f"边终点未定义：{e.dst}")

    # 2) 推导 start / end（若未显式声明）
    if wf.start is None:
        roots = [n for n in wf.nodes if wf.in_degree(n) == 0]
        if len(roots) != 1:
            raise ValidationError("未声明 start 且入度为 0 的起点不唯一，请显式声明 start")
        wf.start = roots[0]
    elif wf.start not in wf.nodes:
        raise ValidationError(f"start 指向未定义节点：{wf.start}")

    if wf.end is None:
        leaves = [n for n in wf.nodes if not wf.out_edges(n)]
        if len(leaves) != 1:
            raise ValidationError("未声明 end 且出度为 0 的终点不唯一，请显式声明 end")
        wf.end = leaves[0]
    elif wf.end not in wf.nodes:
        raise ValidationError(f"end 指向未定义节点：{wf.end}")

    # 3) 环检测：拓扑排序
    indeg = {n: wf.in_degree(n) for n in wf.nodes}
    queue = [n for n, d in indeg.items() if d == 0]
    visited = 0
    while queue:
        n = queue.pop()
        visited += 1
        for e in wf.out_edges(n):
            indeg[e.dst] -= 1
            if indeg[e.dst] == 0:
                queue.append(e.dst)
    if visited != len(wf.nodes):
        raise ValidationError("工作流存在环（cycle），无法拓扑排序")

    # 4) 可达性：start 能否到达 end
    seen = set()
    stack = [wf.start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for e in wf.out_edges(n):
            stack.append(e.dst)
    if wf.end not in seen:
        raise ValidationError("end 不可从 start 到达")


def topo_order(wf: WorkflowDef) -> list:
    """返回拓扑序（供编译器参考）。"""
    indeg = {n: wf.in_degree(n) for n in wf.nodes}
    order = []
    queue = [n for n, d in indeg.items() if d == 0]
    while queue:
        n = queue.pop(0)
        order.append(n)
        for e in wf.out_edges(n):
            indeg[e.dst] -= 1
            if indeg[e.dst] == 0:
                queue.append(e.dst)
    return order
