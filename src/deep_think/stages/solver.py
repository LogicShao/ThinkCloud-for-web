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
    ):
        """
        初始化解决阶段处理器

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

            if self.verbose:
                self.logger.info(
                    f"[SOLVE] 完成子任务 {subtask.id}: {subtask.description[:30]}..."
                )

            return self._create_success_result(result, llm_calls=1)

        except Exception as e:
            # 打印原始响应方便调试
            if 'response' in locals():
                # 输出完整响应到日志
                if len(response) > 0:
                    # 预览前1000字符到WARNING级别
                    self.logger.warning(
                        f"[SOLVE] 子任务 {subtask.id} 执行失败，响应长度: {len(response)}, 前1000字符: {response[:1000]}")
                    # 完整响应到DEBUG级别
                    self.logger.debug(f"[SOLVE] 子任务 {subtask.id} 完整原始响应: {response}")
                else:
                    self.logger.error(f"[SOLVE] 子任务 {subtask.id} 执行失败，响应为空！")
            else:
                self.logger.error(f"[SOLVE] 子任务 {subtask.id} 执行失败，response变量未定义")

            self.logger.warning(f"[SOLVE] 子任务 {subtask.id} 执行失败: {e}")
            # 容错: 使用原始响应作为分析结果
            result = self._create_fallback_result(subtask, response if 'response' in locals() else str(e))
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
