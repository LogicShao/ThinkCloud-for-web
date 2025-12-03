# 日志系统使用指南

## 概述

SimpleLLMFront 项目配备了强大的日志系统，特别针对深度思考模块（deep_think）进行了优化，帮助你轻松调试和监控推理流程。

## 日志系统架构

### 核心组件

1. **EnhancedLogger** - 增强型日志记录器
    - 支持上下文信息（request_id、stage、subtask_id 等）
    - 性能监控和计时器
    - 结构化数据记录
    - 异常堆栈跟踪

2. **日志级别**
    - TRACE (5) - 最详细的调试信息
    - DEBUG (10) - 调试信息
    - INFO (20) - 一般信息
    - WARN (30) - 警告
    - ERROR (40) - 错误
    - CRITICAL (50) - 严重错误

3. **专用日志记录器**
    - `src.deep_think` - 主模块日志
    - `src.deep_think.orchestrator` - 编排器日志（TRACE级别）
    - `src.deep_think.stages.planner` - 规划阶段日志
    - `src.deep_think.stages.solver` - 解决阶段日志
    - `src.deep_think.stages.synthesizer` - 整合阶段日志
    - `src.deep_think.stages.reviewer` - 审查阶段日志

## 使用方法

### 1. 基础日志配置

```python
from src.logging import setup_logging, LogConfigManager

# 方式1: 使用默认配置（推荐用于快速开始）
setup_logging()

# 方式2: 使用调试配置（最详细的日志）
from src.logging import LogConfigManager
manager = LogConfigManager()
config = LogConfigManager.get_debug_config()
setup_logging(config)

# 方式3: 使用生产环境配置（仅记录警告和错误）
config = LogConfigManager.get_production_config()
setup_logging(config)
```

### 2. 获取日志记录器

```python
from src.logging import (
    get_enhanced_logger,
    get_deep_think_logger,
    get_deep_think_stage_logger,
    get_deep_think_orchestrator_logger,
    LogContext
)

# 通用增强日志记录器
logger = get_enhanced_logger("my.module")
logger.info("这是一条信息")

# deep_think 专用日志记录器
logger = get_deep_think_logger()
logger.debug("深度思考日志")

# 带上下文的日志记录器
context = LogContext(
    request_id="req-123",
    session_id="sess-456",
    stage="plan",
    subtask_id=1
)
logger = get_deep_think_orchestrator_logger(context)
logger.info("开始规划阶段")
```

### 3. 上下文和性能监控

```python
# 更新上下文
logger.update_context(stage="solve", subtask_id=2, llm_call_count=5)

# 使用计时器
logger.start_timer("my_operation")
# ... 执行操作 ...
elapsed = logger.stop_timer("my_operation")

# 使用上下文管理器计时
with logger.timer("batch_operation"):
    # ... 执行批量操作 ...
    pass

# 记录性能数据
logger.log_performance("database_query", 0.342, query="SELECT * FROM users")

# 记录结构化数据
logger.log_data("user_profile", {"name": "Alice", "age": 30, "premium": True})
```

### 4. 函数调用日志装饰器

```python
from src.logging import log_function_call, LogLevel

# 默认 DEBUG 级别
@log_function_call()
def my_function(a, b):
    return a + b

# TRACE 级别（更详细）
@log_function_call(level=5)  # TRACE = 5
def detailed_function(x):
    return x * 2

# 自定义日志记录器
from src.logging import get_enhanced_logger
logger = get_enhanced_logger("my.module")

@log_function_call(logger=logger, level=LogLevel.INFO)
def tracked_function(data):
    return process(data)
```

## 日志输出示例

### 控制台输出示例

```
14:25:30 | INFO     | src.deep_think.orchestrator | [编排器] 开始深度思考流程
14:25:30 | TRACE    | src.deep_think.orchestrator | [编排器] 函数调用开始 | run | args=('如何提高编程技能？',) | kwargs={}
14:25:30 | DEBUG    | src.deep_think.orchestrator | [编排器] 计时器 'plan_stage' 已启动
14:25:30 | INFO     | src.deep_think.stages.planner | [规划阶段] [LLM CALL #1] Stage: plan
14:25:32 | INFO     | src.deep_think.stages.planner | [规划阶段] [LLM RESPONSE] {"clarified_question": "如何提高编程技能..."
14:25:32 | INFO     | src.deep_think.stages.planner | [规划阶段] [PLAN] 生成了 3 个子任务
14:25:32 | DEBUG    | src.deep_think.orchestrator | [编排器] 计时器 'plan_stage' 已停止，耗时: 2.123s
14:25:32 | INFO     | src.deep_think.orchestrator | [编排器] 计时器 'solve_stage' 已启动
14:25:32 | INFO     | src.deep_think.stages.solver | [解决阶段] [LLM CALL #2] Stage: solve
14:25:35 | INFO     | src.deep_think.stages.solver | [解决阶段] [SOLVE] 完成子任务 1: 深入理解和分析问题...
14:25:35 | INFO     | src.deep_think.stages.solver | [解决阶段] [LLM CALL #3] Stage: solve
14:25:38 | INFO     | src.deep_think.stages.solver | [解决阶段] [SOLVE] 完成子任务 2: 探索可能的解...
14:25:38 | INFO     | src.deep_think.stages.solver | [解决阶段] [LLM CALL #4] Stage: solve
14:25:42 | INFO     | src.deep_think.stages.solver | [解决阶段] [SOLVE] 完成子任务 3: 综合评估和总结
14:25:42 | DEBUG    | src.deep_think.orchestrator | [编排器] 计时器 'solve_stage' 已停止，耗时: 9.876s
14:25:42 | INFO     | src.deep_think.orchestrator | [编排器] 计时器 'synthesize_stage' 已启动
14:25:42 | INFO     | src.deep_think.stages.synthesizer | [整合阶段] [LLM CALL #5] Stage: synthesize
14:25:45 | INFO     | src.deep_think.stages.synthesizer | [整合阶段] [SYNTHESIZE] 生成最终答案
14:25:45 | DEBUG    | src.deep_think.orchestrator | [编排器] 计时器 'synthesize_stage' 已停止，耗时: 3.456s
14:25:45 | INFO     | src.deep_think.orchestrator | [编排器] 计时器 'review_stage' 已启动
14:25:45 | INFO     | src.deep_think.stages.reviewer | [审查阶段] [LLM CALL #6] Stage: review
14:25:48 | INFO     | src.deep_think.stages.reviewer | [审查阶段] [REVIEW] 审查完成，质量评分: 0.85
14:25:48 | DEBUG    | src.deep_think.orchestrator | [编排器] 计时器 'review_stage' 已停止，耗时: 2.789s
14:25:48 | INFO     | src.deep_think.orchestrator | [编排器] 深度思考流程完成 | total_llm_calls=6 | subtask_count=3 | has_review=True | final_answer_length=1256
```

### JSON 日志输出示例

```json
{
  "timestamp": "2025-12-01T14:25:30",
  "level": "INFO",
  "logger": "src.deep_think.orchestrator",
  "message": "开始深度思考流程",
  "module": "orchestrator",
  "function": "run",
  "line": 153,
  "request_id": "req-123",
  "session_id": "sess-456",
  "custom_fields": {
    "model": "qwen-3-235b-a22b-thinking-2507",
    "max_subtasks": 6,
    "enable_review": true
  }
}
```

## 调试 deep_think 模块

### 调试步骤

1. **启用 TRACE 级别日志**

```python
from src.logging import LogConfigManager, setup_logging

# 获取调试配置（包含 TRACE 级别）
config = LogConfigManager.get_debug_config()
setup_logging(config)
```

2. **查看执行流程**

日志会显示每个阶段的开始和结束、LLM 调用次数、耗时等信息。

3. **检查 LLM 调用**

搜索 `[LLM CALL #N]` 查看每次 LLM 调用的详细信息：

- 调用编号
- 所属阶段
- 响应预览

4. **监控子任务执行**

在解决阶段，每个子任务的执行情况都会记录：

- 子任务 ID
- 描述
- 可信度

5. **查看性能数据**

计时器会记录每个阶段的耗时，帮助你识别性能瓶颈。

### 常见问题排查

#### 问题1: JSON 解析失败

**日志特征**:

```
WARN | [SOLVE] 子任务 2 执行失败: ValueError: 无法解析JSON响应
```

**解决方法**:

- 检查 LLM 响应格式
- 查看 `response_preview` 确认内容
- 检查提示词模板

#### 问题2: LLM 调用返回生成器

**日志特征**:

```
WARN | [LLM CALL] 检测到生成器响应，正在转换为字符串...
```

**解决方法**:

- 确保 `stream=False`
- 检查 API 服务配置

#### 问题3: 缓存命中

**日志特征**:

```
DEBUG | [编排器] 从缓存获取规划
```

**解决方法**:

- 清空缓存：`orchestrator.clear_cache()`
- 检查缓存键生成逻辑

#### 问题4: 阶段执行失败

**日志特征**:

```
WARN | [SYNTHESIZE] 整合失败: KeyError: 'final_answer'
```

**解决方法**:

- 检查提示词模板
- 查看 LLM 响应结构
- 启用详细日志查看完整响应

## 高级配置

### 自定义日志格式

```python
from src.logging import LoggingConfig, LogHandlerConfig, LogLevel

config = LoggingConfig(
    root_level=LogLevel.DEBUG,
    handlers={
        "console": LogHandlerConfig(
            handler_type="console",
            level=LogLevel.DEBUG,
            formatter="default",
            stream="stdout"
        ),
        "file": LogHandlerConfig(
            handler_type="rotating_file",
            level=LogLevel.TRACE,
            formatter="detailed",
            filename="logs/deep_think.log",
            max_bytes=10*1024*1024,  # 10MB
            backup_count=5
        )
    },
    loggers={
        "src.deep_think": {
            "level": LogLevel.TRACE,
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
)

setup_logging(config)
```

### 动态调整日志级别

```python
from src.logging import get_config_manager

# 获取配置管理器
manager = get_config_manager()

# 动态设置日志级别
manager.set_level("src.deep_think", "DEBUG")
manager.set_level("src.deep_think.orchestrator", "TRACE")

# 在生产环境中降低日志级别
manager.set_level("src.deep_think", "INFO")
```

### 输出到文件

```python
from src.logging import LoggingConfig, LogHandlerConfig, LogLevel

config = LoggingConfig()

# 添加文件处理器
config.handlers["deep_think_file"] = LogHandlerConfig(
    handler_type="file",
    level=LogLevel.DEBUG,
    formatter="json",  # 使用 JSON 格式
    filename="logs/deep_think_debug.jsonl"
)

# 为 deep_think 模块添加文件处理器
config.loggers["src.deep_think"].handlers.append("deep_think_file")

setup_logging(config)
```

## 最佳实践

### 1. 开发环境配置

在开发环境中使用 DEBUG 或 TRACE 级别：

```python
from src.logging import setup_logging, LogConfigManager

# 使用调试配置
if __name__ == "__main__":
    setup_logging(LogConfigManager.get_debug_config())
    # ... 你的代码 ...
```

### 2. 生产环境配置

在生产环境中使用 INFO 或 WARN 级别：

```python
from src.logging import setup_logging, LogConfigManager

# 使用生产环境配置
setup_logging(LogConfigManager.get_production_config())
```

### 3. 添加有意义的上下文

```python
context = LogContext(
    request_id=generate_request_id(),
    session_id=user_session.id,
    module="my_module"
)
logger = get_enhanced_logger("my.app", context)

# 后续操作会自动带上上下文
logger.info("处理用户请求")  # 自动包含 request_id 和 session_id
```

### 4. 使用计时器监控性能

```python
# 监控关键操作的性能
with logger.timer("critical_operation"):
    result = perform_critical_operation()

# 自动记录：计时器 'critical_operation' 已启动/已停止
```

### 5. 优雅处理异常

```python
try:
    result = risky_operation()
except Exception as e:
    logger.log_exception("操作失败", e)
    # 自动记录异常信息和堆栈跟踪
```

## 集成到 deep_think 模块

deep_think 模块已经集成了日志系统。你只需配置日志级别即可开始使用！

```python
from src.logging import setup_logging, LogConfigManager
from src.api_service import api_service
from src.deep_think.orchestrator import DeepThinkOrchestrator

# 1. 配置日志（推荐在开发时使用 DEBUG 配置）
setup_logging(LogConfigManager.get_debug_config())

# 2. 创建编排器（自动启用日志）
orchestrator = DeepThinkOrchestrator(
    api_service=api_service,
    model="qwen-3-235b-a22b-thinking-2507",
    max_subtasks=6,
    enable_review=True,
    verbose=True,  # 启用详细日志
    request_id="debug-session-001"  # 可选：设置请求ID用于追踪
)

# 3. 执行深度思考（日志会自动记录）
question = "如何提高编程技能？"
result = orchestrator.run(question)

# 4. 查看控制台输出或日志文件
```

## 总结

本日志系统提供以下优势：

✅ **详细跟踪** - 每一步操作都有迹可循
✅ **性能监控** - 自动记录各阶段耗时
✅ **上下文追踪** - request_id、session_id、stage 等
✅ **易于调试** - TRACE 级别提供最详细信息
✅ **灵活配置** - 控制台、文件、JSON 格式可选
✅ **异常捕获** - 自动记录完整堆栈跟踪

## 相关文件

- `src/logging/` - 日志系统实现
- `src/deep_think/` - 深度思考模块（已集成日志）
- `tests/test_logging_system.py` - 日志系统测试
- `doc/deep_thinking_feature.md` - 深度思考功能文档
