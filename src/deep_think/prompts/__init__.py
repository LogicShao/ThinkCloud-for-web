"""
深度思考提示模板模块
包含提示模板的定义和管理
"""

from .base import BasePromptTemplate
from .manager import PromptTemplateManager
from .templates import (
    PlanPromptTemplate,
    ReviewPromptTemplate,
    SubtaskPromptTemplate,
    SynthesizePromptTemplate,
)

__all__ = [
    "BasePromptTemplate",
    "PlanPromptTemplate",
    "SubtaskPromptTemplate",
    "SynthesizePromptTemplate",
    "ReviewPromptTemplate",
    "PromptTemplateManager",
]
