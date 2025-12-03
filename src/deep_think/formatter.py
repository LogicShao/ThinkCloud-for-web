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
            # 清理答案中的JSON标记和内部格式
            cleaned_answer = self._clean_answer(result.final_answer)
            output_parts.append(cleaned_answer)
        else:
            output_parts.append("⚠️ **未能生成完整答案**\n\n可能原因：")
            output_parts.append("- 模型未返回符合预期的 JSON 格式")
            output_parts.append("- API 调用超时或失败")
            output_parts.append("\n请查看下方的思考过程摘要了解详情。")

        # 思考过程(可选)
        if include_process and result.thinking_process_summary:
            # 清理并格式化思考过程
            cleaned_summary = self._clean_thinking_summary(result.thinking_process_summary)
            output_parts.append(f"\n\n{cleaned_summary}")

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

    def _clean_answer(self, answer: str) -> str:
        """
        清理答案中的JSON格式标记和内部结构

        Args:
            answer: 原始答案文本

        Returns:
            str: 清理后的答案
        """
        import re

        # 移除常见的JSON标记
        cleaned = re.sub(r"```json\n?", "", answer)
        cleaned = re.sub(r"```", "", cleaned)

        # 移除或转换子任务标题
        cleaned = re.sub(r"##\s+子任务\s+\d+:\s*", "", cleaned)

        # 将可信度标记转换为更自然的表达
        cleaned = re.sub(r"可信度:\s*(\d+)%", r"**可信度:** \1%", cleaned)
        cleaned = re.sub(r"可信度:\s*([\d.]+)", r"**可信度:** \1", cleaned)

        # 将"结论:"转换为更自然的段落开头
        cleaned = re.sub(r"^结论:\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"结论:\s*", "\n因此，", cleaned)

        # 移除多余的空格和换行
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()

    def _clean_thinking_summary(self, summary: str) -> str:
        """
        清理思考过程摘要，正确显示子任务的analysis内容

        Args:
            summary: 原始摘要文本

        Returns:
            str: 清理后的摘要
        """
        import re

        if not summary:
            return ""

        output_parts = ["## 🧠 思考过程概述\n"]

        # 检查是否包含子任务部分
        if "子任务执行情况" in summary or "子任务" in summary:
            lines = summary.split("\n")
            in_subtask_section = False
            subtask_content = []

            # 提取子任务内容区域
            for line in lines:
                if "子任务执行情况" in line or ("子任务" in line and (":" in line or "情况" in line)):
                    in_subtask_section = True
                    continue
                elif in_subtask_section and line.startswith("##"):
                    in_subtask_section = False
                    break
                elif in_subtask_section and line.strip():
                    subtask_content.append(line)

            # 重新格式化子任务内容
            if subtask_content:
                current_task_id = ""
                current_task_desc = ""
                current_content = []

                for line in subtask_content:
                    line = line.strip()

                    # 识别子任务标题行（格式：1. description）
                    task_match = re.match(r'(\d+)\.\s*(.+)', line)
                    if task_match:
                        # 完成上一个任务
                        if current_task_id and current_content:
                            self._format_subtask(output_parts, current_task_desc, current_content)

                        # 开始新任务
                        current_task_id = task_match.group(1)
                        current_task_desc = task_match.group(2).strip()
                        current_content = []
                    elif line and not line.startswith("---"):
                        # 收集内容（可信度、结论）
                        if line.startswith('"') and line.endswith('"'):
                            line = line.strip('"')
                        if line:
                            current_content.append(line)

                # 添加最后一个任务
                if current_task_id and current_content:
                    self._format_subtask(output_parts, current_task_desc, current_content)

        # 检查是否有质量审查部分
        if "发现的问题" in summary:
            output_parts.append("\n## 🔍 质量审查\n")

            qa_match = re.search(r"发现的问题:(.*?)(?:改进建议:|---|\Z)", summary, re.DOTALL)
            if qa_match:
                issues_text = qa_match.group(1).strip()
                output_parts.append("**发现的主要问题：**\n")

                issues = re.findall(r"\d+\.\s*(.+)", issues_text)
                for issue in issues:
                    output_parts.append(f"- {issue}")

        if "改进建议" in summary:
            output_parts.append("\n**改进建议：**\n")

            suggestion_match = re.search(r"改进建议:(.*)", summary, re.DOTALL)
            if suggestion_match:
                suggestions_text = suggestion_match.group(1).strip()
                suggestions = re.findall(r"\d+\.\s*(.+)", suggestions_text)
                for suggestion in suggestions:
                    output_parts.append(f"- {suggestion}")

        return "\n".join(output_parts).strip()

    def _format_subtask(self, output_parts, task_title, content_lines):
        """
        格式化单个子任务的输出，正确显示analysis内容

        Args:
            output_parts: 输出列表
            task_title: 子任务描述
            content_lines: 内容行列表（包含结论和可信度）
        """
        # 添加子任务标题
        output_parts.append(f"\n**{task_title}**\n")

        # 添加内容（主要是结论和可信度）
        for line in content_lines:
            line = line.strip()
            if line and not line.startswith("---"):
                # 移除JSON标记
                if "```json" in line:
                    continue
                # 转换可信度标记
                if "可信度:" in line:
                    line = line.replace("可信度:", "**可信度:**")
                if line.startswith('"') and line.endswith('"'):
                    line = line.strip('"')
                if line:
                    output_parts.append(line.strip())

        # 添加一个空白行分隔
        output_parts.append("")


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
