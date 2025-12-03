"""
深度思考核心接口定义
遵循接口隔离原则，定义小而专一的接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .models import (
    DeepThinkResult,
    Plan,
    StageContext,
    StageResult,
    Subtask,
    SubtaskResult,
    ThinkingStage,
)


class ILLMService(ABC):
    """LLM服务接口 - 依赖倒置原则"""

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> Any:
        """调用LLM聊天完成API"""
        pass


class IStageProcessor(ABC):
    """阶段处理器接口 - 开闭原则"""

    @abstractmethod
    def get_stage(self) -> ThinkingStage:
        """获取阶段类型"""
        pass

    @abstractmethod
    def execute(self, context: StageContext, **kwargs) -> StageResult:
        """执行阶段处理"""
        pass


class IPromptTemplate(ABC):
    """提示模板接口"""

    @abstractmethod
    def get_name(self) -> str:
        """获取模板名称"""
        pass

    @abstractmethod
    def get_stage(self) -> ThinkingStage:
        """获取模板对应的阶段"""
        pass

    @abstractmethod
    def format(self, **kwargs) -> str:
        """格式化模板"""
        pass


class IResultFormatter(ABC):
    """结果格式化接口"""

    @abstractmethod
    def format(self, result: DeepThinkResult, **kwargs) -> str:
        """格式化深度思考结果"""
        pass


class IOrchestrator(ABC):
    """编排器接口"""

    @abstractmethod
    def run(self, question: str, **kwargs) -> DeepThinkResult:
        """执行深度思考流程"""
        pass


class IJSONParser(ABC):
    """JSON解析器接口"""

    @abstractmethod
    def parse(self, response: str) -> Dict[str, Any]:
        """解析JSON响应，支持容错处理"""
        pass


class ICacheManager(ABC):
    """缓存管理器接口"""

    @abstractmethod
    def get(self, key: str) -> Any:
        """获取缓存值"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
