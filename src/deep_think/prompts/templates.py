"""
深度思考提示模板集合
包含所有阶段的提示模板
"""

from ..core.models import ThinkingStage
from .base import BasePromptTemplate


class PlanPromptTemplate(BasePromptTemplate):
    """规划阶段提示模板"""

    def __init__(self):
        template = """你是一个专业的问题分析专家。请对以下问题进行深度分析和规划。

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
        super().__init__("plan_prompt", ThinkingStage.PLAN, template)


class SubtaskPromptTemplate(BasePromptTemplate):
    """子任务分析提示模板"""

    def __init__(self):
        template = """你是一个专业的研究分析师。请对以下子任务进行深入分析。

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
        super().__init__("subtask_prompt", ThinkingStage.SOLVE, template)


class SynthesizePromptTemplate(BasePromptTemplate):
    """整合阶段提示模板"""

    def __init__(self):
        template = """你是一个专业的知识整合专家。请基于所有子任务的结论,生成最终答案。

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
        super().__init__("synthesize_prompt", ThinkingStage.SYNTHESIZE, template)


class ReviewPromptTemplate(BasePromptTemplate):
    """审查阶段提示模板"""

    def __init__(self):
        template = """你是一个严格的质量审查专家。请对以下答案进行批判性审查。

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
        super().__init__("review_prompt", ThinkingStage.REVIEW, template)
