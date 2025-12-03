"""
审查阶段处理器
负责对最终答案进行质量审查
"""

from typing import Any, Dict

from ..core.interfaces import IPromptTemplate
from ..core.models import ReviewResult, StageContext, StageResult, ThinkingStage
from .base import BaseStageProcessor


class ReviewerStageProcessor(BaseStageProcessor):
    """审查阶段处理器"""

    def __init__(
            self,
            llm_service,
            json_parser,
            prompt_template: IPromptTemplate,
            verbose: bool = True,
    ):
        """
        初始化审查阶段处理器

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
        return ThinkingStage.REVIEW

    def execute(self, context: StageContext, **kwargs) -> StageResult:
        """执行审查阶段"""
        original_question = kwargs.get("original_question", "")
        final_answer = kwargs.get("final_answer", "")

        if not final_answer:
            return self._create_error_result("最终答案不能为空")

        try:
            # 格式化提示词
            prompt = self.prompt_template.format(
                original_question=original_question,
                final_answer=final_answer,
            )

            # 调用LLM
            response = self._call_llm(prompt, context, self.get_stage())

            # 解析响应
            review_data = self._parse_json_response(response)

            # 构建ReviewResult对象
            review_result = self._build_review_result(review_data)

            if self.verbose:
                self.logger.info(
                    f"[REVIEW] 审查完成，质量评分: {review_result.overall_quality_score:.2f}"
                )

            return self._create_success_result(review_result, llm_calls=1)

        except Exception as e:
            # 打印原始响应方便调试
            if 'response' in locals():
                if len(response) > 0:
                    self.logger.warning(f"[REVIEW] 审查失败，响应长度: {len(response)}, 前1000字符: {response[:1000]}")
                    self.logger.debug(f"[REVIEW] 完整原始响应: {response}")
                else:
                    self.logger.error(f"[REVIEW] 审查失败，响应为空！")
            else:
                self.logger.error(f"[REVIEW] 审查失败，response变量未定义")

            self.logger.warning(f"[REVIEW] 审查失败: {e}")
            # 容错: 返回默认审查结果
            default_review = self._create_default_review_result()
            return self._create_success_result(default_review, llm_calls=1)

    def _build_review_result(self, review_data: Dict[str, Any]) -> ReviewResult:
        """构建ReviewResult对象"""
        return ReviewResult(
            issues_found=review_data.get("issues_found", []),
            improvement_suggestions=review_data.get("improvement_suggestions", []),
            overall_quality_score=float(review_data.get("overall_quality_score", 0.75)),
            review_notes=review_data.get("review_notes", ""),
        )

    def _create_default_review_result(self) -> ReviewResult:
        """创建默认审查结果（容错处理）"""
        return ReviewResult(
            issues_found=[],
            improvement_suggestions=[],
            overall_quality_score=0.7,
            review_notes="审查数据解析失败",
        )
