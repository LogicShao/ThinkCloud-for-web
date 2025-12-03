"""
增强的日志系统模块
提供统一的日志配置、增强的日志记录器、结构化日志等功能
"""

from .config import (
    LogConfigManager,
    LoggingConfig,
    LogLevel,
    setup_logging,
)
from .config import (
    get_logger as get_standard_logger,
)
from .formatters import (
    ColorFormatter,
    DeepThinkFormatter,
    DetailedFormatter,
    JSONFormatter,
    SimpleFormatter,
    get_color_formatter,
    get_deep_think_formatter,
    get_detailed_formatter,
    get_json_formatter,
    get_simple_formatter,
)
from .logger import (
    EnhancedLogger,
    LogContext,
    get_deep_think_logger,
    get_deep_think_orchestrator_logger,
    get_deep_think_stage_logger,
    get_enhanced_logger,
    log_function_call,
)

__all__ = [
    # 配置相关
    "LogLevel",
    "LoggingConfig",
    "LogConfigManager",
    "setup_logging",
    "get_standard_logger",
    # 增强日志记录器
    "EnhancedLogger",
    "LogContext",
    "get_enhanced_logger",
    "get_deep_think_logger",
    "get_deep_think_stage_logger",
    "get_deep_think_orchestrator_logger",
    "log_function_call",
    # 格式化器
    "ColorFormatter",
    "JSONFormatter",
    "DetailedFormatter",
    "SimpleFormatter",
    "DeepThinkFormatter",
    "get_color_formatter",
    "get_json_formatter",
    "get_detailed_formatter",
    "get_simple_formatter",
    "get_deep_think_formatter",
]

# 设置默认日志配置
try:
    setup_logging()
except Exception:
    # 如果设置失败，使用基本的日志配置
    import logging

    logging.basicConfig(level=logging.INFO)
