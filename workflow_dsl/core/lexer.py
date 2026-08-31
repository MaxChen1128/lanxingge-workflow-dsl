"""词法分析器（Lexer）。

将 DSL 文本切分为记号（Token）流。支持的记号类型：关键字、标识符、字符串、数字、
运算符（-> >= <= == != > < = ）、分隔符（(){},）。忽略空白与注释（# 至行尾）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, List


@dataclass
class Token:
    type: str
    value: str
    pos: int


# 记号正则表（按顺序匹配）
_TOKEN_SPEC = [
    ("ARROW", r"->"),
    ("OPCMP", r">=|<=|==|!="),
    ("OP", r"[<>]"),
    ("EQ", r"="),
    ("LPAREN", r"\\("),
    ("RPAREN", r"\\)"),
    ("COMMA", r","),
    ("LBRACE", r"\\{"),
    ("RBRACE", r"\\}"),
    ("STRING", r"\"[^\"]*\""),
    ("NUMBER", r"-?\d+(\.\d+)?"),
    ("NAME", r"[A-Za-z_][A-Za-z0-9_.]*"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t]+"),
    ("COMMENT", r"#[^\n]*"),
]

_KEYWORDS = {"workflow", "node", "edge", "branch", "start", "end", "when"}
_MASTER = re.compile("|".join(f"(?P<{t}>{p})" for t, p in _TOKEN_SPEC))


class LexError(Exception):
    """词法错误。"""


def tokenize(text: str) -> List[Token]:
    """将 DSL 文本转换为记号列表（忽略空白与换行）。"""
    tokens: List[Token] = []
    pos = 0
    while pos < len(text):
        m = _MASTER.match(text, pos)
        if not m:
            raise LexError(f"无法识别的字符：{text[pos]!r}（位置 {pos}）")
        kind = m.lastgroup
        value = m.group()
        pos = m.end()
        if kind in ("SKIP", "NEWLINE", "COMMENT"):
            continue
        # 关键字归并：NAME 命中关键字表则记为 KEYWORD
        if kind == "NAME" and value in _KEYWORDS:
            kind = "KEYWORD"
        tokens.append(Token(kind, value, m.start()))
    return tokens
