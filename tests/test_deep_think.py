"""
测试深度思考模块
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_service import api_service
from src.deep_think import DeepThinkOrchestrator, format_deep_think_result
from src.config import DEFAULT_MODEL


def test_basic_deep_think():
    """测试基础深度思考功能"""
    print("=" * 60)
    print("测试深度思考模块 - 基础功能")
    print("=" * 60)

    # 检查API服务是否可用
    if not api_service.is_available():
        print("[FAIL] 没有可用的API提供商")
        print("请配置至少一个API密钥在.env文件中")
        return

    print(f"\n[INFO] 使用模型: {DEFAULT_MODEL}")
    print(f"[INFO] 可用提供商: {', '.join(api_service.get_available_providers())}")

    # 创建深度思考编排器
    orchestrator = DeepThinkOrchestrator(
        api_service=api_service,
        model=DEFAULT_MODEL,
        max_subtasks=4,
        enable_review=True,
        verbose=True
    )

    # 测试问题
    test_questions = [
        "什么是人工智能?请从历史、技术和应用三个角度分析。",
        "如何提高编程技能?",
        "气候变化的主要原因是什么?"
    ]

    # 选择一个问题测试
    question = test_questions[0]
    print(f"\n[TEST] 测试问题: {question}")
    print("-" * 60)

    try:
        # 执行深度思考
        result = orchestrator.run(question)

        # 格式化并打印结果
        formatted_output = format_deep_think_result(result, include_process=True)
        print("\n[RESULT] 深度思考结果:")
        print("=" * 60)
        print(formatted_output)
        print("=" * 60)

        # 打印统计信息
        print(f"\n[STATS] 统计信息:")
        print(f"  - 子任务数量: {len(result.subtask_results)}")
        print(f"  - LLM调用次数: {result.total_llm_calls}")
        if result.review:
            print(f"  - 质量评分: {result.review.overall_quality_score:.2%}")
            print(f"  - 发现问题: {len(result.review.issues_found)}")
            print(f"  - 改进建议: {len(result.review.improvement_suggestions)}")

        print("\n[SUCCESS] 测试通过!")

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_without_review():
    """测试不启用审查的深度思考"""
    print("\n" + "=" * 60)
    print("测试深度思考模块 - 无审查模式")
    print("=" * 60)

    if not api_service.is_available():
        print("[FAIL] 没有可用的API提供商")
        return

    orchestrator = DeepThinkOrchestrator(
        api_service=api_service,
        model=DEFAULT_MODEL,
        max_subtasks=3,
        enable_review=False,  # 禁用审查
        verbose=True
    )

    question = "Python和JavaScript有什么主要区别?"
    print(f"\n[TEST] 测试问题: {question}")
    print("-" * 60)

    try:
        result = orchestrator.run(question)

        print(f"\n[RESULT] 答案预览:")
        print(result.final_answer[:300] + "...")

        print(f"\n[STATS] 统计:")
        print(f"  - 子任务数: {len(result.subtask_results)}")
        print(f"  - LLM调用: {result.total_llm_calls}")
        print(f"  - 审查结果: {result.review}")

        print("\n[SUCCESS] 无审查模式测试通过!")

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")


def test_format_output():
    """测试输出格式化"""
    print("\n" + "=" * 60)
    print("测试输出格式化功能")
    print("=" * 60)

    # 创建一个模拟的结果对象
    from src.deep_think import (
        DeepThinkResult, Plan, Subtask, SubtaskResult, ReviewResult
    )

    mock_result = DeepThinkResult(
        original_question="测试问题",
        final_answer="# 这是一个测试答案\n\n详细内容...",
        plan=Plan(
            clarified_question="澄清后的测试问题",
            subtasks=[
                Subtask(id=1, description="子任务1"),
                Subtask(id=2, description="子任务2")
            ],
            plan_text="测试规划",
            reasoning_approach="测试策略"
        ),
        subtask_results=[
            SubtaskResult(
                subtask_id=1,
                description="子任务1",
                analysis="分析1",
                intermediate_conclusion="结论1",
                confidence=0.9
            ),
            SubtaskResult(
                subtask_id=2,
                description="子任务2",
                analysis="分析2",
                intermediate_conclusion="结论2",
                confidence=0.8
            )
        ],
        review=ReviewResult(
            issues_found=["问题1"],
            improvement_suggestions=["建议1"],
            overall_quality_score=0.85,
            review_notes="测试审查"
        ),
        total_llm_calls=5
    )

    # 测试格式化
    formatted = format_deep_think_result(mock_result, include_process=True)
    print("\n[FORMATTED OUTPUT]:")
    print(formatted)

    print("\n[SUCCESS] 格式化测试通过!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试深度思考模块")
    parser.add_argument(
        "--test",
        choices=["basic", "no-review", "format", "all"],
        default="all",
        help="选择要运行的测试"
    )

    args = parser.parse_args()

    if args.test == "basic":
        test_basic_deep_think()
    elif args.test == "no-review":
        test_without_review()
    elif args.test == "format":
        test_format_output()
    else:  # all
        test_format_output()
        test_without_review()
        test_basic_deep_think()

    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
