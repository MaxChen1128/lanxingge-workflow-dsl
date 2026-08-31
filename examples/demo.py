"""揽星阁 AI 工作流 DSL 解析器 —— 离线演示。

不依赖任何外部服务，演示：
  1) 文本 DSL → 词法/语法解析 → 抽象语法树；
  2) 静态校验（引用完整、无环、可达）；
  3) 编译为可执行 DAG；
  4) 解释执行，并演示分支（score 高走发布、低走人工复核）。
"""

from workflow_dsl import WorkflowDSL
from workflow_dsl.core.compiler import NodeExecutor

DSL_TEXT = """
# 营销内容审核工作流
workflow "内容审核流" {
  start = fetch
  end   = done

  node fetch = HTTP_GET(url="https://api.example.com/article")
  node summarize = LLM(prompt="总结上文")
  node good = PUBLISH(channel="wechat")
  node bad  = HUMAN_REVIEW()
  node done = PASS()

  edge fetch -> summarize
  branch summarize -> good when score > 0.5
  branch summarize -> bad  when score <= 0.5
  edge good -> done
  edge bad  -> done
}
"""



def run(score: float) -> None:
    dsl = WorkflowDSL()
    wf = dsl.parse(DSL_TEXT)  # 解析 + 校验
    exe = dsl.compile(DSL_TEXT)  # 解析 + 校验 + 编译

    print(f"\n=== score={score} 场景 ===")
    print(f"解析得到节点：{list(wf.nodes.keys())}  start={wf.start} end={wf.end}")
    executor = NodeExecutor(overrides={"summarize": {"text": "mock", "score": score}})
    ctx = exe.run(executor)
    print("执行路径输出键：", list(ctx.keys()))
    taken = "good(PUBLISH)" if "good" in ctx else "bad(HUMAN_REVIEW)"
    print(f"分支命中：{taken}")


def main() -> None:
    run(0.8)  # 高分 -> 发布
    run(0.3)  # 低分 -> 人工复核
    print("\n演示完成。所有能力均离线可用，无外部服务依赖。")


if __name__ == "__main__":
    main()
