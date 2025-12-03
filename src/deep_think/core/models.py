"""
深度思考核心数据模型定义
遵循单一职责原则，只包含数据结构定义
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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


@dataclass
class StageContext:
    """阶段执行上下文"""

    original_question: str
    model: str
    system_instruction: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    verbose: bool = True
    llm_call_count: int = 0


@dataclass
class StageResult:
    """阶段执行结果基类"""

    stage: ThinkingStage
    success: bool
    data: Any
    error: Optional[str] = None
    llm_calls: int = 0
