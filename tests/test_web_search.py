"""
测试Web搜索功能
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_web_search_tool_initialization():
    """测试Web搜索工具初始化"""
    from src.tools.web_search import WebSearchTool

    tool = WebSearchTool(max_results=3)

    print(f"[INFO] Web搜索工具: {tool}")
    print(f"[INFO] 工具可用性: {tool.is_available()}")

    if not tool.is_available():
        print("[WARN] duckduckgo-search 未安装，请运行: pip install duckduckgo-search")
        return False

    return True


def test_web_search_basic():
    """测试基本搜索功能"""
    from src.tools.web_search import WebSearchTool

    tool = WebSearchTool(max_results=3, region="cn-zh")

    if not tool.is_available():
        print("[SKIP] 跳过搜索测试（工具不可用）")
        return

    print("\n" + "=" * 50)
    print("[TEST] 执行搜索: Python编程语言")
    print("=" * 50)

    results = tool.search("Python编程语言", max_results=3)

    print(f"\n[INFO] 找到 {len(results)} 条结果:\n")

    for i, result in enumerate(results, 1):
        print(f"结果 {i}:")
        print(f"  标题: {result.get('title', 'N/A')}")
        print(f"  链接: {result.get('href', 'N/A')}")
        print(f"  摘要: {result.get('body', 'N/A')[:100]}...")
        print()


def test_web_search_formatted():
    """测试格式化搜索结果"""
    from src.tools.web_search import WebSearchTool

    tool = WebSearchTool(max_results=2, region="cn-zh")

    if not tool.is_available():
        print("[SKIP] 跳过格式化测试（工具不可用）")
        return

    print("\n" + "=" * 50)
    print("[TEST] 格式化搜索结果")
    print("=" * 50)

    formatted = tool.search_and_format("AI人工智能", max_results=2)
    print(formatted)


def test_deep_think_with_search():
    """测试深度思考+搜索集成（模拟）"""
    print("\n" + "=" * 50)
    print("[TEST] 深度思考+搜索集成（理论测试）")
    print("=" * 50)

    from src.deep_think.core.models import SubtaskResult

    # 模拟一个需要外部信息的子任务结果
    result = SubtaskResult(
        subtask_id=1,
        description="查找最新的AI发展趋势",
        analysis="初步分析...",
        intermediate_conclusion="需要外部信息",
        confidence=0.5,
        needs_external_info=True,
        suggested_tools=["search"],
    )

    print(f"[INFO] 子任务: {result.description}")
    print(f"[INFO] 需要外部信息: {result.needs_external_info}")
    print(f"[INFO] 建议工具: {result.suggested_tools}")

    if result.needs_external_info and "search" in result.suggested_tools:
        print("[OK] ✓ 子任务正确标记需要搜索")
    else:
        print("[FAIL] ✗ 子任务标记错误")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("Web搜索功能测试")
    print("=" * 50)

    # 测试1: 初始化
    print("\n[1/4] 测试工具初始化...")
    available = test_web_search_tool_initialization()

    if available:
        # 测试2: 基本搜索
        print("\n[2/4] 测试基本搜索...")
        test_web_search_basic()

        # 测试3: 格式化输出
        print("\n[3/4] 测试格式化输出...")
        test_web_search_formatted()
    else:
        print("\n[SKIP] 跳过搜索测试（工具不可用）")

    # 测试4: 集成测试
    print("\n[4/4] 测试深度思考集成...")
    test_deep_think_with_search()

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
