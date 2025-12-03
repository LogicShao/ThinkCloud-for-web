"""
测试脚本 - 重新运行拉康负面评价分析
用于展示完整的深度思考结果
"""

from src.deep_think import DeepThinkOrchestrator, format_deep_think_result
from src.api_service import api_service
from src.config import DEFAULT_MODEL


def main():
    # 创建编排器
    orchestrator = DeepThinkOrchestrator(
        api_service=api_service,
        model=DEFAULT_MODEL,  # 使用默认模型
        max_subtasks=6,
        enable_review=True,
        verbose=False,  # 减少日志输出
    )

    # 用户问题
    question = "拉康理论中关于理论的可证伪性、表述的故意晦涩、对科学方法的排斥、临床效用的质疑，以及其理论可能导致的相对主义或政治保守性的关键批评议题"

    print("=" * 80)
    print("开始深度思考分析...")
    print(f"问题: {question}")
    print("=" * 80)
    print()

    # 执行深度思考
    result = orchestrator.run(question)

    # 格式化输出
    formatted = format_deep_think_result(result, include_process=True)

    # 使用UTF-8编码输出，避免GBK编码错误
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print(formatted)
    print()
    print("=" * 80)
    print(f"总LLM调用次数: {result.total_llm_calls}")
    print(f"子任务数量: {len(result.subtask_results)}")
    print("=" * 80)

    # 保存完整结果到文件
    with open("lacan_analysis_complete.md", "w", encoding="utf-8") as f:
        f.write(formatted)
    print("\n完整结果已保存到: lacan_analysis_complete.md")

if __name__ == "__main__":
    main()
