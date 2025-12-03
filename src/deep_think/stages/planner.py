"""
规划阶段处理器
负责问题澄清和子任务拆解
"""

from typing import Any, Dict, List

from ..core.interfaces import IPromptTemplate
from ..core.models import Plan, StageContext, StageResult, Subtask, ThinkingStage
from .base import BaseStageProcessor


class PlannerStageProcessor(BaseStageProcessor):
    """规划阶段处理器"""

    def __init__(
            self,
            llm_service,
            json_parser,
            prompt_template: IPromptTemplate,
            max_subtasks: int = 6,
            verbose: bool = True,
    ):
        """
        初始化规划阶段处理器

        Args:
            llm_service: LLM服务实例
            json_parser: JSON解析器
            prompt_template: 提示模板
            max_subtasks: 最大子任务数量
            verbose: 是否输出详细日志
        """
        super().__init__(llm_service, json_parser, verbose)
        self.prompt_template = prompt_template
        self.max_subtasks = max_subtasks

    def get_stage(self) -> ThinkingStage:
        """获取阶段类型"""
        return ThinkingStage.PLAN

    def execute(self, context: StageContext, **kwargs) -> StageResult:
        """执行规划阶段"""
        question = kwargs.get("question", "")
        if not question:
            return self._create_error_result("问题不能为空")

        try:
            # 格式化提示词
            prompt = self.prompt_template.format(question=question)

            # 调用LLM
            response = self._call_llm(prompt, context, self.get_stage())

            # 解析响应
            plan_data = self._parse_json_response(response)

            # 构建Plan对象
            plan = self._build_plan(question, plan_data)

            if self.verbose:
                self.logger.info(f"[PLAN] 生成了 {len(plan.subtasks)} 个子任务")

            return self._create_success_result(plan, llm_calls=1)

        except Exception as e:
            # 打印原始响应方便调试
            if 'response' in locals():
                if len(response) > 0:
                    # 预览前1000字符到WARNING级别
                    self.logger.warning(f"[PLAN] 规划失败，响应长度: {len(response)}, 前1000字符: {response[:1000]}")
                    # 完整响应到DEBUG级别
                    self.logger.debug(f"[PLAN] 完整原始响应: {response}")
                else:
                    self.logger.error(f"[PLAN] 规划失败，响应为空！")
            else:
                self.logger.error(f"[PLAN] 规划失败，response变量未定义")

            self.logger.warning(f"[PLAN] 规划失败: {e}")
            # 容错: 创建一个默认的简单规划
            plan = self._create_fallback_plan(question)
            return self._create_success_result(plan, llm_calls=1)

    def _build_plan(self, original_question: str, plan_data: Dict[str, Any]) -> Plan:
        """构建Plan对象"""
        subtasks = [
            Subtask(
                id=st["id"],
                description=st["description"],
                priority=st.get("priority", "medium"),
                dependencies=st.get("dependencies", []),
            )
            for st in plan_data.get("subtasks", [])[: self.max_subtasks]
        ]

        return Plan(
            clarified_question=plan_data.get("clarified_question", original_question),
            subtasks=subtasks,
            plan_text=plan_data.get("plan_text", ""),
            reasoning_approach=plan_data.get("reasoning_approach", ""),
        )

    def _create_fallback_plan(self, question: str) -> Plan:
        """创建回退规划（容错处理）"""
        return Plan(
            clarified_question=question,
            subtasks=[
                Subtask(id=1, description="深入理解和分析问题", priority="high"),
                Subtask(id=2, description="探索可能的解决方案", priority="medium"),
                Subtask(id=3, description="综合评估和总结", priority="medium"),
            ],
            plan_text="由于规划解析失败，使用默认三阶段分析流程",
        )
