"""
增强的日志记录器类
提供结构化日志、性能监控、上下文日志等功能
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps

from .config import LogLevel, get_logger


@dataclass
class LogContext:
    """日志上下文，用于传递额外的上下文信息"""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    module: Optional[str] = None
    stage: Optional[str] = None
    subtask_id: Optional[int] = None
    llm_call_count: Optional[int] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)


class EnhancedLogger:
    """增强的日志记录器"""

    def __init__(self, name: str, context: Optional[LogContext] = None):
        """
        初始化增强日志记录器

        Args:
            name: 日志记录器名称
            context: 日志上下文
        """
        self._logger = get_logger(name)
        self._context = context or LogContext()
        self._name = name

        # 性能监控数据
        self._timers: Dict[str, float] = {}

    @property
    def context(self) -> LogContext:
        """获取日志上下文"""
        return self._context

    @context.setter
    def context(self, value: LogContext):
        """设置日志上下文"""
        self._context = value

    def update_context(self, **kwargs):
        """更新日志上下文"""
        for key, value in kwargs.items():
            if hasattr(self._context, key):
                setattr(self._context, key, value)
            else:
                self._context.custom_fields[key] = value

    def trace(self, message: str, **kwargs):
        """记录TRACE级别日志"""
        if self._logger.isEnabledFor(LogLevel.TRACE):
            self._log_with_context(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        if self._logger.isEnabledFor(LogLevel.DEBUG):
            self._log_with_context(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        if self._logger.isEnabledFor(LogLevel.INFO):
            self._log_with_context(LogLevel.INFO, message, **kwargs)

    def warn(self, message: str, **kwargs):
        """记录WARN级别日志"""
        if self._logger.isEnabledFor(LogLevel.WARN):
            self._log_with_context(LogLevel.WARN, message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        if self._logger.isEnabledFor(LogLevel.ERROR):
            self._log_with_context(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        if self._logger.isEnabledFor(LogLevel.CRITICAL):
            self._log_with_context(LogLevel.CRITICAL, message, **kwargs)

    def _log_with_context(self, level: LogLevel, message: str, **kwargs):
        """带上下文的日志记录"""
        # 构建完整的消息
        full_message = self._build_message(message, **kwargs)

        # 记录日志
        self._logger.log(level.value, full_message, extra=self._get_extra_fields())

    def _build_message(self, message: str, **kwargs) -> str:
        """构建完整的日志消息"""
        parts = [message]

        # 添加上下文信息
        context_parts = []
        if self._context.request_id:
            context_parts.append(f"req_id={self._context.request_id}")
        if self._context.user_id:
            context_parts.append(f"user_id={self._context.user_id}")
        if self._context.session_id:
            context_parts.append(f"session_id={self._context.session_id}")
        if self._context.module:
            context_parts.append(f"context_module={self._context.module}")  # 使用 context_module 保持一致
        if self._context.stage:
            context_parts.append(f"stage={self._context.stage}")
        if self._context.subtask_id is not None:
            context_parts.append(f"subtask_id={self._context.subtask_id}")
        if self._context.llm_call_count is not None:
            context_parts.append(f"llm_call={self._context.llm_call_count}")

        # 添加自定义字段
        for key, value in self._context.custom_fields.items():
            if isinstance(value, (str, int, float, bool)):
                context_parts.append(f"{key}={value}")
            else:
                context_parts.append(f"{key}={str(value)}")

        # 添加额外的关键字参数
        for key, value in kwargs.items():
            if isinstance(value, (str, int, float, bool)):
                context_parts.append(f"{key}={value}")
            else:
                context_parts.append(f"{key}={str(value)}")

        if context_parts:
            parts.append(f"[{', '.join(context_parts)}]")

        return " | ".join(parts)

    def _get_extra_fields(self) -> Dict[str, Any]:
        """获取额外的日志字段（用于结构化日志）"""
        extra = {}

        # 添加上下文字段（使用 context_ 前缀避免与 LogRecord 内置属性冲突）
        if self._context.request_id:
            extra["request_id"] = self._context.request_id
        if self._context.user_id:
            extra["user_id"] = self._context.user_id
        if self._context.session_id:
            extra["session_id"] = self._context.session_id
        if self._context.module:
            extra["context_module"] = self._context.module  # 改为 context_module 避免冲突
        if self._context.stage:
            extra["stage"] = self._context.stage
        if self._context.subtask_id is not None:
            extra["subtask_id"] = self._context.subtask_id
        if self._context.llm_call_count is not None:
            extra["llm_call_count"] = self._context.llm_call_count

        # 添加自定义字段
        extra.update(self._context.custom_fields)

        return extra

    # 性能监控方法
    def start_timer(self, timer_name: str) -> None:
        """开始计时器"""
        self._timers[timer_name] = time.time()
        self.trace(f"计时器 '{timer_name}' 已启动")

    def stop_timer(self, timer_name: str) -> Optional[float]:
        """停止计时器并返回耗时（秒）"""
        if timer_name not in self._timers:
            self.warn(f"计时器 '{timer_name}' 未找到")
            return None

        start_time = self._timers.pop(timer_name)
        elapsed = time.time() - start_time

        self.debug(f"计时器 '{timer_name}' 已停止，耗时: {elapsed:.3f}s")
        return elapsed

    @contextmanager
    def timer(self, timer_name: str):
        """计时器上下文管理器"""
        self.start_timer(timer_name)
        try:
            yield
        finally:
            self.stop_timer(timer_name)

    def log_performance(self, operation: str, duration: float, **kwargs):
        """记录性能日志"""
        self.info(f"性能监控 | {operation} | 耗时: {duration:.3f}s", **kwargs)

    # 结构化数据日志
    def log_data(self, data_name: str, data: Any, level: LogLevel = LogLevel.DEBUG):
        """记录结构化数据"""
        if isinstance(data, dict):
            data_str = ", ".join(f"{k}={v}" for k, v in data.items())
        elif isinstance(data, (list, tuple)):
            data_str = f"[{', '.join(str(item) for item in data)}]"
        else:
            data_str = str(data)

        message = f"数据日志 | {data_name} = {data_str}"
        self._log_with_context(level, message)

    def log_exception(self, message: str, exception: Exception, **kwargs):
        """记录异常日志"""
        self.error(f"{message} | 异常: {type(exception).__name__}: {str(exception)}", **kwargs)

        # 记录堆栈跟踪（DEBUG级别）
        import traceback
        stack_trace = traceback.format_exc()
        self.debug(f"异常堆栈跟踪:\n{stack_trace}")

    # 便捷方法
    @classmethod
    def get_logger(cls, name: str, context: Optional[LogContext] = None) -> "EnhancedLogger":
        """获取增强日志记录器"""
        return cls(name, context)

    def get_child(self, suffix: str) -> "EnhancedLogger":
        """获取子日志记录器"""
        child_name = f"{self._name}.{suffix}"
        child_context = LogContext(
            request_id=self._context.request_id,
            user_id=self._context.user_id,
            session_id=self._context.session_id,
            module=suffix,
            stage=self._context.stage,
            subtask_id=self._context.subtask_id,
            llm_call_count=self._context.llm_call_count,
            custom_fields=self._context.custom_fields.copy()
        )
        return EnhancedLogger(child_name, child_context)


# 装饰器函数
def log_function_call(logger: Optional[EnhancedLogger] = None, level: Union[LogLevel, int] = LogLevel.DEBUG):
    """
    记录函数调用的装饰器

    Args:
        logger: 日志记录器，如果为None则自动创建
        level: 日志级别（可以是LogLevel枚举或整数）
    """
    # 将整数转换为LogLevel枚举
    if isinstance(level, int):
        level = LogLevel(level)  # 从整数转换

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取或创建日志记录器
            func_logger = logger or EnhancedLogger.get_logger(func.__module__)

            # 记录函数开始
            func_logger._log_with_context(
                level,
                f"函数调用开始 | {func.__name__}",
                args=str(args),
                kwargs=str(kwargs)
            )

            # 执行函数并计时
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # 记录函数结束
                func_logger._log_with_context(
                    level,
                    f"函数调用结束 | {func.__name__} | 耗时: {elapsed:.3f}s",
                    result=str(result)[:100]  # 只记录前100个字符
                )

                return result

            except Exception as e:
                elapsed = time.time() - start_time

                # 记录异常
                func_logger._log_with_context(
                    LogLevel.ERROR,
                    f"函数调用异常 | {func.__name__} | 耗时: {elapsed:.3f}s | 异常: {type(e).__name__}: {str(e)}"
                )
                raise

        return wrapper

    return decorator


# 便捷的全局函数
def get_enhanced_logger(name: str, context: Optional[LogContext] = None) -> EnhancedLogger:
    """获取增强日志记录器（便捷函数）"""
    return EnhancedLogger.get_logger(name, context)


# 为deep_think模块预定义的日志记录器
def get_deep_think_logger(context: Optional[LogContext] = None) -> EnhancedLogger:
    """获取deep_think模块的日志记录器"""
    return get_enhanced_logger("src.deep_think", context)


def get_deep_think_stage_logger(stage: str, context: Optional[LogContext] = None) -> EnhancedLogger:
    """获取deep_think阶段日志记录器"""
    if context is None:
        context = LogContext()
    context.stage = stage
    return get_enhanced_logger(f"src.deep_think.stages.{stage}", context)


def get_deep_think_orchestrator_logger(context: Optional[LogContext] = None) -> EnhancedLogger:
    """获取deep_think编排器日志记录器"""
    return get_enhanced_logger("src.deep_think.orchestrator", context)
