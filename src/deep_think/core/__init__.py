"""
深度思考核心模块
包含数据模型和接口定义
"""

from .interfaces import (
    ICacheManager,
    IJSONParser,
    ILLMService,
    IOrchestrator,
    IPromptTemplate,
    IResultFormatter,
    IStageProcessor,
)
from .models import (
    DeepThinkResult,
    Plan,
    ReviewResult,
    StageContext,
    StageResult,
    Subtask,
    SubtaskResult,
    ThinkingStage,
)

__all__ = [
    # 接口
    "ILLMService",
    "IStageProcessor",
    "IPromptTemplate",
    "IResultFormatter",
    "IOrchestrator",
    "IJSONParser",
    "ICacheManager",
    # 数据模型
    "ThinkingStage",
    "Subtask",
    "Plan",
    "SubtaskResult",
    "ReviewResult",
    "DeepThinkResult",
    "StageContext",
    "StageResult",
]
