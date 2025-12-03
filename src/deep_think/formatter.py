"""
深度思考结果格式化工具
将DeepThinkResult格式化为用户友好的输出
"""

from .core.interfaces import IResultFormatter
from .core.models import DeepThinkResult


class DeepThinkResultFormatter(IResultFormatter):
    """深度思考结果格式化器"""

    def format(self, result: DeepThinkResult, **kwargs) -> str:
        """
        格式化深度思考结果为用户友好的输出

        Args:
            result: DeepThinkResult实例
            include_process: 是否包含思考过程详情（默认True）
            **kwargs: 其他参数

        Returns:
            str: 格式化的Markdown文本
        """
        include_process = kwargs.get("include_process", True)

        output_parts = []

        # 主要答案
        output_parts.append("# 💡 深度思考结果\n")

        # 确保 final_answer 不为空
        if result.final_answer and result.final_answer.strip():
            output_parts.append(result.final_answer)
        else:
            output_parts.append("⚠️ **未能生成完整答案**\n\n可能原因：")
            output_parts.append("- 模型未返回符合预期的 JSON 格式")
            output_parts.append("- API 调用超时或失败")
            output_parts.append("\n请查看下方的思考过程摘要了解详情。")

        # 思考过程(可选)
        if include_process and result.thinking_process_summary:
            output_parts.append(f"\n\n{result.thinking_process_summary}")

        # 审查结果(如果有)
        if result.review:
            output_parts.append("\n\n## 🔍 质量审查")
            output_parts.append(f"**整体评分:** {result.review.overall_quality_score:.0%}")

            if result.review.issues_found:
                output_parts.append("\n**发现的问题:**")
                for issue in result.review.issues_found:
                    output_parts.append(f"- {issue}")

            if result.review.improvement_suggestions:
                output_parts.append("\n**改进建议:**")
                for suggestion in result.review.improvement_suggestions:
                    output_parts.append(f"- {suggestion}")

        # 元信息
        output_parts.append(f"\n\n---\n*深度思考模式 | LLM调用次数: {result.total_llm_calls}*")

        return "\n".join(output_parts)


def format_deep_think_result(result: DeepThinkResult, include_process: bool = True) -> str:
    """
    格式化深度思考结果为用户友好的输出（兼容旧接口）

    Args:
        result: DeepThinkResult实例
        include_process: 是否包含思考过程详情

    Returns:
        str: 格式化的Markdown文本
    """
    formatter = DeepThinkResultFormatter()
    return formatter.format(result, include_process=include_process)
