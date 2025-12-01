# 深度思考功能 - 快速开始

## 5分钟快速上手

### 1. 启动应用

```bash
python main.py
```

### 2. 启用深度思考模式

在左侧控制面板中:

1. 勾选 **"启用深度思考"**
2. (可选) 点击 **"高级选项"** 调整配置

### 3. 提问并查看结果

输入一个复杂问题,例如:

```
请从历史、技术和应用三个角度分析人工智能的发展
```

### 4. 结果格式

你会看到:

- 💡 **深度思考结果**: 最终答案
- 🧠 **思考过程摘要**: 问题拆解和各子任务的分析
- 🔍 **质量审查**: 发现的问题和改进建议 (如果启用)
- **元信息**: LLM调用次数

## 示例问题

### 适合深度思考的问题

✅ **分析类**

- "分析远程办公对企业和员工的影响"
- "比较微服务和单体架构的优劣"

✅ **设计类**

- "设计一个在线教育平台的核心功能"
- "如何构建一个可扩展的推荐系统?"

✅ **研究类**

- "量子计算的发展现状和未来趋势"
- "区块链技术在金融领域的应用前景"

### 不适合的问题

❌ **简单查询**

- "Python的最新版本是多少?"
- "什么是HTTP?"

❌ **创意写作**

- "写一首关于春天的诗"
- "编一个科幻故事"

## 配置建议

### 针对不同场景

**快速探索 (节省时间和成本)**

- 模型: `llama-3.3-70b` (Cerebras, 最快)
- 最大子任务数: 3-4
- 启用审查: ❌

**深度分析 (追求质量)**

- 模型: `qwen-3-235b-a22b-thinking-2507` 或 `deepseek-chat`
- 最大子任务数: 5-6
- 启用审查: ✅

**专业级输出 (最高质量)**

- 模型: `gpt-4` 或 `gpt-4o`
- 最大子任务数: 6-8
- 启用审查: ✅
- 显示思考过程: ✅

## 代码使用示例

```python
from src.api_service import api_service
from src.deep_think import DeepThinkOrchestrator, format_deep_think_result

# 创建编排器
orchestrator = DeepThinkOrchestrator(
    api_service=api_service,
    model="qwen-3-235b-a22b-thinking-2507",
    max_subtasks=5,
    enable_review=True,
    verbose=True
)

# 执行深度思考
result = orchestrator.run("你的复杂问题")

# 格式化输出
print(format_deep_think_result(result, include_process=True))

# 访问详细数据
print(f"子任务数: {len(result.subtask_results)}")
for st in result.subtask_results:
    print(f"  - {st.description}: {st.confidence:.0%} 信心")
```

## 测试

```bash
# 运行测试
python tests/test_deep_think.py

# 仅测试基础功能
python tests/test_deep_think.py --test basic
```

## 性能预期

| 配置               | 响应时间  | LLM调用 | 成本估算     |
|------------------|-------|-------|----------|
| 快速模式 (3子任务, 无审查) | ~30s  | 5次    | < $0.005 |
| 标准模式 (5子任务, 有审查) | ~60s  | 8次    | < $0.01  |
| 深度模式 (8子任务, 有审查) | ~120s | 11次   | < $0.015 |

*基于 Cerebras 提供商估算,其他提供商可能不同*

## 故障排查

**问题: 响应时间过长**

- 解决: 减少子任务数量,禁用审查,或切换到更快的模型

**问题: JSON解析错误**

- 解决: 系统会自动使用容错模式,无需担心

**问题: 答案质量不理想**

- 解决: 重新表述问题使其更具体,或增加子任务数量

## 完整文档

详细文档请参考: `doc/deep_thinking_feature.md`

## 技术支持

遇到问题?

1. 查看日志输出 (console)
2. 运行测试脚本验证配置
3. 查阅完整文档
4. 检查 API 密钥配置

---

祝你使用愉快! 🚀
