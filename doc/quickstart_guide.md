# 快速开始指南 - 使用新功能

> 简明教程,5分钟上手异步API、错误处理、缓存和会话持久化

---

## 📦 功能概览

✅ **异步处理** - 请求取消、超时控制、并发优化
✅ **错误处理** - 智能分类、用户友好、自动重试建议
✅ **缓存优化** - LRU策略、持久化、多层缓存
✅ **会话管理** - 自动保存、历史恢复、导入导出

---

## 🚀 快速示例

### 示例 1: 异步API调用

```python
from src.async_api_service import async_api_service
import asyncio

async def chat():
    # 简单调用
    response = await async_api_service.chat_completion(
        messages=[{"role": "user", "content": "你好"}],
        model="llama-3.3-70b"
    )
    print(response)

# 运行
asyncio.run(chat())
```

**特性:**

- ⏱️ 30秒自动超时
- 💾 自动缓存结果
- 🔄 支持中途取消

---

### 示例 2: 带超时和取消的调用

```python
async def chat_with_cancel():
    # 创建取消令牌
    request_id = async_api_service.create_cancellation_token()

    # 5秒后取消(模拟用户取消操作)
    asyncio.create_task(cancel_later(request_id, 5))

    try:
        response = await async_api_service.chat_completion(
            messages=[{"role": "user", "content": "写一篇长文章"}],
            model="llama-3.3-70b",
            timeout=10.0,  # 10秒超时
            request_id=request_id
        )
        print(response)
    except Exception as e:
        print(f"调用被中断: {e}")

async def cancel_later(request_id, delay):
    await asyncio.sleep(delay)
    async_api_service.cancel_request(request_id)
    print("已取消请求")

asyncio.run(chat_with_cancel())
```

---

### 示例 3: 智能错误处理

```python
from src.error_handler import error_handler

async def safe_chat():
    try:
        response = await async_api_service.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            model="gpt-4o"
        )
        return response
    except Exception as e:
        # 格式化错误
        error = error_handler.handle_error(
            error=e,
            provider="openai",
            model="gpt-4o",
            operation="聊天"
        )

        # 打印用户友好的错误消息
        print(error.to_user_message())

        # 自动重试逻辑
        if error.context.is_retryable:
            print(f"等待{error.context.retry_after}秒后重试...")
            await asyncio.sleep(error.context.retry_after)
            # 重新调用...

asyncio.run(safe_chat())
```

**输出示例:**

```
❌ **错误**: 聊天失败: 请求频率超出限制
📍 **提供商**: openai
🤖 **模型**: gpt-4o
💡 **建议**: 请稍后重试,或升级API套餐
⏱️ **重试**: 请等待 60 秒后重试
```

---

### 示例 4: 使用缓存加速

```python
from src.cache_manager import response_cache, generate_cache_key
from datetime import timedelta

# 生成缓存键
cache_key = generate_cache_key(
    "chat",
    model="llama-3.3-70b",
    messages=[{"role": "user", "content": "你好"}],
    temperature=0.7
)

# 检查缓存
cached_response = response_cache.get(cache_key)
if cached_response:
    print("使用缓存响应")
    print(cached_response)
else:
    # 调用API
    response = await async_api_service.chat_completion(...)

    # 缓存结果
    response_cache.set(cache_key, response, ttl=timedelta(minutes=10))
```

---

### 示例 5: 会话持久化

```python
from src.session_store import session_store, ModelConfig

# 创建会话
session = session_store.create_session()

# 添加对话
session_store.update_chat_history("user", "介绍一下Python")
session_store.update_chat_history("assistant", "Python是一门...")

# 保存模型配置
config = ModelConfig(
    provider="openai",
    model="gpt-4o",
    temperature=0.8
)
session_store.update_model_config(config)

# 自动保存到磁盘
session_store.save_session(session)

# 下次启动时加载
loaded = session_store.load_session(session.session_id)
print(f"恢复了{len(loaded.chat_history)}条对话历史")
```

---

### 示例 6: 异步深度思考

```python
from src.async_api_service import async_api_service
from src.async_deep_think import AsyncDeepThinkOrchestrator

async def deep_think():
    orchestrator = AsyncDeepThinkOrchestrator(
        async_api_service=async_api_service,
        model="qwen-3-235b-a22b-thinking-2507",
        max_subtasks=6,
        max_parallel_tasks=3,  # 3个子任务并行
        enable_review=True,
        verbose=True
    )

    result = await orchestrator.run("如何提高编程技能?")

    print(f"LLM调用: {result.total_llm_calls} 次")
    print(f"答案: {result.final_answer}")

asyncio.run(deep_think())
```

**性能对比:**

- 串行执行: ~120秒
- 并行执行: ~60秒 (提升50%)

---

## 🛠️ 常用代码片段

### 1. 批量API调用

```python
async def batch_chat(questions):
    tasks = []
    for q in questions:
        task = async_api_service.chat_completion(
            messages=[{"role": "user", "content": q}],
            model="llama-3.3-70b"
        )
        tasks.append(task)

    # 并发执行
    responses = await asyncio.gather(*tasks)
    return responses

questions = ["问题1", "问题2", "问题3"]
results = asyncio.run(batch_chat(questions))
```

---

### 2. 带重试的API调用

```python
from src.error_handler import error_handler

async def call_with_retry(max_retries=3):
    for i in range(max_retries):
        try:
            return await async_api_service.chat_completion(...)
        except Exception as e:
            error = error_handler.handle_error(e)

            if not error.context.is_retryable or i == max_retries - 1:
                raise

            print(f"重试 {i+1}/{max_retries}...")
            await asyncio.sleep(error.context.retry_after or 5)
```

---

### 3. 缓存装饰器

```python
from src.cache_manager import response_cache, generate_cache_key
from functools import wraps

def cached_api_call(ttl_minutes=10):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key = generate_cache_key(func.__name__, **kwargs)

            # 检查缓存
            cached = response_cache.get(key)
            if cached:
                return cached

            # 执行函数
            result = await func(*args, **kwargs)

            # 缓存结果
            response_cache.set(key, result, ttl=timedelta(minutes=ttl_minutes))
            return result

        return wrapper
    return decorator

@cached_api_call(ttl_minutes=15)
async def my_api_call(model, messages):
    return await async_api_service.chat_completion(
        messages=messages,
        model=model
    )
```

---

## 📊 性能优化技巧

### 1. 合理设置并发数

```python
# 根据API限流调整
async_api_service = AsyncAPIService(
    max_concurrent_requests=10  # OpenAI: 10-20, Cerebras: 5-10
)
```

---

### 2. 启用缓存

```python
# 高命中率场景(重复查询多)
response = await async_api_service.chat_completion(
    ...,
    enable_cache=True  # 默认开启
)

# 低命中率场景(每次查询不同)
response = await async_api_service.chat_completion(
    ...,
    enable_cache=False  # 节省内存
)
```

---

### 3. 定期清理缓存

```python
from src.cache_manager import response_cache

# 清理过期条目
expired_count = response_cache.cleanup_expired()
print(f"清理了{expired_count}个过期条目")

# 查看统计
stats = response_cache.get_stats()
print(f"命中率: {stats['hit_rate']}")
```

---

## ⚙️ 配置建议

### 开发环境

```python
# 异步API
AsyncAPIService(max_concurrent_requests=5)

# 缓存
CacheManager(
    max_size=100,
    max_memory_mb=10,
    default_ttl=timedelta(minutes=5),
    enable_persistence=False  # 开发环境可关闭持久化
)

# 深度思考
AsyncDeepThinkOrchestrator(
    max_parallel_tasks=2,
    enable_review=False,  # 快速测试
    verbose=True
)
```

---

### 生产环境

```python
# 异步API
AsyncAPIService(max_concurrent_requests=20)

# 缓存
CacheManager(
    max_size=1000,
    max_memory_mb=100,
    default_ttl=timedelta(minutes=10),
    enable_persistence=True  # 持久化
)

# 深度思考
AsyncDeepThinkOrchestrator(
    max_parallel_tasks=3,
    enable_review=True,
    verbose=False  # 减少日志
)
```

---

## 🐛 故障排查

### 问题 1: "No module named 'src'"

**解决:**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

### 问题 2: "This event loop is already running"

**解决:**

```python
# 不要在Jupyter/IPython中使用asyncio.run()
# 直接使用await

# 错误
# asyncio.run(main())

# 正确 (Jupyter)
await main()

# 正确 (普通脚本)
if __name__ == "__main__":
    asyncio.run(main())
```

---

### 问题 3: 缓存未命中

**检查:**

```python
from src.cache_manager import response_cache

# 查看统计
stats = response_cache.get_stats()
print(stats)

# 确认缓存键一致
key1 = generate_cache_key("api", model="gpt-4o", temp=0.7)
key2 = generate_cache_key("api", model="gpt-4o", temp=0.7)
assert key1 == key2  # 应该相等
```

---

## 📚 更多资源

- **完整文档**: `doc/advanced_features_improvement.md`
- **测试示例**: `tests/test_new_features.py`
- **源代码**: `src/async_api_service.py`, `src/error_handler.py` 等

---

**祝你使用愉快! 🎉**
