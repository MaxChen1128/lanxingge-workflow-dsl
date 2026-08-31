"""工作流 DSL 门面（统一入口）。

对外暴露 ``parse``（文本 → 校验后的 WorkflowDef）与 ``compile``（文本 → 可执行工作流），
以及 ``load_file`` 从文件加载。解析、校验、编译三阶段解耦，便于单独测试与扩展。
"""

from __future__ import annotations

from pathlib import Path

from .core.ast import WorkflowDef
from .core.compiler import ExecutableWorkflow, compile
from .core.parser import ParseError, parse
from .core.validator import ValidationError, validate


class DSLFacade:
    """工作流 DSL 解析与编译门面。"""

    def parse(self, text: str) -> WorkflowDef:
        """解析并静态校验，返回 WorkflowDef。"""
        wf = parse(text)
        validate(wf)
        return wf

    def compile(self, text: str) -> ExecutableWorkflow:
        """解析 + 校验 + 编译，返回可执行工作流。"""
        return compile(self.parse(text))

    def load_file(self, path: str) -> ExecutableWorkflow:
        """从 .dsl / .txt 文件加载并编译。"""
        text = Path(path).read_text(encoding="utf-8")
        return self.compile(text)


# 兼容导出别名
WorkflowDSL = DSLFacade
