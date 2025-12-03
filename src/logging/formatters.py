"""
日志格式化器模块
提供各种日志格式化器
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class ColorFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    # 颜色代码
    COLORS = {
        "TRACE": "\033[90m",  # 灰色
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARN": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "RESET": "\033[0m",  # 重置颜色
    }

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """初始化颜色格式化器"""
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录，添加颜色"""
        # 保存原始级别名称
        original_levelname = record.levelname

        # 添加颜色
        if original_levelname in self.COLORS:
            color = self.COLORS[original_levelname]
            reset = self.COLORS["RESET"]
            record.levelname = f"{color}{original_levelname}{reset}"

        # 格式化消息
        formatted = super().format(record)

        # 恢复原始级别名称
        record.levelname = original_levelname

        return formatted


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""

    def __init__(self, include_extra: bool = True):
        """初始化JSON格式化器"""
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """将日志记录格式化为JSON字符串"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
            "process": record.processName,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # 添加额外的字段
        if self.include_extra and hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in log_data and not key.startswith("_"):
                    # 尝试序列化值
                    try:
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)

        return json.dumps(log_data, ensure_ascii=False)


class DetailedFormatter(logging.Formatter):
    """详细的日志格式化器"""

    def __init__(self):
        """初始化详细格式化器"""
        fmt = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-30s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        super().__init__(fmt, datefmt)


class SimpleFormatter(logging.Formatter):
    """简单的日志格式化器"""

    def __init__(self):
        """初始化简单格式化器"""
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        datefmt = "%H:%M:%S"
        super().__init__(fmt, datefmt)


class DeepThinkFormatter(logging.Formatter):
    """deep_think模块专用的日志格式化器"""

    def __init__(self):
        """初始化deep_think格式化器"""
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        datefmt = "%H:%M:%S"
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """格式化deep_think日志记录"""
        # 添加deep_think特定的格式化
        message = record.getMessage()

        # 根据日志名称添加前缀
        if record.name.startswith("src.deep_think.orchestrator"):
            prefix = "[编排器]"
        elif record.name.startswith("src.deep_think.stages.planner"):
            prefix = "[规划阶段]"
        elif record.name.startswith("src.deep_think.stages.solver"):
            prefix = "[解决阶段]"
        elif record.name.startswith("src.deep_think.stages.synthesizer"):
            prefix = "[整合阶段]"
        elif record.name.startswith("src.deep_think.stages.reviewer"):
            prefix = "[审查阶段]"
        elif record.name.startswith("src.deep_think"):
            prefix = "[深度思考]"
        else:
            prefix = ""

        if prefix:
            record.msg = f"{prefix} {message}"

        return super().format(record)


# 预定义的格式化器
def get_color_formatter() -> ColorFormatter:
    """获取带颜色的控制台格式化器"""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
    datefmt = "%H:%M:%S"
    return ColorFormatter(fmt, datefmt)


def get_json_formatter() -> JSONFormatter:
    """获取JSON格式化器"""
    return JSONFormatter()


def get_detailed_formatter() -> DetailedFormatter:
    """获取详细格式化器"""
    return DetailedFormatter()


def get_simple_formatter() -> SimpleFormatter:
    """获取简单格式化器"""
    return SimpleFormatter()


def get_deep_think_formatter() -> DeepThinkFormatter:
    """获取deep_think格式化器"""
    return DeepThinkFormatter()
