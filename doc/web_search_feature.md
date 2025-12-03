# Web 搜索功能文档

## 功能概述

ThinkCloud for Web 现已支持 **网络搜索功能**，可在深度思考模式中自动搜索外部信息，增强 AI 的回答质量。

## 功能特性

- 🌐 **自动搜索**: 当 AI 需要最新信息或外部数据时���自动触发网络搜索
- 🔍 **智能整合**: 将搜索结果智能整合到深度思考分析中
- 🚀 **DuckDuckGo 驱动**: 使用 DuckDuckGo 搜索引擎，无需 API 密钥
- 🌏 **区域化搜索**: 支持设置搜索区域（默认中文）
- 📊 **结果格式化**: 自动格式化搜索结果，包括标题、链接和摘要

## 安装依赖

```bash
# 安装 duckduckgo-search 库
pip install duckduckgo-search

# 或从 requirements.txt 安装所有依赖
pip install -r requirements.txt
```

## 使用方法

### 1. 在 UI 中启用

1. 启动应用: `python main.py`
2. 在左侧控制面板找到 **🧠 深度思考模式** 区域
3. 勾选 "启用深度思考"
4. 展开 "高级选项"
5. 勾选 **"启用网络搜索"**
6. 输入需要搜索信息的问题

### 2. 适用场景

✅ **推荐使用网络搜索的场景：**

- 询问最新资讯（如"2024年AI发展趋势"）
- 需要实时数据（如"当前股票价格"）
- 查询事实信息（如"某公司成立时间"）
- 技术问题（如"Python最新版本特性"）
- 学术研究（如"某领域最新论文"）

❌ **不推荐使用的场景：**

- 纯理论分析问题
- 主观意见问答
- 创意写作任务
- 已有足够上下文的问题

### 3. 工作原理

```
用户提问 → 深度思考规��� → 分解子任务
    ↓
子任务分析 → AI判断是否需要外部信息
    ↓（如果需要）
触发网络搜索 → 获取搜索结果（3条）
    ↓
LLM整合搜索结果 → 生成增强分析
    ↓
继续下一个子任务 → ... → 最终答案
```

## 配置选项

### 程序化使用

```python
from src.deep_think import DeepThinkOrchestrator
from src.api_service import api_service

# 创建编排器，启用网络搜索
orchestrator = DeepThinkOrchestrator(
    api_service=api_service,
    model="qwen-3-235b-a22b-thinking-2507",
    max_subtasks=6,
    enable_review=True,
    enable_web_search=True,  # 启用网络搜索
    verbose=True
)

# 执行深度思考
result = orchestrator.run("2024年人工智能发展的最新趋势是什么？")
```

### 自定义搜索工具

```python
from src.tools.web_search import WebSearchTool

# 创建自定义搜索工具
tool = WebSearchTool(
    max_results=5,      # 最大搜索结果数（默认: 5）
    region="us-en"      # 搜索区域（默认: cn-zh）
)

# 执行搜索
results = tool.search("artificial intelligence trends 2024")

# 格式化输出
formatted = tool.search_and_format("AI trends", max_results=3)
print(formatted)
```

## 技术细节

### 搜索触发条件

AI 会在子任务分析时判断是否需要外部信息：

```python
# 在 SubtaskResult 中标记
SubtaskResult(
    needs_external_info=True,        # 需要外部信息
    suggested_tools=["search"],      # 建议使用搜索工具
    # ...
)
```

当满足以下条件时自动触发搜索：

1. `enable_web_search=True`（用户已启用）
2. `needs_external_info=True`（AI判断需要）
3. `web_search_tool.is_available()`（工具可用）

### 搜索结果处理

1. **搜索查询构建**: 使用子任务描述或原始问题构建查询
2. **获取搜索结果**: 默认获取 3 条搜索结果
3. **LLM 整合**: 使用 LLM 将搜索结果整合到分析中
4. **更新结果**: 更新 `analysis` 和 `intermediate_conclusion`

### 性能影响

- **额外 LLM 调用**: 每个需要搜索的子任务增加 1 次 LLM 调用
- **网络延迟**: 搜索请求增加 1-3 秒延迟
- **Token 消耗**: 搜索结果增加约 500-1000 tokens

**示例**:

- 无搜索: 5-9 次 LLM 调用，30-180秒
- 有搜索 (2个子任务): 7-11 次 LLM 调用，40-200秒

## 示例对话

### 示例 1: 查询最新信息

**用户**: 2024年 Python 最新版本有哪些新特性？

**AI 行为**:

1. 规划阶段: 拆分为查询版本、分析特性等子任务
2. 子任务1: "查询 Python 最新版本"
    - AI 判断需要外部信息 → 触发搜索
    - 搜索: "Python latest version 2024"
    - 整合搜索结果到分析中
3. 子任务2: "分析新特性"
    - 基于搜索结果进行分析
4. 最终答案: 整合所有信息生成完整回复

### 示例 2: 技术对比

**用户**: 比较 2024 年主流 LLM 模型的性能表现

**AI 行为**:

1. 子任务需要各模型的最新 benchmark 数据
2. 自动搜索 "LLM benchmark 2024"
3. 整合搜索结果到对比分析中
4. 生成基于真实数据的对比报告

## 故障排查

### 问题 1: 搜索功能不可用

**症状**: UI 显示搜索选项，但搜索未触发

**解决方案**:

```bash
# 检查是否安装依赖
pip list | grep duckduckgo

# 重新安装
pip install duckduckgo-search

# 或使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple duckduckgo-search
```

### 问题 2: 搜索结果为空

**可能原因**:

- 网络连接问题
- DuckDuckGo API 限流
- 搜索关键词不合适

**解决方案**:

- 检查网络连接
- 稍后重试
- 调整搜索区域设置

### 问题 3: 搜索超时

**解决方案**:

```python
# 在 web_search.py 中调整超时设置
# 目前使用 duckduckgo_search 默认设置
# 如需自定义，可修改 WebSearchTool 类
```

## 路线图

### 未来计划

- [ ] 支持更多搜索引擎（Google、Bing）
- [ ] 搜索结果缓存机制
- [ ] 用户自定义搜索参数
- [ ] 搜索历史记录
- [ ] 并行搜索多个关键词
- [ ] 智能搜索关键词提取

## 相关文件

- `src/tools/web_search.py` - Web 搜索工具实现
- `src/tools/__init__.py` - 工具模块入口
- `src/deep_think/orchestrator.py` - 深度思考编排器（集成搜索）
- `src/deep_think/stages/solver.py` - 子任务处理器（搜索增强）
- `tests/test_web_search.py` - 搜索功能测试

## 贡献指南

欢迎贡献搜索功能相关代码！请确保：

1. 添加单元测试
2. 更新相关文档
3. 遵循现有代码风格
4. 考虑错误处理和容错性

---

**需要帮助？** 请在 GitHub 提交 Issue。
