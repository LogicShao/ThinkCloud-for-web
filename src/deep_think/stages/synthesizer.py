"""
整合阶段处理器
负责综合所有子任务结论生成最终答案
"""

from typing import Any, Dict, List

from ..core.interfaces import IPromptTemplate
from ..core.models import Plan, StageContext, StageResult, SubtaskResult, ThinkingStage
from .base import BaseStageProcessor


class SynthesizerStageProcessor(BaseStageProcessor):
    """整合阶段处理器"""

    def __init__(
            self,
            llm_service,
            json_parser,
            prompt_template: IPromptTemplate,
            verbose: bool = True,
    ):
        """
        初始化整合阶段处理器

        Args:
            llm_service: LLM服务实例
            json_parser: JSON解析器
            prompt_template: 提示模板
            verbose: 是否输出详细日志
        """
        super().__init__(llm_service, json_parser, verbose)
        self.prompt_template = prompt_template

    def get_stage(self) -> ThinkingStage:
        """获取阶段类型"""
        return ThinkingStage.SYNTHESIZE

    def execute(self, context: StageContext, **kwargs) -> StageResult:
        """执行整合阶段"""
        original_question = kwargs.get("original_question", "")
        plan = kwargs.get("plan")
        subtask_results = kwargs.get("subtask_results", [])

        if not plan:
            return self._create_error_result("规划不能为空")

        try:
            # 构建所有结论的汇总
            all_conclusions = self._build_all_conclusions(subtask_results)

            # 格式化提示词
            prompt = self.prompt_template.format(
                original_question=original_question,
                clarified_question=plan.clarified_question,
                reasoning_approach=plan.reasoning_approach,
                all_conclusions=all_conclusions,
            )

            # 调用LLM
            response = self._call_llm(prompt, context, self.get_stage())

            # 解析响应
            synthesis_data = self._parse_json_response(response)

            # 获取最终答案
            final_answer = self._extract_final_answer(synthesis_data, response)

            if self.verbose:
                self.logger.info("[SYNTHESIZE] 生成最终答案")

            return self._create_success_result(final_answer, llm_calls=1)

        except Exception as e:
            # 打印原始响应方便调试
            if 'response' in locals():
                if len(response) > 0:
                    self.logger.warning(
                        f"[SYNTHESIZE] 整合失败，响应长度: {len(response)}, 前1000字符: {response[:1000]}")
                    self.logger.debug(f"[SYNTHESIZE] 完整原始响应: {response}")
                else:
                    self.logger.error(f"[SYNTHESIZE] 整合失败，响应为空！")
            else:
                self.logger.error(f"[SYNTHESIZE] 整合失败，response变量未定义")

            self.logger.warning(f"[SYNTHESIZE] 整合失败: {e}")
            # 容错: 使用回退答案
            fallback_answer = self._create_fallback_answer(subtask_results)
            return self._create_success_result(fallback_answer, llm_calls=1)

    def _build_all_conclusions(self, subtask_results: List[SubtaskResult]) -> str:
        """构建所有子任务结论的汇总"""
        if not subtask_results:
            return "暂无子任务结论"

        conclusion_parts = []
        for result in subtask_results:
            part = (
                f"**子任务 {result.subtask_id}: {result.description}**\n"
                f"结论: {result.intermediate_conclusion}\n"
                f"可信度: {result.confidence:.0%}\n"
                f"局限性: {', '.join(result.limitations) if result.limitations else '无'}"
            )
            conclusion_parts.append(part)

        return "\n\n".join(conclusion_parts)

    def _extract_final_answer(self, synthesis_data: Dict[str, Any], original_response: str) -> str:
        """从整合数据中提取最终答案"""
        final_answer = synthesis_data.get("final_answer", original_response)

        # 添加整合说明(可选)
        if "synthesis_notes" in synthesis_data:
            final_answer += f"\n\n---\n**整合说明:** {synthesis_data['synthesis_notes']}"

        return final_answer

    def _create_fallback_answer(self, subtask_results: List[SubtaskResult]) -> str:
        """创建回退答案（容错处理）"""
        if not subtask_results:
            return "⚠️ 未能生成完整答案：没有可用的子任务结论"

        fallback_parts = ["基于上述分析，综合结论如下：\n"]
        for result in subtask_results:
            conclusion_preview = result.intermediate_conclusion[:100]
            fallback_parts.append(f"- {result.description}: {conclusion_preview}")

        return "\n".join(fallback_parts)
