"""
提示模板基类
遵循开闭原则，支持扩展新的提示模板
"""

from abc import abstractmethod
from typing import Any, Dict

from ..core.interfaces import IPromptTemplate
from ..core.models import ThinkingStage


class BasePromptTemplate(IPromptTemplate):
    """提示模板基类"""

    def __init__(self, name: str, stage: ThinkingStage, template: str):
        """
        初始化提示模板

        Args:
            name: 模板名称
            stage: 对应的阶段
            template: 模板字符串
        """
        self._name = name
        self._stage = stage
        self._template = template

    def get_name(self) -> str:
        """获取模板名称"""
        return self._name

    def get_stage(self) -> ThinkingStage:
        """获取模板对应的阶段"""
        return self._stage

    def format(self, **kwargs) -> str:
        """格式化模板"""
        try:
            return self._template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板参数缺失: {e}")
        except Exception as e:
            raise ValueError(f"模板格式化失败: {e}")

    def get_required_params(self) -> list:
        """获取模板所需的参数列表"""
        # 从模板字符串中提取所有 {param} 格式的参数
        import re
        params = re.findall(r'\{(\w+)\}', self._template)
        return list(set(params))  # 去重
