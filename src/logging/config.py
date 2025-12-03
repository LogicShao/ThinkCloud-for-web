"""
日志配置模块
提供统一的日志配置管理
"""

import logging
import os
import sys
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional, Union


class LogLevel(IntEnum):
    """自定义日志级别"""

    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogHandlerConfig:
    """日志处理器配置"""

    handler_type: str  # console, file, rotating_file, timed_rotating_file
    level: Union[str, LogLevel] = LogLevel.INFO
    formatter: str = "default"

    # 文件处理器专用配置
    filename: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    when: str = "midnight"  # 时间轮转的间隔
    interval: int = 1

    # 控制台处理器专用配置
    stream: Optional[str] = None  # stdout, stderr


@dataclass
class LoggerConfig:
    """日志记录器配置"""

    name: str
    level: Union[str, LogLevel] = LogLevel.INFO
    handlers: List[str] = field(default_factory=lambda: ["console"])
    propagate: bool = False


@dataclass
class LoggingConfig:
    """完整的日志配置"""

    # 根日志记录器配置
    root_level: Union[str, LogLevel] = LogLevel.INFO
    root_handlers: List[str] = field(default_factory=lambda: ["console"])

    # 处理器配置
    handlers: Dict[str, LogHandlerConfig] = field(default_factory=dict)

    # 日志记录器配置
    loggers: Dict[str, LoggerConfig] = field(default_factory=dict)

    # 格式化器配置
    formatters: Dict[str, str] = field(default_factory=dict)

    # 其他配置
    disable_existing_loggers: bool = False

    def __post_init__(self):
        """初始化后处理"""
        # 设置默认处理器
        if not self.handlers:
            self.handlers = {
                "console": LogHandlerConfig(
                    handler_type="console", level=self.root_level, formatter="default"
                )
            }

        # 设置默认格式化器
        if not self.formatters:
            self.formatters = {
                "default": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                "json": '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
            }

        # 设置默认日志记录器
        if not self.loggers:
            self.loggers = {}


class LogConfigManager:
    """日志配置管理器"""

    def __init__(self, config: Optional[LoggingConfig] = None):
        """
        初始化日志配置管理器

        Args:
            config: 日志配置，如果为None则使用默认配置
        """
        self.config = config or self.get_default_config()
        self._configured = False

    @classmethod
    def get_default_config(cls) -> LoggingConfig:
        """获取默认配置"""
        return LoggingConfig(
            root_level=LogLevel.INFO,
            root_handlers=["console"],
            handlers={
                "console": LogHandlerConfig(
                    handler_type="console",
                    level=LogLevel.INFO,
                    formatter="default",
                    stream="stdout",
                ),
                "file": LogHandlerConfig(
                    handler_type="file",
                    level=LogLevel.DEBUG,
                    formatter="detailed",
                    filename="logs/app.log",
                ),
                "error_file": LogHandlerConfig(
                    handler_type="file",
                    level=LogLevel.ERROR,
                    formatter="detailed",
                    filename="logs/error.log",
                ),
            },
            loggers={
                "src.deep_think": LoggerConfig(
                    name="src.deep_think",
                    level=LogLevel.DEBUG,
                    handlers=["console", "file"],
                    propagate=False,
                ),
                "src.deep_think.core": LoggerConfig(
                    name="src.deep_think.core",
                    level=LogLevel.INFO,
                    handlers=["console"],
                    propagate=True,
                ),
                "src.deep_think.stages": LoggerConfig(
                    name="src.deep_think.stages",
                    level=LogLevel.DEBUG,
                    handlers=["console", "file"],
                    propagate=False,
                ),
                "src.deep_think.orchestrator": LoggerConfig(
                    name="src.deep_think.orchestrator",
                    level=LogLevel.TRACE,
                    handlers=["console", "file"],
                    propagate=False,
                ),
            },
        )

    @classmethod
    def get_debug_config(cls) -> LoggingConfig:
        """获取调试配置（最详细的日志）"""
        config = cls.get_default_config()
        config.root_level = LogLevel.DEBUG

        # 为deep_think模块设置TRACE级别
        config.loggers["src.deep_think"].level = LogLevel.TRACE
        config.loggers["src.deep_think.stages"].level = LogLevel.TRACE
        config.loggers["src.deep_think.orchestrator"].level = LogLevel.TRACE

        return config

    @classmethod
    def get_production_config(cls) -> LoggingConfig:
        """获取生产环境配置（只记录重要信息）"""
        config = cls.get_default_config()
        config.root_level = LogLevel.WARN

        # 移除文件处理器，只保留控制台
        config.root_handlers = ["console"]
        config.handlers = {
            "console": LogHandlerConfig(
                handler_type="console", level=LogLevel.WARN, formatter="default", stream="stdout"
            )
        }

        # 简化日志记录器配置
        config.loggers = {
            "src.deep_think": LoggerConfig(
                name="src.deep_think", level=LogLevel.INFO, handlers=["console"], propagate=False
            )
        }

        return config

    def configure(self) -> None:
        """应用日志配置"""
        if self._configured:
            return

        # 添加自定义日志级别
        self._add_custom_levels()

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_level_value(self.config.root_level))

        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 添加根处理器
        for handler_name in self.config.root_handlers:
            if handler_name in self.config.handlers:
                handler = self._create_handler(self.config.handlers[handler_name])
                if handler:
                    root_logger.addHandler(handler)

        # 配置各个日志记录器
        for logger_name, logger_config in self.config.loggers.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(self._get_level_value(logger_config.level))
            logger.propagate = logger_config.propagate

            # 清除现有的处理器
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

            # 添加处理器
            for handler_name in logger_config.handlers:
                if handler_name in self.config.handlers:
                    handler = self._create_handler(self.config.handlers[handler_name])
                    if handler:
                        logger.addHandler(handler)

        self._configured = True
        logging.getLogger(__name__).info("日志系统配置完成")

    def _add_custom_levels(self) -> None:
        """添加自定义日志级别"""
        # 添加TRACE级别
        logging.addLevelName(LogLevel.TRACE, "TRACE")

        def trace(self, message, *args, **kwargs):
            if self.isEnabledFor(LogLevel.TRACE):
                self._log(LogLevel.TRACE, message, args, **kwargs)

        logging.Logger.trace = trace

    def _get_level_value(self, level: Union[str, LogLevel, int]) -> int:
        """获取日志级别的数值"""
        if isinstance(level, LogLevel):
            return level.value
        elif isinstance(level, str):
            if hasattr(logging, level.upper()):
                return getattr(logging, level.upper())
            elif level.upper() in LogLevel.__members__:
                return LogLevel[level.upper()].value
            else:
                return logging.INFO
        elif isinstance(level, int):
            return level
        else:
            return logging.INFO

    def _create_handler(self, handler_config: LogHandlerConfig) -> Optional[logging.Handler]:
        """创建日志处理器"""
        # 创建格式化器
        formatter_str = self.config.formatters.get(
            handler_config.formatter, self.config.formatters["default"]
        )
        formatter = logging.Formatter(formatter_str)

        # 创建处理器
        if handler_config.handler_type == "console":
            if handler_config.stream == "stderr":
                stream = sys.stderr
            else:
                stream = sys.stdout

            handler = logging.StreamHandler(stream)

        elif handler_config.handler_type == "file":
            if not handler_config.filename:
                return None

            # 确保日志目录存在
            log_dir = os.path.dirname(handler_config.filename)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            handler = logging.FileHandler(handler_config.filename, encoding="utf-8")

        elif handler_config.handler_type == "rotating_file":
            if not handler_config.filename:
                return None

            from logging.handlers import RotatingFileHandler

            log_dir = os.path.dirname(handler_config.filename)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            handler = RotatingFileHandler(
                handler_config.filename,
                maxBytes=handler_config.max_bytes,
                backupCount=handler_config.backup_count,
                encoding="utf-8",
            )

        elif handler_config.handler_type == "timed_rotating_file":
            if not handler_config.filename:
                return None

            from logging.handlers import TimedRotatingFileHandler

            log_dir = os.path.dirname(handler_config.filename)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            handler = TimedRotatingFileHandler(
                handler_config.filename,
                when=handler_config.when,
                interval=handler_config.interval,
                backupCount=handler_config.backup_count,
                encoding="utf-8",
            )

        else:
            # 未知的处理器类型，使用控制台处理器
            handler = logging.StreamHandler(sys.stdout)

        # 设置处理器级别和格式化器
        handler.setLevel(self._get_level_value(handler_config.level))
        handler.setFormatter(formatter)

        return handler

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器（确保配置已应用）"""
        if not self._configured:
            self.configure()

        return logging.getLogger(name)

    def update_config(self, new_config: LoggingConfig) -> None:
        """更新配置并重新应用"""
        self.config = new_config
        self._configured = False
        self.configure()

    def set_level(self, logger_name: str, level: Union[str, LogLevel]) -> None:
        """动态设置日志记录器级别"""
        logger = logging.getLogger(logger_name)
        logger.setLevel(self._get_level_value(level))

        # 更新配置
        if logger_name in self.config.loggers:
            self.config.loggers[logger_name].level = level
        else:
            # 如果是根日志记录器
            if logger_name == "":
                self.config.root_level = level


# 全局配置管理器实例
_config_manager: Optional[LogConfigManager] = None


def get_config_manager() -> LogConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = LogConfigManager()
    return _config_manager


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """设置日志系统（入口函数）"""
    global _config_manager
    _config_manager = LogConfigManager(config)
    _config_manager.configure()


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器（便捷函数）"""
    return get_config_manager().get_logger(name)
