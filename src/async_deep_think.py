"""
异步深度思考编排器 - 支持并行任务处理
优化深度思考模式的性能,支持子任务并行执行
"""

import asyncio
from typing import Any, Dict, List, Optional

from .async_api_service import AsyncAPIService
from .deep_think.core.interfaces import ILLMService
from .deep_think.core.models import DeepThinkResult, Plan, ReviewResult, SubtaskResult
from .deep_think.prompts.manager import PromptTemplateManager
from .deep_think.stages import (
    PlannerStageProcessor,
    ReviewerStageProcessor,
    SolverStageProcessor,
    SynthesizerStageProcessor,
)
from .deep_think.utils import DefaultJSONParser, MemoryCacheManager, generate_cache_key


class AsyncLLMServiceAdapter(ILLMService):
    """异步LLM服务适配器,将AsyncAPIService适配为ILLMService接口"""

    def __init__(self, async_service: AsyncAPIService):
        self.async_service = async_service
        self._loop = None

    def chat_completion(self, messages, model, **kwargs) -> Any:
        """
        同步调用异步API服务
        这个方法在同步上下文中被调用,需要创建事件循环
        """
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # 运行异步任务
        return loop.run_until_complete(
            self.async_service.chat_completion(messages=messages, model=model, **kwargs)
        )


class AsyncDeepThinkOrchestrator:
    """
    异步深度思考编排器
    支持子任务并行执行,提升性能
    """

    def __init__(
        self,
        async_api_service: AsyncAPIService,
        model: str,
        max_subtasks: int = 6,
        enable_review: bool = True,
        enable_web_search: bool = False,
        verbose: bool = True,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_parallel_tasks: int = 3,
    ):
        """
        初始化异步深度思考编排器

        Args:
            async_api_service: 异步API服务
            model: 模型名称
            max_subtasks: 最大子任务数
            enable_review: 是否启用审查
            enable_web_search: 是否启用网络搜索
            verbose: 是否输出详细日志
            system_instruction: 系统提示词
            temperature: 温度参数
            top_p: Top P参数
            max_tokens: 最大Token数
            max_parallel_tasks: 最大并行子任务数
        """
        self.async_api_service = async_api_service
        self.model = model
        self.max_subtasks = max_subtasks
        self.enable_review = enable_review
        self.enable_web_search = enable_web_search
        self.verbose = verbose
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.max_parallel_tasks = max_parallel_tasks

        # 初始化组件
        self.json_parser = DefaultJSONParser()
        self.cache_manager = MemoryCacheManager()
        self.prompt_manager = PromptTemplateManager()

        # 创建同步适配器用于现有的阶段处理器
        self.sync_adapter = AsyncLLMServiceAdapter(async_api_service)

        # 初始化阶段处理器
        self._initialize_stage_processors()

        # LLM调用计数
        self.llm_call_count = 0

    def _initialize_stage_processors(self):
        """初始化阶段处理器"""
        from .deep_think.core.models import ThinkingStage

        # 规划阶段处理器
        self.planner = PlannerStageProcessor(
            llm_service=self.sync_adapter,
            json_parser=self.json_parser,
            prompt_template=self.prompt_manager.get_template_by_stage(ThinkingStage.PLAN),
            max_subtasks=self.max_subtasks,
            verbose=self.verbose,
        )

        # 解决阶段处理器
        self.solver = SolverStageProcessor(
            llm_service=self.sync_adapter,
            json_parser=self.json_parser,
            prompt_template=self.prompt_manager.get_template_by_stage(ThinkingStage.SOLVE),
            verbose=self.verbose,
        )

        # 整合阶段处理器
        self.synthesizer = SynthesizerStageProcessor(
            llm_service=self.sync_adapter,
            json_parser=self.json_parser,
            prompt_template=self.prompt_manager.get_template_by_stage(ThinkingStage.SYNTHESIZE),
            verbose=self.verbose,
        )

        # 审查阶段处理器
        self.reviewer = ReviewerStageProcessor(
            llm_service=self.sync_adapter,
            json_parser=self.json_parser,
            prompt_template=self.prompt_manager.get_template_by_stage(ThinkingStage.REVIEW),
            verbose=self.verbose,
        )

    async def run(self, question: str, **kwargs) -> DeepThinkResult:
        """
        异步运行深度思考流程

        Args:
            question: 用户问题
            **kwargs: 其他参数

        Returns:
            DeepThinkResult: 深度思考结果
        """
        if self.verbose:
            print("\n" + "=" * 80)
            print("[DEEP THINK] 开始深度思考模式（异步优化版本）")
            print("=" * 80 + "\n")

        # 1. 规划阶段
        plan = await self._execute_plan_stage_async(question)
        self.llm_call_count += 1

        # 2. 解决阶段(并行执行)
        subtask_results = await self._execute_solve_stage_parallel(question, plan)
        self.llm_call_count += len(plan.subtasks)

        # 3. 整合阶段
        final_answer = await self._execute_synthesize_stage_async(question, plan, subtask_results)
        self.llm_call_count += 1

        # 4. 审查阶段(可选)
        review_result = None
        if self.enable_review:
            review_result = await self._execute_review_stage_async(question, final_answer)
            self.llm_call_count += 1

        # 5. 返回完整结果
        result = DeepThinkResult(
            original_question=question,
            final_answer=final_answer,
            plan=plan,
            subtask_results=subtask_results,
            review=review_result,
            total_llm_calls=self.llm_call_count,
            thinking_process_summary=self._generate_process_summary(
                plan, subtask_results, review_result
            ),
        )

        if self.verbose:
            print("\n" + "=" * 80)
            print(f"[DEEP THINK] 深度思考完成！总LLM调用次数: {self.llm_call_count}")
            print("=" * 80 + "\n")

        return result

    async def _execute_plan_stage_async(self, question: str) -> Plan:
        """异步执行规划阶段"""
        if self.verbose:
            print("[STAGE 1/4] 规划阶段 - 澄清问题并拆解子任务...")

        # 使用事件循环运行同步代码
        loop = asyncio.get_event_loop()
        plan = await loop.run_in_executor(
            None,
            lambda: self.planner.execute(
                context=self._create_context(),
                question=question,
                model=self.model,
                system_instruction=self.system_instruction,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
            ).data,
        )

        if self.verbose:
            print(f"[PLAN] 澄清后的问题: {plan.clarified_question}")
            print(f"[PLAN] 拆解为 {len(plan.subtasks)} 个子任务")
            for i, subtask in enumerate(plan.subtasks, 1):
                print(f"  {i}. {subtask.description}")

        return plan

    async def _execute_solve_stage_parallel(self, question: str, plan: Plan) -> List[SubtaskResult]:
        """
        并行执行解决阶段
        使用信号量控制并发数
        """
        if self.verbose:
            print(
                f"\n[STAGE 2/4] 解决阶段 - 并行分析子任务(最多{self.max_parallel_tasks}个并行)..."
            )

        subtask_results = []
        semaphore = asyncio.Semaphore(self.max_parallel_tasks)

        async def solve_subtask_with_semaphore(subtask, index, previous_results):
            """带信号量控制的子任务求解"""
            async with semaphore:
                if self.verbose:
                    print(
                        f"[SOLVE {index + 1}/{len(plan.subtasks)}] 开始分析: {subtask.description}"
                    )

                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.solver.execute(
                        context=self._create_context(),
                        question=question,
                        clarified_question=plan.clarified_question,
                        subtask=subtask,
                        previous_results=previous_results,
                        model=self.model,
                        system_instruction=self.system_instruction,
                        temperature=self.temperature,
                        top_p=self.top_p,
                        max_tokens=self.max_tokens,
                    ).data,
                )

                if self.verbose:
                    print(
                        f"[SOLVE {index + 1}/{len(plan.subtasks)}] 完成 - "
                        f"置信度: {result.confidence:.1%}, "
                        f"局限性: {len(result.limitations)}"
                    )

                return result

        # 策略: 依赖子任务串行执行,独立子任务并行执行
        # 这里简化处理,按批次并行执行
        batch_size = self.max_parallel_tasks

        for i in range(0, len(plan.subtasks), batch_size):
            batch_subtasks = plan.subtasks[i : i + batch_size]
            batch_tasks = []

            for j, subtask in enumerate(batch_subtasks):
                task = solve_subtask_with_semaphore(subtask, i + j, subtask_results.copy())
                batch_tasks.append(task)

            # 并行执行当前批次
            batch_results = await asyncio.gather(*batch_tasks)
            subtask_results.extend(batch_results)

        return subtask_results

    async def _execute_synthesize_stage_async(
        self, question: str, plan: Plan, subtask_results: List[SubtaskResult]
    ) -> str:
        """异步执行整合阶段"""
        if self.verbose:
            print("\n[STAGE 3/4] 整合阶段 - 综合所有子任务结论...")

        loop = asyncio.get_event_loop()
        final_answer = await loop.run_in_executor(
            None,
            lambda: self.synthesizer.execute(
                context=self._create_context(),
                question=question,
                clarified_question=plan.clarified_question,
                subtask_results=subtask_results,
                model=self.model,
                system_instruction=self.system_instruction,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
            ).data,
        )

        if self.verbose:
            print(f"[SYNTHESIZE] 生成最终答案，长度: {len(final_answer)} 字符")

        return final_answer

    async def _execute_review_stage_async(self, question: str, final_answer: str) -> ReviewResult:
        """异步执行审查阶段"""
        if self.verbose:
            print("\n[STAGE 4/4] 审查阶段 - 批判性审查答案质量...")

        loop = asyncio.get_event_loop()
        review_result = await loop.run_in_executor(
            None,
            lambda: self.reviewer.execute(
                context=self._create_context(),
                question=question,
                final_answer=final_answer,
                model=self.model,
                system_instruction=self.system_instruction,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
            ).data,
        )

        if self.verbose:
            print(f"[REVIEW] 质量评分: {review_result.quality_score}/10")
            print(f"[REVIEW] 识别出 {len(review_result.potential_issues)} 个潜在问题")
            print(f"[REVIEW] 提供 {len(review_result.improvement_suggestions)} 条改进建议")

        return review_result

    def _create_context(self) -> Dict[str, Any]:
        """创建执行上下文"""
        from .deep_think.core.models import StageContext

        return StageContext(
            llm_call_count=self.llm_call_count, cache_manager=self.cache_manager, metadata={}
        )

    def _generate_process_summary(
        self, plan: Plan, subtask_results: List[SubtaskResult], review: Optional[ReviewResult]
    ) -> str:
        """生成思考过程摘要"""
        summary_parts = []

        summary_parts.append(f"问题澄清: {plan.clarified_question}")
        summary_parts.append(f"\n任务拆解: {len(plan.subtasks)} 个子任务")

        summary_parts.append("\n子任务分析:")
        for i, result in enumerate(subtask_results, 1):
            summary_parts.append(f"  {i}. {result.description} (置信度: {result.confidence:.1%})")

        if review:
            summary_parts.append(f"\n质量审查: {review.quality_score}/10分")

        summary_parts.append(f"\n总LLM调用: {self.llm_call_count} 次")

        return "\n".join(summary_parts)
