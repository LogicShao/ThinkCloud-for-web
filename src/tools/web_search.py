"""
Web搜索工具 - 支持通过API进行网络搜索
目前支持DuckDuckGo搜索（无需API密钥）
"""

import json
import os
import warnings
from typing import Any, Dict, List, Optional

# NOTE: 尝试使用新的 ddgs 包（无警告）
try:
    from ddgs import DDGS

    DDGS_AVAILABLE = True
    USING_NEW_PACKAGE = True
except ImportError:
    # 回退到旧的 duckduckgo_search 包
    # 使用包级别的 catch_warnings 来抑制导入警告
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            from duckduckgo_search import DDGS

            DDGS_AVAILABLE = True
            USING_NEW_PACKAGE = False
        except ImportError:
            DDGS_AVAILABLE = False
            USING_NEW_PACKAGE = False


class WebSearchTool:
    """Web搜索工具类"""

    def __init__(self, max_results: int = 5, region: str = "cn-zh"):
        """
        初始化Web搜索工具

        Args:
            max_results: 返回的最大搜索结果数
            region: 搜索区域（cn-zh为中国，us-en为美国）
        """
        self.max_results = max_results
        self.region = region
        self.available = DDGS_AVAILABLE
        self.using_new_package = USING_NEW_PACKAGE

        if not self.available:
            print("[WARN] duckduckgo_search 未安装，web_search 功能不可用")
            print("[WARN] 请运行: pip install duckduckgo-search")

    def is_available(self) -> bool:
        """检查工具是否可用"""
        return self.available

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        执行网络搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数（可覆盖初始化设置）

        Returns:
            搜索结果列表，每个结果包含: title, href, body
        """
        if not self.available:
            return [{"title": "错误", "href": "", "body": "duckduckgo_search 未安装，无法执行搜索"}]

        max_results = max_results or self.max_results

        try:
            # 实例化DDGS - 如果是旧包，则使用更严格的警告抑制
            if self.using_new_package:
                with DDGS() as ddgs:
                    results = list(
                        ddgs.text(keywords=query, region=self.region, max_results=max_results)
                    )
            else:
                # 旧包 - 捕获实例化时的警告
                # 警告通常在DDGS()构造函数时发出
                import sys
                from io import StringIO

                # 暂时重定向stderr以捕获警告
                old_stderr = sys.stderr
                sys.stderr = StringIO()

                try:
                    with DDGS() as ddgs:
                        # 恢复stderr
                        sys.stderr = old_stderr
                        results = list(
                            ddgs.text(keywords=query, region=self.region, max_results=max_results)
                        )
                except Exception:
                    sys.stderr = old_stderr
                    raise
                finally:
                    sys.stderr = old_stderr

            # 格式化结果
            formatted_results = []
            for r in results:
                formatted_results.append(
                    {
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", ""),
                    }
                )

            return formatted_results

        except Exception as e:
            print(f"[ERROR] 搜索失败: {e}")
            return [{"title": "搜索错误", "href": "", "body": f"搜索过程中发生错误: {e!s}"}]

    def search_and_format(self, query: str, max_results: Optional[int] = None) -> str:
        """
        执行搜索并格式化为文本

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            格式化的搜索结果文本
        """
        results = self.search(query, max_results)

        if not results:
            return f'搜索查询 "{query}" 没有返回任何结果。'

        output = f'搜索查询: "{query}"\n'
        output += f"找到 {len(results)} 条结果:\n\n"

        for i, result in enumerate(results, 1):
            output += f"### 结果 {i}: {result['title']}\n"
            output += f"链接: {result['href']}\n"
            output += f"摘要: {result['body']}\n\n"

        return output

    def __repr__(self) -> str:
        status = "可用" if self.available else "不可用"
        return f"<WebSearchTool: {status}, max_results={self.max_results}, region={self.region}>"


# 创建默认实例
default_search_tool = WebSearchTool()
