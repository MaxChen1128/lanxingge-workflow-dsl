# 揽星阁 AI 工作流 DSL 解析器

> 软件设计说明书（用于软件著作权登记与高新技术企业文化产品论证）

## 一、系统概述

揽星阁 AI 工作流 DSL 解析器（Lanxingge Workflow DSL）是一套面向 AI 工作流的领域
特定语言解析与执行软件。系统将文本化的工作流描述经词法分析、语法解析转换为抽象
语法树（AST），再做静态校验（环检测、引用完整性、可达性），最终编译为可执行的
有向无环图（DAG）并解释执行。可作为智能体编排引擎、RAG、推理调度等上层 AI 能力的
流程编排底座，亦可作为高新技术企业认定的研发活动与核心支撑佐证。

## 二、运行环境

- 操作系统：Windows / Linux / macOS
- 运行环境：Python 3.10 及以上
- 依赖：标准库即可离线运行；接入真实算子时可选对应 SDK

## 三、总体架构

```
DSL 文本
   │
   ▼
Lexer 词法分析 ──► Parser 语法分析（递归下降）
   │                   │
   │                   ▼
   │              WorkflowDef（AST）
   │                   │
   ▼                   ▼
Validator 校验（引用/环/可达）──► Compiler 编译（DAG）
                                  │
                                  ▼
                            Interpreter 解释执行（分支选择）
```

## 四、功能模块说明

| 模块 | 职责 |
|---|---|
| `lexer` | 词法分析：文本 → 记号流（含关键字/字符串/数字/运算符） |
| `parser` | 语法分析：记号流 → `WorkflowDef` AST（递归下降） |
| `ast` | AST 定义：节点、边、分支条件、工作流 |
| `validator` | 静态校验：节点/边引用完整、无环、起止可达 |
| `compiler` | 编译为 DAG + 节点执行器 + 解释器（分支选择） |
| `dsl` | 门面：parse / compile / load_file 统一入口 |

## 五、核心处理流程

1. `workflow` 文本经词法分析切分为记号；
2. 递归下降解析为 `WorkflowDef`（节点、边、分支条件、起止）；
3. 校验器检查引用完整性、环（拓扑排序）、start→end 可达性；
4. 编译器生成拓扑序与可执行工作流；
5. 解释器按序执行节点，依据分支条件选择下游路径，输出各节点结果。

## 六、DSL 示例

```
workflow "内容审核流" {
  start = fetch
  node fetch = HTTP_GET(url="https://api.x")
  node summarize = LLM(prompt="总结上文")
  branch summarize -> good when score > 0.5
  branch summarize -> bad  when score <= 0.5
  edge good -> done
}
```

## 七、使用方法

```bash
cd lanxingge-workflow-dsl
python examples/demo.py
```

接入真实算子时，继承 `NodeExecutor` 覆写 `_op_<算子>` 方法，其余解析/校验/执行
流程无需改动。

## 八、软件特点

- **真解析**：自带词法 + 递归下降语法分析，非简单正则匹配；
- **可校验**：编译前静态检查，环/悬空引用/不可达一律拦截；
- **可分支**：条件边支持 `> < >= <= == !=`，驱动多路流程；
- **离线可用**：内置 Mock 算子，无需外部服务即可联调；
- **易扩展**：算子以 `_op_<名称>` 约定接入，新增算子零侵入。
