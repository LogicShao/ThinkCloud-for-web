"""
提示模板管理器
负责管理所有提示模板的注册和获取
"""

from typing import Dict, Optional

from ..core.interfaces import IPromptTemplate
from ..core.models import ThinkingStage
from .templates import (
    PlanPromptTemplate,
    ReviewPromptTemplate,
    SubtaskPromptTemplate,
    SynthesizePromptTemplate,
)


class PromptTemplateManager:
    """提示模板管理器"""

    def __init__(self):
        self._templates: Dict[str, IPromptTemplate] = {}
        self._stage_templates: Dict[ThinkingStage, IPromptTemplate] = {}
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """初始化默认模板"""
        default_templates = [
            PlanPromptTemplate(),
            SubtaskPromptTemplate(),
            SynthesizePromptTemplate(),
            ReviewPromptTemplate(),
        ]

        for template in default_templates:
            self.register_template(template)

    def register_template(self, template: IPromptTemplate) -> None:
        """注册模板"""
        name = template.get_name()
        stage = template.get_stage()

        self._templates[name] = template
        self._stage_templates[stage] = template

    def get_template(self, name: str) -> Optional[IPromptTemplate]:
        """根据名称获取模板"""
        return self._templates.get(name)

    def get_template_by_stage(self, stage: ThinkingStage) -> Optional[IPromptTemplate]:
        """根据阶段获取模板"""
        return self._stage_templates.get(stage)

    def get_all_templates(self) -> Dict[str, IPromptTemplate]:
        """获取所有模板"""
        return self._templates.copy()

    def get_all_stage_templates(self) -> Dict[ThinkingStage, IPromptTemplate]:
        """获取所有阶段模板"""
        return self._stage_templates.copy()

    def has_template(self, name: str) -> bool:
        """检查是否存在指定名称的模板"""
        return name in self._templates

    def has_stage_template(self, stage: ThinkingStage) -> bool:
        """检查是否存在指定阶段的模板"""
        return stage in self._stage_templates

    def clear_templates(self) -> None:
        """清空所有模板"""
        self._templates.clear()
        self._stage_templates.clear()
