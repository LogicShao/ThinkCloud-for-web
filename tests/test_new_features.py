"""
新功能测试 - 验证异步API、错误处理、缓存、会话持久化
"""

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 测试异步API服务


def test_async_api_service():
    """测试异步API服务"""
    print("\n" + "=" * 80)
    print("测试 1: 异步API服务")
    print("=" * 80)

    from src.async_api_service import async_api_service

    async def run_test():
        # 创建请求取消令牌
        request_id = async_api_service.create_cancellation_token()
        print(f"✓ 创建取消令牌: {request_id}")

        # 测试非流式调用
        messages = [{"role": "user", "content": "你好,请说'Hello World'"}]

        try:
            response = await async_api_service.chat_completion(
                messages=messages,
                model="llama-3.3-70b",
                timeout=30.0,
                request_id=request_id,
                enable_cache=True,
            )
            print(f"✓ 非流式响应: {response[:100]}...")

            # 测试缓存
            response2 = await async_api_service.chat_completion(
                messages=messages, model="llama-3.3-70b", enable_cache=True
            )
            print(f"✓ 缓存响应: {response2[:100]}...")

            # 获取缓存统计
            stats = async_api_service.get_cache_stats()
            print(f"✓ 缓存统计: {stats}")

        except Exception as e:
            print(f"✗ 测试失败: {e}")

    asyncio.run(run_test())


# 测试错误处理器


def test_error_handler():
    """测试全局错误处理器"""
    print("\n" + "=" * 80)
    print("测试 2: 全局错误处理器")
    print("=" * 80)

    from src.error_handler import error_handler

    # 模拟各种错误
    test_errors = [
        (Exception("authentication failed"), "openai"),
        (Exception("rate limit exceeded, retry after 60 seconds"), "deepseek"),
        (Exception("connection timeout"), "cerebras"),
        (Exception("InvalidApiKey"), "dashscope"),
    ]

    for error, provider in test_errors:
        formatted_error = error_handler.handle_error(
            error, provider=provider, model="test-model", operation="测试调用"
        )

        print(f"\n提供商: {provider}")
        print(f"错误类别: {formatted_error.context.category.value}")
        print(f"严重程度: {formatted_error.context.severity.value}")
        print(f"是否可重试: {formatted_error.context.is_retryable}")
        print(f"用户消息:\n{formatted_error.to_user_message()}")


# 测试缓存管理器


def test_cache_manager():
    """测试缓存管理器"""
    print("\n" + "=" * 80)
    print("测试 3: 缓存管理器")
    print("=" * 80)

    from src.cache_manager import CacheManager, generate_cache_key

    cache = CacheManager(
        max_size=10, max_memory_mb=1, default_ttl=timedelta(seconds=5), enable_persistence=False
    )

    # 测试基本操作
    cache.set("key1", "value1")
    print(f"✓ 设置缓存: key1 = value1")

    value = cache.get("key1")
    print(f"✓ 获取缓存: key1 = {value}")

    # 测试get_or_compute
    def compute_value():
        print("  计算新值...")
        return "computed_value"

    value = cache.get_or_compute("key2", compute_value)
    print(f"✓ 首次获取(计算): key2 = {value}")

    value = cache.get_or_compute("key2", compute_value)
    print(f"✓ 二次获取(缓存): key2 = {value}")

    # 测试统计
    stats = cache.get_stats()
    print(f"✓ 缓存统计: {stats}")

    # 测试缓存键生成
    key = generate_cache_key("api", model="gpt-4", temperature=0.7, top_p=0.9)
    print(f"✓ 生成缓存键: {key}")


# 测试会话存储


def test_session_store():
    """测试会话状态持久化"""
    print("\n" + "=" * 80)
    print("测试 4: 会话状态持久化")
    print("=" * 80)

    from src.session_store import ModelConfig, SessionStore

    # 创建临时存储
    temp_path = Path(".sessions_test")
    store = SessionStore(storage_path=temp_path, enable_disk_persistence=True)

    # 创建会话
    session = store.create_session()
    print(f"✓ 创建会话: {session.session_id}")

    # 更新对话历史
    store.update_chat_history("user", "你好")
    store.update_chat_history("assistant", "你好!有什么可以帮助你的吗?")
    print(f"✓ 添加对话历史: {len(session.chat_history)} 条消息")

    # 更新模型配置
    config = ModelConfig(provider="openai", model="gpt-4o", temperature=0.8, max_tokens=4096)
    store.update_model_config(config)
    print(f"✓ 更新模型配置: {config.provider}/{config.model}")

    # 保存会话
    store.save_session(session)
    print("✓ 保存会话到磁盘")

    # 加载会话
    session_id = session.session_id
    store.current_session = None  # 清空当前会话

    loaded_session = store.load_session(session_id)
    print(f"✓ 加载会话: {loaded_session.session_id}")
    print(f"  对话历史: {len(loaded_session.chat_history)} 条")
    print(f"  模型配置: {loaded_session.model_config.provider}/{loaded_session.model_config.model}")

    # 导出会话
    export_path = temp_path / "exported_session.json"
    store.export_session(session_id, export_path)
    print(f"✓ 导出会话到: {export_path}")

    # 列出所有会话
    sessions = store.list_sessions()
    print(f"✓ 会话列表: {len(sessions)} 个会话")

    # 清理
    store.delete_session(session_id)
    print("✓ 删除测试会话")


# 测试异步深度思考


def test_async_deep_think():
    """测试异步深度思考"""
    print("\n" + "=" * 80)
    print("测试 5: 异步深度思考（需要有效的API密钥）")
    print("=" * 80)

    from src.async_api_service import async_api_service
    from src.async_deep_think import AsyncDeepThinkOrchestrator

    async def run_test():
        # 检查是否有可用的提供商
        if not async_api_service.is_available():
            print("⚠ 没有可用的API提供商,跳过深度思考测试")
            return

        orchestrator = AsyncDeepThinkOrchestrator(
            async_api_service=async_api_service,
            model="llama-3.3-70b",
            max_subtasks=3,
            enable_review=False,  # 快速测试,禁用审查
            verbose=True,
            max_parallel_tasks=2,
        )

        question = "如何快速学习一门新的编程语言?"

        try:
            print(f"\n提问: {question}\n")
            result = await orchestrator.run(question)

            print(f"\n✓ 深度思考完成")
            print(f"  LLM调用次数: {result.total_llm_calls}")
            print(f"  子任务数: {len(result.subtask_results)}")
            print(f"  最终答案长度: {len(result.final_answer)} 字符")

        except Exception as e:
            print(f"✗ 深度思考测试失败: {e}")

    asyncio.run(run_test())


# 主测试函数


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("SimpleLLMFront 新功能测试套件")
    print("=" * 80)

    # 基础测试（不需要API密钥）
    test_error_handler()
    test_cache_manager()
    test_session_store()

    # API相关测试（需要API密钥）
    print("\n" + "=" * 80)
    print("以下测试需要配置有效的API密钥")
    print("=" * 80)

    try:
        # test_async_api_service()
        # test_async_deep_think()
        print("⚠ API测试已跳过（取消注释上面两行以运行）")
    except Exception as e:
        print(f"✗ API测试失败: {e}")

    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_tests()
