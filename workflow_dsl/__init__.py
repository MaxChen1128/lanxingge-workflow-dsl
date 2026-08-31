"""揽星阁 AI 工作流 DSL 解析器。

面向 AI 工作流的领域特定语言（DSL）解析与执行软件。系统将文本化的工作流描述经
词法分析、语法解析转换为抽象语法树（AST），再做静态校验（环检测、引用完整性、
可达性），最终编译为可执行的 DAG 并执行。可作为智能体编排引擎、RAG、推理调度等
上层能力的流程编排底座，亦可作为高新技术企业认定的研发活动与核心支撑佐证。
"""

from .dsl import WorkflowDSL
from .core.ast import WorkflowDef

__all__ = ["WorkflowDSL", "WorkflowDef"]
__version__ = "0.1.0"
