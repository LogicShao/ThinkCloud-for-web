"""
深度思考编排器
管理多阶段推理流程，协调各个阶段处理器
"""

from typing import Optional

from src.logging import (
    EnhancedLogger,
    LogContext,
    get_deep_think_orchestrator_logger,
    log_function_call,
)

from .core.interfaces import ILLMService, IOrchestrator
from .core.models import (
    DeepThinkResult,
    Plan,
    ReviewResult,
    StageContext,
    SubtaskResult,
    ThinkingStage,
)
from .prompts.manager import PromptTemplateManager
from .stages import (
    PlannerStageProcessor,
    ReviewerStageProcessor,
    SolverStageProcessor,
    SynthesizerStageProcessor,
)
from .utils import DefaultJSONParser, MemoryCacheManager, generate_cache_key


class DeepThinkOrchestrator(IOrchestrator):
    """深度思考编排器 - 管理多阶段推理流程"""

    def __init__(
        self,
        api_service: ILLMService,
        model: str,
        max_subtasks: int = 6,
        enable_review: bool = True,
        enable_web_search: bool = False,
        verbose: bool = True,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        request_id: Optional[str] = None,
    ):
        """
        初始化深度思考编排器

        Args:
            api_service: MultiProviderAPIService实例
            model: 使用的模型名称
            max_subtasks: 最大子任务数量
            enable_review: 是否启用最终审查
            enable_web_search: 是否启用网络搜索功能
            verbose: 是否输出详细日志
            system_instruction: 系统提示词
            temperature: 温度参数
            top_p: 核采样参数
            max_tokens: 最大token数
            request_id: 请求ID，用于日志追踪
        """
        self.api_service = api_service
        self.model = model
        self.max_subtasks = max_subtasks
        self.enable_review = enable_review
        self.enable_web_search = enable_web_search
        self.verbose = verbose

        # 模型参数
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        # 初始化Web搜索工具
        self.web_search_tool = None
        if enable_web_search:
            try:
                from src.tools.web_search import WebSearchTool

                self.web_search_tool = WebSearchTool()
                if not self.web_search_tool.is_available():
                    print("[WARN] Web搜索工具不可用，请安装: pip install duckduckgo-search")
                    self.web_search_tool = None
            except Exception as e:
                print(f"[ERROR] 初始化Web搜索工具失败: {e}")
                self.web_search_tool = None

        # 初始化日志记录器
        self.logger = get_deep_think_orchestrator_logger(
            LogContext(
                request_id=request_id,
                module="orchestrator",
                custom_fields={
                    "model": model,
                    "max_subtasks": max_subtasks,
                    "enable_review": enable_review,
                    "verbose": verbose,
                },
            )
        )

        # 初始化组件
        self.json_parser = DefaultJSONParser()
        self.cache_manager = MemoryCacheManager()
        self.prompt_manager = PromptTemplateManager()

        # 初始化阶段处理器
        self._initialize_stage_processors()

        # 统计信息
        self.total_llm_calls = 0

        self.logger.info("编排器初始化完成")

    def _initialize_stage_processors(self):
        """初始化阶段处理器"""
        # 获取各个阶段的模板
        plan_template = self.prompt_manager.get_template_by_stage(ThinkingStage.PLAN)
        solve_template = self.prompt_manager.get_template_by_stage(ThinkingStage.SOLVE)
        synthesize_template = self.prompt_manager.get_template_by_stage(ThinkingStage.SYNTHESIZE)
        review_template = self.prompt_manager.get_template_by_stage(ThinkingStage.REVIEW)

        # 创建阶段处理器
        self.planner = PlannerStageProcessor(
            llm_service=self.api_service,
            json_parser=self.json_parser,
            prompt_template=plan_template,
            max_subtasks=self.max_subtasks,
            verbose=self.verbose,
        )

        self.solver = SolverStageProcessor(
            llm_service=self.api_service,
            json_parser=self.json_parser,
            prompt_template=solve_template,
            verbose=self.verbose,
            web_search_tool=self.web_search_tool if self.enable_web_search else None,
        )

        self.synthesizer = SynthesizerStageProcessor(
            llm_service=self.api_service,
            json_parser=self.json_parser,
            prompt_template=synthesize_template,
            verbose=self.verbose,
        )

        self.reviewer = ReviewerStageProcessor(
            llm_service=self.api_service,
            json_parser=self.json_parser,
            prompt_template=review_template,
            verbose=self.verbose,
        )

    @log_function_call(level=5)  # TRACE级别
    def run(self, question: str, **kwargs) -> DeepThinkResult:
        """
        执行深度思考流程

        Args:
            question: 用户问题

        Returns:
            DeepThinkResult: 完整的思考结果
        """
        self.logger.info("开始深度思考流程", question_preview=question[:50])

        try:
            # 创建执行上下文
            context = self._create_context()

            # 阶段1: 规划
            with self.logger.timer("plan_stage"):
                plan = self._execute_plan_stage(context, question)

            # 阶段2: 逐个解决子任务
            with self.logger.timer("solve_stage"):
                subtask_results = self._execute_solve_stage(context, question, plan)

            # 阶段3: 整合结果
            with self.logger.timer("synthesize_stage"):
                final_answer = self._execute_synthesize_stage(
                    context, question, plan, subtask_results
                )

            # 阶段4: 可选审查
            review_result = None
            if self.enable_review:
                with self.logger.timer("review_stage"):
                    review_result = self._execute_review_stage(context, question, final_answer)

            # 生成思考过程摘要
            thinking_summary = self._generate_thinking_summary(plan, subtask_results)

            # 更新总LLM调用次数
            self.total_llm_calls = context.llm_call_count

            result = DeepThinkResult(
                original_question=question,
                final_answer=final_answer,
                plan=plan,
                subtask_results=subtask_results,
                review=review_result,
                total_llm_calls=self.total_llm_calls,
                thinking_process_summary=thinking_summary,
            )

            self.logger.info(
                "深度思考流程完成",
                total_llm_calls=self.total_llm_calls,
                subtask_count=len(subtask_results),
                has_review=review_result is not None,
                final_answer_length=len(final_answer),
            )

            # 记录性能数据
            self._log_performance_summary(context)

            return result

        except Exception as e:
            self.logger.log_exception("深度思考流程执行失败", e)
            # 返回一个错误结果
            return self._create_error_result(question, e)

    def _create_context(self) -> StageContext:
        """创建阶段执行上下文"""
        return StageContext(
            original_question="",  # 将在各阶段设置
            model=self.model,
            system_instruction=self.system_instruction,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            verbose=self.verbose,
            llm_call_count=0,
        )

    def _execute_plan_stage(self, context: StageContext, question: str) -> Plan:
        """执行规划阶段"""
        # 尝试从缓存获取
        cache_key = generate_cache_key("plan", question)
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            if self.verbose:
                self.logger.debug("从缓存获取规划")
            return cached_result

        # 执行规划
        result = self.planner.execute(
            context,
            question=question,
        )

        if not result.success:
            raise RuntimeError(f"规划阶段失败: {result.error}")

        plan = result.data
        context.llm_call_count += result.llm_calls

        # 存储到缓存
        self.cache_manager.set(cache_key, plan)
        return plan

    def _execute_solve_stage(
        self, context: StageContext, question: str, plan: Plan
    ) -> list[SubtaskResult]:
        """执行解决阶段"""
        subtask_results = []
        for subtask in plan.subtasks:
            result = self.solver.execute(
                context,
                subtask=subtask,
                original_question=question,
                previous_results=subtask_results,
            )

            if not result.success:
                self.logger.warning("子任务执行失败", subtask_id=subtask.id, error=result.error)
                # 继续执行下一个子任务

            subtask_results.append(result.data)
            context.llm_call_count += result.llm_calls

        return subtask_results

    def _execute_synthesize_stage(
        self,
        context: StageContext,
        question: str,
        plan: Plan,
        subtask_results: list[SubtaskResult],
    ) -> str:
        """执行整合阶段"""
        result = self.synthesizer.execute(
            context,
            original_question=question,
            plan=plan,
            subtask_results=subtask_results,
        )

        if not result.success:
            raise RuntimeError(f"整合阶段失败: {result.error}")

        context.llm_call_count += result.llm_calls
        return result.data

    def _execute_review_stage(
        self, context: StageContext, question: str, final_answer: str
    ) -> ReviewResult:
        """执行审查阶段"""
        result = self.reviewer.execute(
            context,
            original_question=question,
            final_answer=final_answer,
        )

        if not result.success:
            self.logger.warning("审查阶段失败", error=result.error)
            # 返回默认审查结果
            return ReviewResult(
                issues_found=[],
                improvement_suggestions=[],
                overall_quality_score=0.7,
                review_notes="审查阶段执行失败",
            )

        context.llm_call_count += result.llm_calls
        return result.data

    def _generate_thinking_summary(self, plan: Plan, subtask_results: list[SubtaskResult]) -> str:
        """生成思考过程摘要"""
        summary_parts = [
            "## 🧠 深度思考过程摘要\n",
            f"**问题澄清:** {plan.clarified_question}\n",
            f"**推理策略:** {plan.reasoning_approach}\n",
            "\n**子任务执行情况:**",
        ]

        for result in subtask_results:
            # 移除截断限制，显示完整结论
            conclusion_display = result.intermediate_conclusion

            summary_parts.append(
                f"\n{result.subtask_id}. {result.description}\n"
                f"   - 可信度: {result.confidence:.0%}\n"
                f"   - 结论: {conclusion_display}"
            )

        return "\n".join(summary_parts)

    def _create_error_result(self, question: str, error: Exception) -> DeepThinkResult:
        """创建错误结果"""
        return DeepThinkResult(
            original_question=question,
            final_answer=f"深度思考过程中出现错误: {error!s}",
            plan=Plan(clarified_question=question, subtasks=[], plan_text=""),
            subtask_results=[],
            total_llm_calls=self.total_llm_calls,
        )

    def _log_performance_summary(self, context: StageContext) -> None:
        """记录性能摘要"""
        # 这里可以添加更多的性能指标
        self.logger.debug(
            "性能摘要",
            total_llm_calls=context.llm_call_count,
            model=self.model,
            max_subtasks=self.max_subtasks,
            enable_review=self.enable_review,
        )

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        return {
            "size": self.cache_manager.size(),
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache_manager.clear()
        self.logger.info("缓存已清空")
