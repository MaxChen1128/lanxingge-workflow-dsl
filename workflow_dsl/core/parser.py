"""语法分析器（Parser）。

采用递归下降（recursive descent）将记号流解析为 ``WorkflowDef`` AST。语法：

    workflow <name> {
        start = <node_id>
        end   = <node_id>
        node  <id> = <OP>(key="val", key2=3.0, ...)
        edge  <src> -> <dst>
        branch <src> -> <dst> when <field> <op> <value>
    }
"""

from __future__ import annotations

from typing import List

from .ast import Condition, EdgeDef, NodeDef, WorkflowDef
from .lexer import LexError, Token, tokenize


class ParseError(Exception):
    """语法错误。"""


class _Cursor:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def next(self) -> Token:
        t = self.tokens[self.i]
        self.i += 1
        return t

    def expect(self, *types: str) -> Token:
        t = self.tokens[self.i]
        if t.type not in types:
            raise ParseError(f"期望 {types}，实际 {t.type}({t.value!r}) 位置 {t.pos}")
        self.i += 1
        return t

    def at_end(self) -> bool:
        return self.i >= len(self.tokens)


def _parse_args(cur: _Cursor) -> dict:
    """解析 (key=value, key2="str", ...) 参数表。"""
    args: dict = {}
    cur.expect("LPAREN")
    if cur.peek().type == "RPAREN":
        cur.next()
        return args
    while True:
        key = cur.expect("NAME").value
        cur.expect("EQ")
        vt = cur.peek().type
        if vt == "STRING":
            val = cur.next().value[1:-1]
        elif vt == "NUMBER":
            val = float(cur.next().value)
            if val.is_integer():
                val = int(val)
        elif vt == "NAME":
            val = cur.next().value
        else:
            raise ParseError(f"参数值非法：{cur.peek().value!r}")
        args[key] = val
        if cur.peek().type == "COMMA":
            cur.next()
            continue
        break
    cur.expect("RPAREN")
    return args


def _parse_condition(cur: _Cursor) -> Condition:
    """解析 when <field> <op> <value>。"""
    cur.expect("KEYWORD")  # 'when'
    field = cur.expect("NAME").value
    op_tok = cur.peek()
    if op_tok.type == "OPCMP":
        op = cur.next().value
    elif op_tok.type == "OP":
        op = cur.next().value
    else:
        raise ParseError(f"条件运算符非法：{op_tok.value!r}")
    vt = cur.peek().type
    if vt == "STRING":
        value = cur.next().value[1:-1]
    elif vt == "NUMBER":
        value = float(cur.next().value)
        if value.is_integer():
            value = int(value)
    elif vt == "NAME":
        value = cur.next().value
    else:
        raise ParseError(f"条件值非法：{cur.peek().value!r}")
    return Condition(field=field, op=op, value=value)


def parse(text: str) -> WorkflowDef:
    """解析 DSL 文本为 WorkflowDef。"""
    try:
        tokens = tokenize(text)
    except LexError as e:
        raise ParseError(str(e)) from e
    cur = _Cursor(tokens)

    cur.expect("KEYWORD")  # 'workflow'
    name = cur.expect("NAME", "STRING").value
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    cur.expect("LBRACE")

    wf = WorkflowDef(name=name)
    while not cur.at_end() and cur.peek().type != "RBRACE":
        kw = cur.expect("KEYWORD").value
        if kw == "start":
            cur.expect("EQ")
            wf.start = cur.expect("NAME").value
        elif kw == "end":
            cur.expect("EQ")
            wf.end = cur.expect("NAME").value
        elif kw == "node":
            nid = cur.expect("NAME").value
            cur.expect("EQ")
            op = cur.expect("NAME").value
            args = _parse_args(cur)
            wf.nodes[nid] = NodeDef(id=nid, op=op, args=args)
        elif kw == "edge":
            src = cur.expect("NAME").value
            cur.expect("ARROW")
            dst = cur.expect("NAME").value
            wf.edges.append(EdgeDef(src=src, dst=dst))
        elif kw == "branch":
            src = cur.expect("NAME").value
            cur.expect("ARROW")
            dst = cur.expect("NAME").value
            cond = _parse_condition(cur)
            wf.edges.append(EdgeDef(src=src, dst=dst, condition=cond))
        else:
            raise ParseError(f"未知语句：{kw}")
    cur.expect("RBRACE")
    return wf
