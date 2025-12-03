"""
解决阶段处理器
负责逐个分析子任务
"""

from typing import Any, Dict, List

from ..core.interfaces import IPromptTemplate
from ..core.models import (
    Plan,
    StageContext,
    StageResult,
    Subtask,
    SubtaskResult,
    ThinkingStage,
)
from .base import BaseStageProcessor


class SolverStageProcessor(BaseStageProcessor):
    """解决阶段处理器"""

    def __init__(
        self,
        llm_service,
        json_parser,
        prompt_template: IPromptTemplate,
        verbose: bool = True,
        web_search_tool=None,
    ):
        """
        初始化解决阶段处理器

        Args:
            llm_service: LLM服务实例
            json_parser: JSON解析器
            prompt_template: 提示模板
            verbose: 是否输出详细日志
            web_search_tool: Web搜索工具实例（可选）
        """
        super().__init__(llm_service, json_parser, verbose)
        self.prompt_template = prompt_template
        self.web_search_tool = web_search_tool

    def get_stage(self) -> ThinkingStage:
        """获取阶段类型"""
        return ThinkingStage.SOLVE

    def execute(self, context: StageContext, **kwargs) -> StageResult:
        """执行解决阶段"""
        subtask = kwargs.get("subtask")
        original_question = kwargs.get("original_question", "")
        previous_results = kwargs.get("previous_results", [])

        if not subtask:
            return self._create_error_result("子任务不能为空")

        try:
            # 构建之前的结论上下文
            previous_conclusions = self._build_previous_conclusions(previous_results)

            # 格式化提示词
            prompt = self.prompt_template.format(
                original_question=original_question,
                subtask_description=subtask.description,
                previous_conclusions=previous_conclusions,
            )

            # 调用LLM
            response = self._call_llm(prompt, context, self.get_stage())

            # 解析响应
            result_data = self._parse_json_response(response)

            # 构建SubtaskResult对象
            result = self._build_subtask_result(subtask, result_data, response)

            # 检查是否需要网络搜索
            if (
                result.needs_external_info
                and self.web_search_tool
                and self.web_search_tool.is_available()
            ):
                if self.verbose:
                    self.logger.info(f"[SOLVE] 子任务 {subtask.id} 需要外部信息，执行网络搜索...")
                result = self._enhance_with_web_search(result, original_question, context)

            if self.verbose:
                self.logger.info(f"[SOLVE] 完成子任务 {subtask.id}: {subtask.description[:30]}...")

            return self._create_success_result(result, llm_calls=1)

        except Exception as e:
            # 打印原始响应方便调试
            if "response" in locals():
                # 输出完整响应到日志
                if len(response) > 0:
                    # 预览前1000字符到WARNING级别
                    self.logger.warning(
                        f"[SOLVE] 子任务 {subtask.id} 执行失败，响应长度: {len(response)}, 前1000字符: {response[:1000]}"
                    )
                    # 完整响应到DEBUG级别
                    self.logger.debug(f"[SOLVE] 子任务 {subtask.id} 完整原始响应: {response}")
                else:
                    self.logger.error(f"[SOLVE] 子任务 {subtask.id} 执行失败，响应为空！")
            else:
                self.logger.error(f"[SOLVE] 子任务 {subtask.id} 执行失败，response变量未定义")

            self.logger.warning(f"[SOLVE] 子任务 {subtask.id} 执行失败: {e}")
            # 容错: 使用原始响应作为分析结果
            result = self._create_fallback_result(
                subtask, response if "response" in locals() else str(e)
            )
            return self._create_success_result(result, llm_calls=1)

    def _build_previous_conclusions(self, previous_results: List[SubtaskResult]) -> str:
        """构建之前的结论上下文"""
        if not previous_results:
            return "暂无"

        return "\n".join(
            [f"- 子任务{r.subtask_id}: {r.intermediate_conclusion}" for r in previous_results]
        )

    def _build_subtask_result(
        self, subtask: Subtask, result_data: Dict[str, Any], original_response: str
    ) -> SubtaskResult:
        """构建SubtaskResult对象"""
        return SubtaskResult(
            subtask_id=subtask.id,
            description=subtask.description,
            analysis=result_data.get("analysis", original_response),
            intermediate_conclusion=result_data.get("intermediate_conclusion", ""),
            confidence=float(result_data.get("confidence", 0.7)),
            limitations=result_data.get("limitations", []),
            needs_external_info=result_data.get("needs_external_info", False),
            suggested_tools=result_data.get("suggested_tools", []),
        )

    def _create_fallback_result(self, subtask: Subtask, response: str) -> SubtaskResult:
        """创建回退结果（容错处理）"""
        # 确保 response 是字符串且不为空
        if not isinstance(response, str):
            response = str(response)

        conclusion = response.strip()
        if len(conclusion) > 200:
            conclusion = conclusion[:200] + "..."
        elif not conclusion:
            conclusion = "（子任务执行完成，但未能提取结论）"

        return SubtaskResult(
            subtask_id=subtask.id,
            description=subtask.description,
            analysis=response,
            intermediate_conclusion=conclusion,
            confidence=0.6,
            limitations=["JSON解析失败，使用原始响应"],
        )

    def _enhance_with_web_search(
        self, result: SubtaskResult, original_question: str, context: StageContext
    ) -> SubtaskResult:
        """
        使用网络搜索增强子任务结果

        Args:
            result: 原始子任务结果
            original_question: 原始问题
            context: 阶段上下文

        Returns:
            增强后的子任务结果
        """
        try:
            # 构建搜索查询
            search_queries = []

            # 如果有建议的工具并包含"search"，使用建议的搜索关键词
            if result.suggested_tools and any(
                "search" in tool.lower() for tool in result.suggested_tools
            ):
                # 从子任务描述中提取关键词作为搜索查询
                search_queries.append(result.description)
            else:
                # 使用原始问题和子任务描述组合
                search_queries.append(f"{original_question} {result.description}")

            # 执行搜索并收集结果
            all_search_results = []
            for query in search_queries[:1]:  # 限制为1个查询避免过度搜索
                if self.verbose:
                    self.logger.info(f"[SEARCH] 执行搜索: {query[:50]}...")

                search_results = self.web_search_tool.search_and_format(query, max_results=3)
                all_search_results.append(search_results)

            # 将搜索结果合并到分析中
            enhanced_analysis = (
                result.analysis + "\n\n### 🌐 网络搜索结果\n\n" + "\n\n".join(all_search_results)
            )

            # 使用LLM重新分析，整合搜索结果
            integration_prompt = f"""
请基于以下信息，整合网络搜索结果到你的分析中：

**原始问题:** {original_question}

**子任务:** {result.description}

**初步分析:**
{result.analysis}

**网络搜索结果:**
{chr(10).join(all_search_results)}

请提供一个整合了搜索结果的更完整的分析和结论。以JSON格式返回：
{{
    "enhanced_analysis": "整合后的分析（包含搜索结果的关键信息）",
    "enhanced_conclusion": "更新后的结论",
    "confidence": 0.0-1.0 的置信度（考虑搜索结果后）
}}
"""

            # 调用LLM整合搜索结果
            integration_response = self._call_llm(integration_prompt, context, self.get_stage())
            integration_data = self._parse_json_response(integration_response)

            # 更新结果
            result.analysis = integration_data.get("enhanced_analysis", enhanced_analysis)
            result.intermediate_conclusion = integration_data.get(
                "enhanced_conclusion", result.intermediate_conclusion
            )
            result.confidence = float(integration_data.get("confidence", result.confidence))
            result.limitations.append("已整合网络搜���结果")

            if self.verbose:
                self.logger.info(f"[SEARCH] 成功整合搜索结果到子任务 {result.subtask_id}")

        except Exception as e:
            self.logger.warning(f"[SEARCH] 网络搜索增强失败: {e}")
            # 失败时返回原始结果
            result.limitations.append(f"网络搜索失败: {e!s}")

        return result
