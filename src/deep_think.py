"""
深度思考模块 - 实现多阶段推理和深度研究能力
"""

import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThinkingStage(Enum):
    """深度思考的各个阶段"""

    PLAN = "plan"
    SOLVE = "solve"
    SYNTHESIZE = "synthesize"
    REVIEW = "review"


@dataclass
class Subtask:
    """子任务数据结构"""

    id: int
    description: str
    priority: str = "medium"  # high, medium, low
    dependencies: List[int] = field(default_factory=list)


@dataclass
class Plan:
    """任务规划结果"""

    clarified_question: str
    subtasks: List[Subtask]
    plan_text: str
    reasoning_approach: str = ""


@dataclass
class SubtaskResult:
    """子任务执行结果"""

    subtask_id: int
    description: str
    analysis: str
    intermediate_conclusion: str
    confidence: float  # 0.0 - 1.0
    limitations: List[str] = field(default_factory=list)
    needs_external_info: bool = False  # 是否需要外部信息(预留工具调用)
    suggested_tools: List[str] = field(default_factory=list)  # 建议使用的工具


@dataclass
class ReviewResult:
    """审查结果"""

    issues_found: List[str]
    improvement_suggestions: List[str]
    overall_quality_score: float  # 0.0 - 1.0
    review_notes: str


@dataclass
class DeepThinkResult:
    """深度思考完整结果"""

    original_question: str
    final_answer: str
    plan: Plan
    subtask_results: List[SubtaskResult]
    review: Optional[ReviewResult] = None
    total_llm_calls: int = 0
    thinking_process_summary: str = ""


class PromptTemplates:
    """Prompt模板集合"""

    PLAN_PROMPT = """你是一个专业的问题分析专家。请对以下问题进行深度分析和规划。

**用户问题:**
{question}

**任务要求:**
1. 理解并澄清问题的核心意图
2. 将复杂问题拆解为3-6个可管理的子任务
3. 为每个子任务设定优先级(high/medium/low)
4. 规划合理的推理路径

**输出要求:**
请以JSON格式输出,严格遵循以下结构:
{{
    "clarified_question": "澄清后的问题描述",
    "reasoning_approach": "总体推理策略说明",
    "subtasks": [
        {{
            "id": 1,
            "description": "子任务描述",
            "priority": "high|medium|low",
            "dependencies": []
        }}
    ],
    "plan_text": "整体规划的自然语言描述"
}}

只返回JSON,不要包含其他内容。"""

    SUBTASK_PROMPT = """你是一个专业的研究分析师。请对以下子任务进行深入分析。

**原始问题:** {original_question}

**当前子任务:**
{subtask_description}

**已完成的相关子任务结论:**
{previous_conclusions}

**分析要求:**
1. 深入分析这个子任务
2. 基于已知信息给出中间结论
3. 评估结论的可信度
4. 识别分析的局限性
5. 判断是否需要外部信息(如搜索、数据查询等)

**输出要求:**
请以JSON格式输出:
{{
    "analysis": "详细的分析过程",
    "intermediate_conclusion": "该子任务的结论",
    "confidence": 0.85,
    "limitations": ["局限性1", "局限性2"],
    "needs_external_info": false,
    "suggested_tools": []
}}

只返回JSON,不要包含其他内容。"""

    SYNTHESIZE_PROMPT = """你是一个专业的知识整合专家。请基于所有子任务的结论,生成最终答案。

**原始问题:**
{original_question}

**澄清后的问题:**
{clarified_question}

**推理策略:**
{reasoning_approach}

**所有子任务的结论:**
{all_conclusions}

**整合要求:**
1. 综合所有子任务的结论
2. 形成连贯、完整的最终答案
3. 保持逻辑严密性
4. 标注不确定的部分
5. 使用清晰的结构(如分段、列表等)

**输出要求:**
请以JSON格式输出:
{{
    "final_answer": "结构化的最终答案,使用Markdown格式",
    "synthesis_notes": "整合过程的说明",
    "confidence_areas": {{
        "high_confidence": ["确定性高的结论"],
        "medium_confidence": ["中等确定性的结论"],
        "low_confidence": ["需要进一步验证的结论"]
    }}
}}

只返回JSON,不要包含其他内容。"""

    REVIEW_PROMPT = """你是一个严格的质量审查专家。请对以下答案进行批判性审查。

**原始问题:**
{original_question}

**待审查的答案:**
{final_answer}

**审查要求:**
1. 检查逻辑一致性
2. 识别潜在的错误或遗漏
3. 评估答案的完整性
4. 提出改进建议
5. 给出整体质量评分(0.0-1.0)

**输出要求:**
请以JSON格式输出:
{{
    "issues_found": ["问题1", "问题2"],
    "improvement_suggestions": ["改进建议1", "建议2"],
    "overall_quality_score": 0.85,
    "review_notes": "总体审查意见"
}}

只返回JSON,不要包含其他内容。"""


class DeepThinkOrchestrator:
    """深度思考编排器 - 管理多阶段推理流程"""

    def __init__(
            self,
            api_service,
            model: str,
            max_subtasks: int = 6,
            enable_review: bool = True,
            verbose: bool = True,
            system_instruction: Optional[str] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            max_tokens: Optional[int] = None,
    ):
        """
        初始化深度思考编排器

        Args:
            api_service: MultiProviderAPIService实例
            model: 使用的模型名称
            max_subtasks: 最大子任务数量
            enable_review: 是否启用最终审查
            verbose: 是否输出详细日志
            system_instruction: 系统提示词
            temperature: 温度参数
            top_p: 核采样参数
            max_tokens: 最大token数
        """
        self.api_service = api_service
        self.model = model
        self.max_subtasks = max_subtasks
        self.enable_review = enable_review
        self.verbose = verbose
        self.llm_call_count = 0

        # 模型参数
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        # 添加缓存功能
        self.intermediate_cache = {}
        self.cache_lock = threading.Lock()

    def run(self, question: str) -> DeepThinkResult:
        """
        执行深度思考流程

        Args:
            question: 用户问题

        Returns:
            DeepThinkResult: 完整的思考结果
        """
        logger.info(f"[DEEP THINK] 开始深度思考模式: {question[:50]}...")

        try:
            # 阶段1: 规划
            plan = self._plan(question)
            logger.info(f"[PLAN] 生成了 {len(plan.subtasks)} 个子任务")

            # 阶段2: 逐个解决子任务
            subtask_results = []
            for subtask in plan.subtasks:
                result = self._solve_subtask(subtask, question, subtask_results)
                subtask_results.append(result)
                logger.info(f"[SOLVE] 完成子任务 {subtask.id}: {subtask.description[:30]}...")

            # 阶段3: 整合结果
            final_answer = self._synthesize(question, plan, subtask_results)
            logger.info("[SYNTHESIZE] 生成最终答案")

            # 阶段4: 可选审查
            review_result = None
            if self.enable_review:
                review_result = self._review(question, final_answer)
                logger.info(
                    f"[REVIEW] 审查完成,质量评分: {review_result.overall_quality_score:.2f}"
                )

            # 生成思考过程摘要
            thinking_summary = self._generate_thinking_summary(plan, subtask_results)

            result = DeepThinkResult(
                original_question=question,
                final_answer=final_answer,
                plan=plan,
                subtask_results=subtask_results,
                review=review_result,
                total_llm_calls=self.llm_call_count,
                thinking_process_summary=thinking_summary,
            )

            logger.info(f"[DEEP THINK] 完成,共调用LLM {self.llm_call_count} 次")
            return result

        except Exception as e:
            logger.error(f"[DEEP THINK] 执行失败: {e}")
            # 返回一个错误结果
            return DeepThinkResult(
                original_question=question,
                final_answer=f"深度思考过程中出现错误: {e!s}",
                plan=Plan(clarified_question=question, subtasks=[], plan_text=""),
                subtask_results=[],
                total_llm_calls=self.llm_call_count,
            )

    def _get_cache_key(self, method_name: str, *args, **kwargs):
        """生成缓存键"""
        cache_input = {
            "method": method_name,
            "args": args,
            "kwargs": {k: v for k, v in kwargs.items() if k != "self"},
        }
        cache_str = str(sorted(cache_input.items()))
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_from_cache(self, key):
        """从缓存获取结果"""
        with self.cache_lock:
            return self.intermediate_cache.get(key)

    def _set_to_cache(self, key, value):
        """设置缓存"""
        with self.cache_lock:
            self.intermediate_cache[key] = value

    def _plan(self, question: str) -> Plan:
        """生成任务规划"""
        # 尝试从缓存获取
        cache_key = self._get_cache_key("_plan", question)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            if self.verbose:
                logger.info("[PLAN] 从缓存获取规划")
            return cached_result

        prompt = PromptTemplates.PLAN_PROMPT.format(question=question)
        response = self._call_llm(prompt, stage=ThinkingStage.PLAN)

        try:
            plan_data = self._parse_json_response(response)

            subtasks = [
                Subtask(
                    id=st["id"],
                    description=st["description"],
                    priority=st.get("priority", "medium"),
                    dependencies=st.get("dependencies", []),
                )
                for st in plan_data.get("subtasks", [])[: self.max_subtasks]
            ]

            result = Plan(
                clarified_question=plan_data.get("clarified_question", question),
                subtasks=subtasks,
                plan_text=plan_data.get("plan_text", ""),
                reasoning_approach=plan_data.get("reasoning_approach", ""),
            )

            # 存储到缓存
            self._set_to_cache(cache_key, result)
            return result

        except Exception as e:
            logger.warning(f"[PLAN] JSON解析失败,使用默认规划: {e}")
            # 容错: 创建一个默认的简单规划
            result = Plan(
                clarified_question=question,
                subtasks=[
                    Subtask(id=1, description="深入理解和分析问题", priority="high"),
                    Subtask(id=2, description="探索可能的解决方案", priority="medium"),
                    Subtask(id=3, description="综合评估和总结", priority="medium"),
                ],
                plan_text="由于规划解析失败,使用默认三阶段分析流程",
            )

            # 存储到缓存
            self._set_to_cache(cache_key, result)
            return result

    def _solve_subtask(
            self, subtask: Subtask, original_question: str, previous_results: List[SubtaskResult]
    ) -> SubtaskResult:
        """解决单个子任务"""
        # 构建之前的结论上下文
        previous_conclusions = (
            "\n".join(
                [f"- 子任务{r.subtask_id}: {r.intermediate_conclusion}" for r in previous_results]
            )
            if previous_results
            else "暂无"
        )

        prompt = PromptTemplates.SUBTASK_PROMPT.format(
            original_question=original_question,
            subtask_description=subtask.description,
            previous_conclusions=previous_conclusions,
        )

        response = self._call_llm(prompt, stage=ThinkingStage.SOLVE)

        try:
            result_data = self._parse_json_response(response)

            return SubtaskResult(
                subtask_id=subtask.id,
                description=subtask.description,
                analysis=result_data.get("analysis", response),
                intermediate_conclusion=result_data.get("intermediate_conclusion", ""),
                confidence=float(result_data.get("confidence", 0.7)),
                limitations=result_data.get("limitations", []),
                needs_external_info=result_data.get("needs_external_info", False),
                suggested_tools=result_data.get("suggested_tools", []),
            )

        except Exception as e:
            logger.warning(f"[SOLVE] 子任务 {subtask.id} JSON解析失败: {e}")
            # 容错: 使用原始响应作为分析结果
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
                limitations=["JSON解析失败,使用原始响应"],
            )

    def _synthesize(
            self, original_question: str, plan: Plan, subtask_results: List[SubtaskResult]
    ) -> str:
        """整合所有子任务结果"""
        all_conclusions = "\n\n".join(
            [
                f"**子任务 {r.subtask_id}: {r.description}**\n"
                f"结论: {r.intermediate_conclusion}\n"
                f"可信度: {r.confidence:.0%}\n"
                f"局限性: {', '.join(r.limitations) if r.limitations else '无'}"
                for r in subtask_results
            ]
        )

        prompt = PromptTemplates.SYNTHESIZE_PROMPT.format(
            original_question=original_question,
            clarified_question=plan.clarified_question,
            reasoning_approach=plan.reasoning_approach,
            all_conclusions=all_conclusions,
        )

        response = self._call_llm(prompt, stage=ThinkingStage.SYNTHESIZE)

        try:
            synthesis_data = self._parse_json_response(response)
            final_answer = synthesis_data.get("final_answer", response)

            # 添加整合说明(可选)
            if "synthesis_notes" in synthesis_data:
                final_answer += f"\n\n---\n**整合说明:** {synthesis_data['synthesis_notes']}"

            return final_answer

        except Exception as e:
            logger.warning(f"[SYNTHESIZE] JSON解析失败: {e}")
            # 容错: 直接使用响应
            # 确保响应不为空
            if response and response.strip():
                return response
            else:
                # 如果响应为空，返回基于子任务结论的回退答案
                logger.warning("[SYNTHESIZE] 响应为空，使用回退答案")
                fallback_parts = ["基于上述分析，综合结论如下：\n"]
                for r in subtask_results:
                    fallback_parts.append(f"- {r.description}: {r.intermediate_conclusion[:100]}")
                return "\n".join(fallback_parts)

    def _review(self, original_question: str, final_answer: str) -> ReviewResult:
        """审查最终答案"""
        prompt = PromptTemplates.REVIEW_PROMPT.format(
            original_question=original_question, final_answer=final_answer
        )

        response = self._call_llm(prompt, stage=ThinkingStage.REVIEW)

        try:
            review_data = self._parse_json_response(response)

            return ReviewResult(
                issues_found=review_data.get("issues_found", []),
                improvement_suggestions=review_data.get("improvement_suggestions", []),
                overall_quality_score=float(review_data.get("overall_quality_score", 0.75)),
                review_notes=review_data.get("review_notes", ""),
            )

        except Exception as e:
            logger.warning(f"[REVIEW] JSON解析失败: {e}")
            # 容错: 返回默认审查结果
            return ReviewResult(
                issues_found=[],
                improvement_suggestions=[],
                overall_quality_score=0.7,
                review_notes="审查数据解析失败",
            )

    def _call_llm(self, prompt: str, stage: ThinkingStage) -> str:
        """调用LLM"""
        self.llm_call_count += 1

        if self.verbose:
            logger.info(f"[LLM CALL #{self.llm_call_count}] Stage: {stage.value}")

        messages = [{"role": "user", "content": prompt}]

        response = self.api_service.chat_completion(
            messages=messages,
            model=self.model,
            system_instruction=self.system_instruction,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=False,  # 深度思考模式必须使用非流式传输
        )

        # 确保返回的是字符串类型
        # 如果 API 返回了生成器（不应该发生，但做防护），将其完全消费
        if hasattr(response, '__iter__') and not isinstance(response, (str, bytes)):
            if self.verbose:
                logger.warning("[LLM CALL] 检测到生成器响应，正在转换为字符串...")
            try:
                response = ''.join(str(chunk) for chunk in response)
            except Exception as e:
                error_msg = f"无法将生成器转换为字符串: {e}"
                logger.error(f"[LLM CALL] {error_msg}")
                raise TypeError(error_msg)

        # 最终类型检查
        if not isinstance(response, str):
            raise TypeError(f"API 响应必须是字符串，而不是 {type(response).__name__}")

        # 调试日志：显示响应的前200个字符
        if self.verbose:
            preview = response[:200].replace('\n', ' ')
            logger.info(f"[LLM RESPONSE] {preview}{'...' if len(response) > 200 else ''}")

        return response

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应,支持容错处理"""
        # 防护：如果收到生成器对象，将其转换为字符串
        if hasattr(response, '__iter__') and not isinstance(response, (str, bytes)):
            try:
                response = ''.join(response)
            except Exception as e:
                raise TypeError(f"响应必须是字符串，而不是 {type(response).__name__}: {e}")

        # 确保是字符串类型
        if not isinstance(response, str):
            raise TypeError(f"响应必须是字符串，而不是 {type(response).__name__}")

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON代码块
        if "```json" in response:
            json_block = response.split("```json")[1].split("```")[0].strip()
            try:
                return json.loads(json_block)
            except json.JSONDecodeError:
                pass

        # 尝试查找花括号内的内容
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass

        # 如果都失败,抛出异常
        raise ValueError(f"无法解析JSON响应: {response[:100]}...")

    def _generate_thinking_summary(self, plan: Plan, subtask_results: List[SubtaskResult]) -> str:
        """生成思考过程摘要"""
        summary_parts = [
            "## 🧠 深度思考过程摘要\n",
            f"**问题澄清:** {plan.clarified_question}\n",
            f"**推理策略:** {plan.reasoning_approach}\n",
            "\n**子任务执行情况:**",
        ]

        for result in subtask_results:
            # 智能截断：只在超过100字符时才添加省略号
            conclusion = result.intermediate_conclusion
            if len(conclusion) > 100:
                conclusion_display = conclusion[:100] + "..."
            else:
                conclusion_display = conclusion

            summary_parts.append(
                f"\n{result.subtask_id}. {result.description}\n"
                f"   - 可信度: {result.confidence:.0%}\n"
                f"   - 结论: {conclusion_display}"
            )

        return "\n".join(summary_parts)


def format_deep_think_result(result: DeepThinkResult, include_process: bool = True) -> str:
    """
    格式化深度思考结果为用户友好的输出

    Args:
        result: DeepThinkResult实例
        include_process: 是否包含思考过程详情

    Returns:
        str: 格式化的Markdown文本
    """
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
