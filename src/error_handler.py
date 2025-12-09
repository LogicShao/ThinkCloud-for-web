"""
全局错误处理器 - 统一处理和格式化所有错误
支持提供商特定错误处理、错误分类、重试策略
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type


class ErrorCategory(Enum):
    """错误类别"""

    NETWORK = "network"  # 网络错误
    AUTHENTICATION = "authentication"  # 认证错误
    RATE_LIMIT = "rate_limit"  # 速率限制
    INVALID_REQUEST = "invalid_request"  # 无效请求
    MODEL_ERROR = "model_error"  # 模型错误
    TIMEOUT = "timeout"  # 超时
    CANCELLED = "cancelled"  # 用户取消
    UNKNOWN = "unknown"  # 未知错误


class ErrorSeverity(Enum):
    """错误严重程度"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重错误


@dataclass
class ErrorContext:
    """错误上下文信息"""

    category: ErrorCategory
    severity: ErrorSeverity
    provider: Optional[str] = None
    model: Optional[str] = None
    error_code: Optional[str] = None
    original_error: Optional[Exception] = None
    timestamp: datetime = None
    retry_after: Optional[int] = None  # 重试等待时间(秒)
    is_retryable: bool = False  # 是否可重试

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class FormattedError:
    """格式化的错误信息"""

    message: str  # 用户友好的错误消息
    context: ErrorContext  # 错误上下文
    suggestion: Optional[str] = None  # 解决建议
    technical_details: Optional[str] = None  # 技术细节

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message": self.message,
            "category": self.context.category.value,
            "severity": self.context.severity.value,
            "provider": self.context.provider,
            "model": self.context.model,
            "error_code": self.context.error_code,
            "timestamp": self.context.timestamp.isoformat(),
            "retry_after": self.context.retry_after,
            "is_retryable": self.context.is_retryable,
            "suggestion": self.suggestion,
            "technical_details": self.technical_details,
        }

    def to_user_message(self) -> str:
        """生成用户友好的错误消息"""
        parts = [f"❌ **错误**: {self.message}"]

        if self.context.provider:
            parts.append(f"\n📍 **提供商**: {self.context.provider}")

        if self.context.model:
            parts.append(f"\n🤖 **模型**: {self.context.model}")

        if self.suggestion:
            parts.append(f"\n💡 **建议**: {self.suggestion}")

        if self.context.is_retryable and self.context.retry_after:
            parts.append(f"\n⏱️ **重试**: 请等待 {self.context.retry_after} 秒后重试")

        if self.technical_details:
            parts.append(
                f"\n\n<details>\n<summary>技术细节</summary>\n\n```\n{self.technical_details}\n```\n</details>"
            )

        return "".join(parts)


class ProviderErrorParser:
    """提供商特定错误解析器"""

    @staticmethod
    def parse_openai_error(error: Exception) -> ErrorContext:
        """解析OpenAI错误"""
        error_str = str(error)

        # 认证错误
        if "authentication" in error_str.lower() or "api key" in error_str.lower():
            return ErrorContext(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.ERROR,
                provider="openai",
                original_error=error,
                is_retryable=False,
            )

        # 速率限制
        if "rate limit" in error_str.lower():
            retry_after = ProviderErrorParser._extract_retry_after(error_str)
            return ErrorContext(
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.WARNING,
                provider="openai",
                original_error=error,
                retry_after=retry_after,
                is_retryable=True,
            )

        # 无效请求
        if "invalid" in error_str.lower() or "bad request" in error_str.lower():
            return ErrorContext(
                category=ErrorCategory.INVALID_REQUEST,
                severity=ErrorSeverity.ERROR,
                provider="openai",
                original_error=error,
                is_retryable=False,
            )

        # 模型错误
        if "model" in error_str.lower():
            return ErrorContext(
                category=ErrorCategory.MODEL_ERROR,
                severity=ErrorSeverity.ERROR,
                provider="openai",
                original_error=error,
                is_retryable=False,
            )

        # 网络错误
        if "connection" in error_str.lower() or "timeout" in error_str.lower():
            return ErrorContext(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.WARNING,
                provider="openai",
                original_error=error,
                is_retryable=True,
            )

        return ErrorContext(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            provider="openai",
            original_error=error,
            is_retryable=False,
        )

    @staticmethod
    def parse_deepseek_error(error: Exception) -> ErrorContext:
        """解析DeepSeek错误"""
        error_str = str(error)

        # DeepSeek使用OpenAI兼容接口,错误格式类似
        context = ProviderErrorParser.parse_openai_error(error)
        context.provider = "deepseek"
        return context

    @staticmethod
    def parse_cerebras_error(error: Exception) -> ErrorContext:
        """解析Cerebras错误"""
        error_str = str(error)

        # 认证错误
        if "invalid api key" in error_str.lower() or "unauthorized" in error_str.lower():
            return ErrorContext(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.ERROR,
                provider="cerebras",
                original_error=error,
                is_retryable=False,
            )

        # 速率限制
        if "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
            return ErrorContext(
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.WARNING,
                provider="cerebras",
                original_error=error,
                retry_after=60,
                is_retryable=True,
            )

        # 网络错误
        if "connection" in error_str.lower():
            return ErrorContext(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.WARNING,
                provider="cerebras",
                original_error=error,
                is_retryable=True,
            )

        return ErrorContext(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            provider="cerebras",
            original_error=error,
            is_retryable=False,
        )

    @staticmethod
    def parse_dashscope_error(error: Exception) -> ErrorContext:
        """解析DashScope(通义千问)错误"""
        error_str = str(error)

        # 认证错误
        if "invalid api-key" in error_str.lower() or "InvalidApiKey" in error_str:
            return ErrorContext(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.ERROR,
                provider="dashscope",
                original_error=error,
                is_retryable=False,
            )

        # 限流错误
        if "Throttling" in error_str or "流控" in error_str:
            return ErrorContext(
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.WARNING,
                provider="dashscope",
                original_error=error,
                retry_after=10,
                is_retryable=True,
            )

        # 参数错误
        if "InvalidParameter" in error_str:
            return ErrorContext(
                category=ErrorCategory.INVALID_REQUEST,
                severity=ErrorSeverity.ERROR,
                provider="dashscope",
                original_error=error,
                is_retryable=False,
            )

        return ErrorContext(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            provider="dashscope",
            original_error=error,
            is_retryable=False,
        )

    @staticmethod
    def parse_kimi_error(error: Exception) -> ErrorContext:
        """解析Kimi(月之暗面)错误"""
        error_str = str(error)

        # Kimi使用OpenAI兼容接口,错误格式类似
        context = ProviderErrorParser.parse_openai_error(error)
        context.provider = "kimi"
        return context

    @staticmethod
    def _extract_retry_after(error_str: str) -> Optional[int]:
        """从错误消息中提取重试等待时间"""
        # 尝试匹配 "retry after X seconds"
        match = re.search(r"retry after (\d+)", error_str, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # 尝试匹配 "wait X seconds"
        match = re.search(r"wait (\d+)", error_str, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # 默认返回60秒
        return 60


class GlobalErrorHandler:
    """全局错误处理器"""

    # 提供商错误解析器映射
    _provider_parsers: Dict[str, Callable[[Exception], ErrorContext]] = {
        "openai": ProviderErrorParser.parse_openai_error,
        "deepseek": ProviderErrorParser.parse_deepseek_error,
        "cerebras": ProviderErrorParser.parse_cerebras_error,
        "dashscope": ProviderErrorParser.parse_dashscope_error,
        "kimi": ProviderErrorParser.parse_kimi_error,
    }

    # 错误类别对应的用户消息模板
    _category_messages = {
        ErrorCategory.NETWORK: "网络连接失败,请检查网络状态",
        ErrorCategory.AUTHENTICATION: "API密钥验证失败",
        ErrorCategory.RATE_LIMIT: "请求频率超出限制",
        ErrorCategory.INVALID_REQUEST: "请求参数无效",
        ErrorCategory.MODEL_ERROR: "模型调用错误",
        ErrorCategory.TIMEOUT: "请求超时",
        ErrorCategory.CANCELLED: "请求已被取消",
        ErrorCategory.UNKNOWN: "发生未知错误",
    }

    # 错误类别对应的建议
    _category_suggestions = {
        ErrorCategory.NETWORK: "请检查网络连接后重试",
        ErrorCategory.AUTHENTICATION: "请检查.env文件中的API密钥配置是否正确",
        ErrorCategory.RATE_LIMIT: "请稍后重试,或升级API套餐",
        ErrorCategory.INVALID_REQUEST: "请检查模型参数配置(温度、tokens等)",
        ErrorCategory.MODEL_ERROR: "请尝试切换到其他模型或提供商",
        ErrorCategory.TIMEOUT: "请减小max_tokens参数或增加timeout设置",
        ErrorCategory.CANCELLED: "操作已取消,可以重新开始",
        ErrorCategory.UNKNOWN: "请查看技术细节或联系技术支持",
    }

    def __init__(self, enable_logging: bool = True):
        """
        初始化全局错误处理器

        Args:
            enable_logging: 是否启用日志记录
        """
        self.enable_logging = enable_logging
        if enable_logging:
            logging.basicConfig(
                level=logging.INFO,
                format="[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        self.logger = logging.getLogger(__name__)

    def handle_error(
        self,
        error: Exception,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        operation: str = "API调用",
    ) -> FormattedError:
        """
        处理错误并返回格式化的错误信息

        Args:
            error: 原始异常
            provider: 提供商名称
            model: 模型名称
            operation: 操作描述

        Returns:
            FormattedError: 格式化的错误对象
        """
        # 解析错误上下文
        context = self._parse_error(error, provider)

        # 补充模型信息
        if model:
            context.model = model

        # 生成用户消息
        category_message = self._category_messages.get(context.category, "发生错误")
        user_message = f"{operation}失败: {category_message}"

        # 生成建议
        suggestion = self._category_suggestions.get(context.category)

        # 生成技术细节
        technical_details = self._format_technical_details(error, context)

        # 创建格式化错误
        formatted_error = FormattedError(
            message=user_message,
            context=context,
            suggestion=suggestion,
            technical_details=technical_details,
        )

        # 记录日志
        if self.enable_logging:
            self._log_error(formatted_error, operation)

        return formatted_error

    def _parse_error(self, error: Exception, provider: Optional[str]) -> ErrorContext:
        """解析错误,返回错误上下文"""
        # 特殊错误类型处理
        error_type = type(error).__name__

        # 超时错误
        if "timeout" in error_type.lower() or "TimeoutError" in error_type:
            return ErrorContext(
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.WARNING,
                provider=provider,
                original_error=error,
                is_retryable=True,
            )

        # 取消错误
        if "cancel" in error_type.lower() or "CancelledError" in error_type:
            return ErrorContext(
                category=ErrorCategory.CANCELLED,
                severity=ErrorSeverity.INFO,
                provider=provider,
                original_error=error,
                is_retryable=False,
            )

        # 使用提供商特定解析器
        if provider and provider in self._provider_parsers:
            parser = self._provider_parsers[provider]
            return parser(error)

        # 默认解析
        return self._parse_generic_error(error, provider)

    def _parse_generic_error(self, error: Exception, provider: Optional[str]) -> ErrorContext:
        """通用错误解析"""
        error_str = str(error).lower()

        # 网络相关
        if any(keyword in error_str for keyword in ["connection", "network", "dns"]):
            return ErrorContext(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.WARNING,
                provider=provider,
                original_error=error,
                is_retryable=True,
            )

        # 认证相关
        if any(keyword in error_str for keyword in ["auth", "key", "token", "unauthorized"]):
            return ErrorContext(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.ERROR,
                provider=provider,
                original_error=error,
                is_retryable=False,
            )

        # 速率限制
        if any(keyword in error_str for keyword in ["rate", "limit", "quota", "throttle"]):
            return ErrorContext(
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.WARNING,
                provider=provider,
                original_error=error,
                retry_after=60,
                is_retryable=True,
            )

        # 默认未知错误
        return ErrorContext(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            provider=provider,
            original_error=error,
            is_retryable=False,
        )

    def _format_technical_details(self, error: Exception, context: ErrorContext) -> str:
        """格式化技术细节"""
        details = []
        details.append(f"异常类型: {type(error).__name__}")
        details.append(f"错误类别: {context.category.value}")
        details.append(f"严重程度: {context.severity.value}")
        if context.provider:
            details.append(f"提供商: {context.provider}")
        if context.model:
            details.append(f"模型: {context.model}")
        if context.error_code:
            details.append(f"错误代码: {context.error_code}")
        details.append(f"原始错误: {str(error)}")
        details.append(f"发生时间: {context.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(details)

    def _log_error(self, formatted_error: FormattedError, operation: str):
        """记录错误日志"""
        context = formatted_error.context
        log_message = (
            f"[{context.severity.value.upper()}] {operation} - "
            f"{formatted_error.message} "
            f"(Category: {context.category.value}, "
            f"Provider: {context.provider or 'N/A'}, "
            f"Model: {context.model or 'N/A'})"
        )

        if context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif context.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif context.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    @classmethod
    def register_provider_parser(cls, provider: str, parser: Callable[[Exception], ErrorContext]):
        """
        注册自定义提供商错误解析器

        Args:
            provider: 提供商名称
            parser: 解析器函数
        """
        cls._provider_parsers[provider] = parser


# 全局错误处理器实例
error_handler = GlobalErrorHandler()
