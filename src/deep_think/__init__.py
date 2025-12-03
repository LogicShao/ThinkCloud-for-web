"""
深度思考模块
多阶段推理和深度研究能力实现
"""

from .core import *
from .formatter import DeepThinkResultFormatter, format_deep_think_result
from .orchestrator import DeepThinkOrchestrator
from .utils import DefaultJSONParser, MemoryCacheManager, generate_cache_key

__all__ = [
    # 核心接口和模型
    "ThinkingStage",
    "Subtask",
    "Plan",
    "SubtaskResult",
    "ReviewResult",
    "DeepThinkResult",
    "StageContext",
    "StageResult",
    # 编排器
    "DeepThinkOrchestrator",
    # 格式化工具
    "DeepThinkResultFormatter",
    "format_deep_think_result",
    # 工具类
    "DefaultJSONParser",
    "MemoryCacheManager",
    "generate_cache_key",
]

# 保持向后兼容性
# 旧代码中的 from src.deep_think import DeepThinkOrchestrator, format_deep_think_result 仍然有效
