"""
异步API服务模块 - 处理异步多提供商API调用
支持请求取消、超时控制、并发限制
"""

import asyncio
import hashlib
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from .config import get_model_provider
from .providers import ProviderFactory


class CancellationToken:
    """请求取消令牌"""

    def __init__(self):
        self._cancelled = False
        self._lock = threading.Lock()

    def cancel(self):
        """取消请求"""
        with self._lock:
            self._cancelled = True

    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        with self._lock:
            return self._cancelled


class AsyncAPIService:
    """异步多提供商API服务类"""

    def __init__(self, max_concurrent_requests: int = 10):
        """
        初始化异步API服务

        Args:
            max_concurrent_requests: 最大并发请求数
        """
        self.providers = {}
        self._initialize_providers()
        # 缓存功能
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.cache_ttl = timedelta(minutes=10)
        # 性能监控
        self.metrics = defaultdict(list)
        # 并发控制
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        # 请求追踪
        self._active_requests: Dict[str, CancellationToken] = {}
        self._requests_lock = threading.Lock()

    def _initialize_providers(self):
        """初始化所有提供商"""
        available_providers = ProviderFactory.get_available_providers()

        for provider_name in available_providers:
            try:
                provider = ProviderFactory.create_provider(provider_name)
                if provider.is_available():
                    self.providers[provider_name] = provider
                    print(f"[SUCCESS] {provider_name} 提供商初始化成功")
                else:
                    print(f"[FAILED] {provider_name} 提供商初始化失败")
            except Exception as e:
                print(f"[ERROR] 初始化 {provider_name} 提供商时出错: {e}")

    def _generate_cache_key(self, messages, model, **kwargs):
        """生成缓存键"""
        cache_input = {
            "messages": messages,
            "model": model,
            "system_instruction": kwargs.get("system_instruction"),
            "temperature": kwargs.get("temperature"),
            "top_p": kwargs.get("top_p"),
            "max_tokens": kwargs.get("max_tokens"),
        }
        cache_str = str(sorted(cache_input.items()))
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _generate_request_id(self) -> str:
        """生成唯一请求ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()

    def _get_from_cache(self, key):
        """从缓存获取结果"""
        with self.cache_lock:
            if key in self.cache:
                result, timestamp = self.cache[key]
                if datetime.now() - timestamp < self.cache_ttl:
                    return result
                else:
                    del self.cache[key]
        return None

    def _set_to_cache(self, key, value):
        """设置缓存"""
        with self.cache_lock:
            self.cache[key] = (value, datetime.now())

    def create_cancellation_token(self) -> str:
        """
        创建请求取消令牌

        Returns:
            str: 请求ID
        """
        request_id = self._generate_request_id()
        with self._requests_lock:
            self._active_requests[request_id] = CancellationToken()
        return request_id

    def cancel_request(self, request_id: str):
        """
        取消指定请求

        Args:
            request_id: 请求ID
        """
        with self._requests_lock:
            if request_id in self._active_requests:
                self._active_requests[request_id].cancel()
                print(f"[CANCEL] 请求 {request_id} 已取消")

    def _cleanup_request(self, request_id: str):
        """清理已完成的请求"""
        with self._requests_lock:
            if request_id in self._active_requests:
                del self._active_requests[request_id]

    async def chat_completion(
        self,
        messages: List[Dict],
        model: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stream: bool = False,
        timeout: Optional[float] = 120.0,
        request_id: Optional[str] = None,
        enable_cache: bool = True,
        **kwargs,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        异步调用聊天完成API

        Args:
            messages: 消息列表
            model: 模型名称
            system_instruction: 系统提示词
            temperature: 温度参数
            top_p: 核采样参数
            max_tokens: 最大生成token数
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
            stream: 是否使用流式传输
            timeout: 超时时间(秒)
            request_id: 请求ID(用于取消请求)
            enable_cache: 是否启用缓存
            **kwargs: 其他参数

        Returns:
            str: API回复内容（非流式），或异步生成器（流式）
        """
        # 如果没有提供request_id，创建一个新的
        if request_id is None:
            request_id = self.create_cancellation_token()

        try:
            # 使用信号量控制并发
            async with self.semaphore:
                if stream:
                    return self._chat_completion_stream(
                        messages=messages,
                        model=model,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty,
                        timeout=timeout,
                        request_id=request_id,
                        **kwargs,
                    )
                else:
                    return await self._chat_completion_async(
                        messages=messages,
                        model=model,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty,
                        timeout=timeout,
                        request_id=request_id,
                        enable_cache=enable_cache,
                        **kwargs,
                    )
        finally:
            self._cleanup_request(request_id)

    async def _chat_completion_async(
        self,
        messages: List[Dict],
        model: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        timeout: Optional[float] = 120.0,
        request_id: Optional[str] = None,
        enable_cache: bool = True,
        **kwargs,
    ) -> str:
        """异步非流式传输实现"""
        # 检查缓存
        if enable_cache:
            cache_key = self._generate_cache_key(
                messages,
                model,
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                print("[CACHE] 使用缓存响应")
                return cached_result

        # 获取提供商
        provider_name = get_model_provider(model)
        if not provider_name:
            return f"错误: 不支持模型 '{model}'。请检查模型名称是否正确。"

        if provider_name not in self.providers:
            return f"错误: 提供商 '{provider_name}' 未配置或不可用。请检查{provider_name.upper()}_API_KEY环境变量。"

        provider = self.providers[provider_name]
        if not provider.is_available():
            return f"错误: {provider_name} 提供商不可用。请检查配置。"

        try:
            # 在线程池中执行同步API调用
            loop = asyncio.get_event_loop()

            async def call_with_cancellation():
                """支持取消的API调用包装"""

                # 定期检查取消状态
                def check_cancellation():
                    with self._requests_lock:
                        token = self._active_requests.get(request_id)
                        if token and token.is_cancelled():
                            raise asyncio.CancelledError("请求已被用户取消")

                check_cancellation()

                # 执行API调用
                result = await loop.run_in_executor(
                    None,
                    lambda: provider.chat_completion(
                        messages=messages,
                        model=model,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty,
                        stream=False,
                        **kwargs,
                    ),
                )
                return result

            # 应用超时控制
            if timeout:
                result = await asyncio.wait_for(call_with_cancellation(), timeout=timeout)
            else:
                result = await call_with_cancellation()

            # 确保结果是字符串
            if hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
                # 同步代码中已经处理了这种情况,这里应该不会发生
                result = str(result)

            # 存入缓存
            if enable_cache:
                self._set_to_cache(cache_key, result)

            return result

        except asyncio.TimeoutError:
            error_msg = f"{provider_name} API调用超时（{timeout}秒）"
            print(f"[TIMEOUT] {error_msg}")
            return error_msg
        except asyncio.CancelledError:
            error_msg = "请求已被用户取消"
            print(f"[CANCELLED] {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"{provider_name} API调用失败: {e!s}"
            print(f"[ERROR] {error_msg}")
            return error_msg

    async def _chat_completion_stream(
        self,
        messages: List[Dict],
        model: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        timeout: Optional[float] = 120.0,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """异步流式传输实现"""
        provider_name = get_model_provider(model)

        if not provider_name:
            yield f"错误: 不支持模型 '{model}'。"
            return

        if provider_name not in self.providers:
            yield f"错误: 提供商 '{provider_name}' 未配置或不可用。"
            return

        provider = self.providers[provider_name]
        if not provider.is_available():
            yield f"错误: {provider_name} 提供商不可用。"
            return

        try:
            # 在线程池中执行同步流式API调用
            loop = asyncio.get_event_loop()

            # 获取生成器
            stream_generator = await loop.run_in_executor(
                None,
                lambda: provider.chat_completion(
                    messages=messages,
                    model=model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stream=True,
                    **kwargs,
                ),
            )

            # 异步迭代流式响应
            start_time = asyncio.get_event_loop().time()
            for chunk in stream_generator:
                # 检查取消状态
                with self._requests_lock:
                    token = self._active_requests.get(request_id)
                    if token and token.is_cancelled():
                        print(f"[CANCELLED] 流式请求 {request_id} 已取消")
                        break

                # 检查超时
                if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                    print(f"[TIMEOUT] 流式请求超时（{timeout}秒）")
                    break

                yield chunk
                # 让出控制权
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            print(f"[CANCELLED] 流式请求 {request_id} 已取消")
        except Exception as e:
            error_msg = f"{provider_name} 流式API调用失败: {e!s}"
            print(f"[ERROR] {error_msg}")
            yield error_msg

    def is_available(self, provider_name: Optional[str] = None) -> bool:
        """
        检查API服务是否可用

        Args:
            provider_name: 指定提供商，None表示检查是否有任何提供商可用

        Returns:
            bool: 服务是否可用
        """
        if provider_name:
            return provider_name in self.providers and self.providers[provider_name].is_available()
        return len(self.providers) > 0

    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        return list(self.providers.keys())

    def get_provider_status(self) -> str:
        """获取所有提供商的状态信息"""
        status_info = []
        for provider_name, provider in self.providers.items():
            status = "[OK] 可用" if provider.is_available() else "[FAIL] 不可用"
            status_info.append(f"{provider_name}: {status}")

        if not status_info:
            return "[FAIL] 没有可用的提供商"

        return " | ".join(status_info)

    def clear_cache(self):
        """清空缓存"""
        with self.cache_lock:
            self.cache.clear()
            print("[CACHE] 缓存已清空")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.cache_lock:
            total_items = len(self.cache)
            valid_items = sum(
                1
                for _, (_, timestamp) in self.cache.items()
                if datetime.now() - timestamp < self.cache_ttl
            )
            return {
                "total_items": total_items,
                "valid_items": valid_items,
                "expired_items": total_items - valid_items,
                "cache_ttl_minutes": self.cache_ttl.total_seconds() / 60,
            }


# 全局异步API服务实例
async_api_service = AsyncAPIService()
