"""
API服务模块 - 处理多提供商API调用
"""

import hashlib
import threading
from collections import defaultdict
from datetime import datetime, timedelta

from .config import get_model_provider
from .providers import ProviderFactory


class MultiProviderAPIService:
    """多提供商API服务类"""

    def __init__(self):
        self.providers = {}
        self._initialize_providers()
        # 添加缓存功能
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.cache_ttl = timedelta(minutes=10)  # 缓存有效期10分钟
        # 性能监控
        self.metrics = defaultdict(list)

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

    def is_available(self, provider_name=None):
        """
        检查API服务是否可用

        Args:
            provider_name: 指定提供商，None表示检查是否有任何提供商可用

        Returns:
            bool: 服务是否可用
        """
        if provider_name:
            return provider_name in self.providers and self.providers[provider_name].is_available()

        # 检查是否有任何提供商可用
        return len(self.providers) > 0

    def get_available_providers(self):
        """获取可用的提供商列表"""
        return list(self.providers.keys())

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

    def _get_from_cache(self, key):
        """从缓存获取结果"""
        with self.cache_lock:
            if key in self.cache:
                result, timestamp = self.cache[key]
                if datetime.now() - timestamp < self.cache_ttl:
                    return result
                else:
                    # 清除过期缓存
                    del self.cache[key]
        return None

    def _set_to_cache(self, key, value):
        """设置缓存"""
        with self.cache_lock:
            self.cache[key] = (value, datetime.now())

    def chat_completion(
            self,
            messages,
            model,
            system_instruction=None,
            temperature=None,
            top_p=None,
            max_tokens=None,
            frequency_penalty=None,
            presence_penalty=None,
            stream=False,
            **kwargs,
    ):
        """
        调用聊天完成API

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
            **kwargs: 其他参数

        Returns:
            str: API回复内容（非流式），或生成器（流式）
        """
        # 根据 stream 参数决定调用哪个方法
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
                **kwargs,
            )
        else:
            return self._chat_completion_sync(
                messages=messages,
                model=model,
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                **kwargs,
            )

    def _chat_completion_stream(
            self,
            messages,
            model,
            system_instruction=None,
            temperature=None,
            top_p=None,
            max_tokens=None,
            frequency_penalty=None,
            presence_penalty=None,
            **kwargs,
    ):
        """流式传输实现（生成器）"""
        # 根据模型确定提供商
        provider_name = get_model_provider(model)

        if not provider_name:
            error_msg = f"错误: 不支持模型 '{model}'。请检查模型名称是否正确。"
            yield error_msg
            return

        if provider_name not in self.providers:
            error_msg = f"错误: 提供商 '{provider_name}' 未配置或不可用。请检查{provider_name.upper()}_API_KEY环境变量。"
            yield error_msg
            return

        provider = self.providers[provider_name]

        if not provider.is_available():
            error_msg = f"错误: {provider_name} 提供商不可用。请检查配置。"
            yield error_msg
            return

        try:
            result = provider.chat_completion(
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
            )

            # 流式传输 - 直接传递生成器
            yield from result
        except Exception as e:
            error_msg = f"{provider_name} API调用失败: {e!s}"
            print(error_msg)
            yield error_msg

    def _chat_completion_sync(
            self,
            messages,
            model,
            system_instruction=None,
            temperature=None,
            top_p=None,
            max_tokens=None,
            frequency_penalty=None,
            presence_penalty=None,
            **kwargs,
    ):
        """非流式传输实现（返回字符串）"""
        # 使用缓存
        cache_key = self._generate_cache_key(
            messages,
            model,
            system_instruction=system_instruction,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

        # 尝试从缓存获取
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            print("[CACHE] 使用缓存响应")
            return cached_result

        # 根据模型确定提供商
        provider_name = get_model_provider(model)

        if not provider_name:
            error_msg = f"错误: 不支持模型 '{model}'。请检查模型名称是否正确。"
            return error_msg

        if provider_name not in self.providers:
            error_msg = f"错误: 提供商 '{provider_name}' 未配置或不可用。请检查{provider_name.upper()}_API_KEY环境变量。"
            return error_msg

        provider = self.providers[provider_name]

        if not provider.is_available():
            error_msg = f"错误: {provider_name} 提供商不可用。请检查配置。"
            return error_msg

        try:
            result = provider.chat_completion(
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
            )

            # 确保结果是字符串而非生成器（某些提供商可能错误返回生成器）
            if hasattr(result, '__iter__') and not isinstance(result, (str, bytes)):
                print(f"[WARN] {provider_name} 在非流式模式下返回了生成器，正在转换...")
                print(f"[DEBUG] Response type: {type(result)}")
                print(f"[DEBUG] Response dir: {[attr for attr in dir(result) if not attr.startswith('_')][:10]}")

                # 尝试直接获取内容（如果这是ChatCompletion对象而不是生成器）
                if hasattr(result, 'choices'):
                    print(f"[DEBUG] Response has 'choices' attribute, extracting directly...")
                    try:
                        if len(result.choices) > 0 and hasattr(result.choices[0], 'message'):
                            direct_content = result.choices[0].message.content
                            if direct_content:
                                print(f"[INFO] 直接提取成功，内容长度: {len(direct_content)}")
                                result = direct_content
                                # 跳过生成器迭代
                                self._set_to_cache(cache_key, result)
                                return result
                    except Exception as e:
                        print(f"[WARN] 直接提取失败: {e}")

                chunks = []
                try:
                    for chunk in result:
                        # 尝试多种方式提取内容
                        if isinstance(chunk, str):
                            chunks.append(chunk)
                        elif hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                            # OpenAI ChatCompletionChunk格式
                            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                                content = chunk.choices[0].delta.content
                                if content:
                                    chunks.append(content)
                            elif hasattr(chunk.choices[0], 'message') and hasattr(chunk.choices[0].message, 'content'):
                                content = chunk.choices[0].message.content
                                if content:
                                    chunks.append(content)
                        elif hasattr(chunk, 'content'):
                            chunks.append(chunk.content if chunk.content else '')
                        elif hasattr(chunk, 'text'):
                            chunks.append(chunk.text if chunk.text else '')
                        else:
                            chunks.append(str(chunk))

                    result = ''.join(chunks)
                    print(f"[INFO] 生成器转换完成，共{len(chunks)}个chunk，总长度: {len(result)}")
                except Exception as convert_error:
                    print(f"[ERROR] 生成器转换失败: {convert_error}")
                    result = f"错误: 无法转换提供商响应 - {convert_error}"

            # 非流式传输 - 将结果存入缓存
            self._set_to_cache(cache_key, result)
            return result

        except Exception as e:
            error_msg = f"{provider_name} API调用失败: {e!s}"
            print(error_msg)
            return error_msg

    def get_provider_status(self):
        """获取所有提供商的状态信息"""
        status_info = []
        for provider_name, provider in self.providers.items():
            status = "[OK] 可用" if provider.is_available() else "[FAIL] 不可用"
            status_info.append(f"{provider_name}: {status}")

        if not status_info:
            return "[FAIL] 没有可用的提供商"

        return " | ".join(status_info)


# 全局API服务实例
api_service = MultiProviderAPIService()
