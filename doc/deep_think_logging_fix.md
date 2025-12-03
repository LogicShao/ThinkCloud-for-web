# 深度思考模块日志增强修复说明

## 问题诊断

### 原始问题

根据日志 `logs/app.log` (行119-136)，深度思考功能中出现JSON解析失败：

```
[LLM RESPONSE PREVIEW]
[LLM RESPONSE FULL]
[SOLVE] 子任务 1 执行失败，原始响应: ...
[SOLVE] 子任务 1 执行失败: 无法解析JSON响应: ...
```

**症状分析**：

1. LLM响应被检测为生成器
2. 转换为字符串后响应为空
3. JSON解析失败
4. 日志中没有打印实际的LLM响应内容，无法调试

## 修复内容

### 修复的文件列表

- ✅ `src/deep_think/stages/base.py` - 基础处理器（生成器转换和日志输出）
- ✅ `src/deep_think/stages/planner.py` - 规划阶段错误日志
- ✅ `src/deep_think/stages/solver.py` - 解决阶段错误日志
- ✅ `src/deep_think/stages/synthesizer.py` - 整合阶段错误日志
- ✅ `src/deep_think/stages/reviewer.py` - 审查阶段错误日志

### 主要改进

#### 1. 增强生成器转换逻辑

支持多种chunk格式，正确提取内容：

- 字符串类型直接添加
- `.content` 属性（OpenAI风格）
- `.text` 属性
- `.delta.content` 属性（流式响应）
- 记录前3个chunk的类型和内容用于调试

#### 2. 增强日志输出

- 显示响应类型和长度
- 响应为空时发出明确警告/错误
- 完整响应输出到DEBUG级别（避免日志过大）
- 预览输出到INFO级别（便于快速定位）

#### 3. 统一错误日志格式

所有阶段处理器都增强了错误日志：

- 显示响应长度
- 区分"响应为空"和"变量未定义"
- 预览和完整响应分级输出

## 使用指南

### 启用DEBUG级别日志

修改日志配置以查看完整响应：

```python
import logging
logging.getLogger('src.deep_think.stages.base').setLevel(logging.DEBUG)
```

### 调试JSON解析问题

1. 查看响应长度和类型
2. 检查chunk提取是否成功
3. 查看完整响应内容（DEBUG级别）
4. 分析JSON格式是否正确

## 预期效果

修复后的日志示例：

**成功场景**：

```
[LLM CALL] 生成器转换完成，共25个chunk，总长度: 1024
[LLM CALL] 最终响应类型: str, 长度: 1024
[LLM RESPONSE PREVIEW] {"analysis": "..."}...
```

**失败场景**：

```
[LLM CALL] 生成器转换完成，共10个chunk，总长度: 0
[LLM CALL] 最终响应类型: str, 长度: 0
[LLM RESPONSE PREVIEW] 响应为空字符串！
[LLM RESPONSE FULL] 响应为空！这可能导致JSON解析失败
```

## 修复时间

- 日期：2025-12-03
- 文件数：5个
- 向后兼容：✅ 完全兼容
