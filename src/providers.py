"""
提供商模块 - 定义AI提供商接口和具体实现
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from cerebras.cloud.sdk import Cerebras
from openai import OpenAI

from .config import get_provider_config


class BaseProvider(ABC):
    """AI提供商抽象基类"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.client = None
        self._initialize_client()

    @abstractmethod
    def _initialize_client(self):
        """初始化客户端"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查提供商是否可用"""
        pass

    @abstractmethod
    def chat_completion(
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
        **kwargs,
    ):
        """
        调用聊天完成API

        Args:
            messages: 消息列表
            model: 模型名称
            system_instruction: 系统提示词
            temperature: 温度参数 (0.0-2.0)
            top_p: 核采样参数 (0.0-1.0)
            max_tokens: 最大生成token数
            frequency_penalty: 频率惩罚 (-2.0-2.0)
            presence_penalty: 存在惩罚 (-2.0-2.0)
            stream: 是否使用流式传输
            **kwargs: 其他参数

        Returns:
            str: API回复内容（非流式），或生成器（流式）
        """
        pass


class CerebrasProvider(BaseProvider):
    """Cerebras提供商实现"""

    def __init__(self):
        super().__init__("cerebras")

    def _initialize_client(self):
        """初始化Cerebras客户端"""
        config = get_provider_config(self.provider_name)
        api_key = config.get("api_key")

        if not api_key:
            return

        try:
            self.client = Cerebras(api_key=api_key)
        except Exception as e:
            print(f"初始化Cerebras客户端失败: {e}")

    def is_available(self) -> bool:
        """检查Cerebras服务是否可用"""
        return self.client is not None

    def chat_completion(
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
        **kwargs,
    ):
        """调用Cerebras聊天完成API"""
        if not self.is_available():
            error_msg = f"错误: 无法初始化{self.provider_name}客户端。请检查{self.provider_name.upper()}_API_KEY环境变量。"
            if stream:
                yield error_msg
                return
            return error_msg

        try:
            # 如果有系统提示词，添加到消息列表开头
            api_messages = messages.copy()
            if system_instruction:
                api_messages.insert(0, {"role": "system", "content": system_instruction})

            # 构建API参数
            api_params = {
                "messages": api_messages,
                "model": model,
                "stream": stream,
            }

            # 添加可选参数
            if temperature is not None:
                api_params["temperature"] = temperature
            if top_p is not None:
                api_params["top_p"] = top_p
            if max_tokens is not None:
                api_params["max_tokens"] = max_tokens
            if frequency_penalty is not None:
                api_params["frequency_penalty"] = frequency_penalty
            if presence_penalty is not None:
                api_params["presence_penalty"] = presence_penalty

            chat_completion = self.client.chat.completions.create(**api_params)

            if stream:
                # 流式传输
                for chunk in chat_completion:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                # 非流式传输
                return chat_completion.choices[0].message.content

        except Exception as e:
            error_msg = f"{self.provider_name} API调用失败: {e!s}"
            print(error_msg)
            if stream:
                yield error_msg
            else:
                return error_msg


class DeepSeekProvider(BaseProvider):
    """DeepSeek提供商实现"""

    def __init__(self):
        super().__init__("deepseek")

    def _initialize_client(self):
        """初始化DeepSeek客户端"""
        config = get_provider_config(self.provider_name)
        api_key = config.get("api_key")
        base_url = config.get("base_url")

        if not api_key:
            return

        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"初始化DeepSeek客户端失败: {e}")

    def is_available(self) -> bool:
        """检查DeepSeek服务是否可用"""
        return self.client is not None

    def chat_completion(
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
        **kwargs,
    ):
        """调用DeepSeek聊天完成API"""
        if stream:
            # 流式传输 - 调用生成器方法
            return self._chat_completion_stream(
                messages,
                model,
                system_instruction,
                temperature,
                top_p,
                max_tokens,
                frequency_penalty,
                presence_penalty,
                **kwargs,
            )
        else:
            # 非流式传输 - 调用普通方法（没有yield，不是生成器）
            return self._chat_completion_sync(
                messages,
                model,
                system_instruction,
                temperature,
                top_p,
                max_tokens,
                frequency_penalty,
                presence_penalty,
                **kwargs,
            )

    def _chat_completion_sync(
        self,
        messages: List[Dict],
        model: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        **kwargs,
    ):
        """非流式聊天完成（普通方法，非生成器）"""
        if not self.is_available():
            return f"错误: 无法初始化{self.provider_name}客户端。请检查{self.provider_name.upper()}_API_KEY环境变量。"

        try:
            # 构建消息
            api_messages = messages.copy()
            if system_instruction:
                api_messages.insert(0, {"role": "system", "content": system_instruction})

            # 构建API参数
            api_params = {"model": model, "messages": api_messages, "stream": False}
            if temperature is not None:
                api_params["temperature"] = temperature
            if top_p is not None:
                api_params["top_p"] = top_p
            if max_tokens is not None:
                api_params["max_tokens"] = max_tokens
            if frequency_penalty is not None:
                api_params["frequency_penalty"] = frequency_penalty
            if presence_penalty is not None:
                api_params["presence_penalty"] = presence_penalty

            # 调用API
            response = self.client.chat.completions.create(**api_params)

            # 调试信息

            # 提取内容
            if not hasattr(response, "choices") or len(response.choices) == 0:
                return "错误: API响应格式异常"

            content = response.choices[0].message.content
            if content is None:
                return "错误: API返回空内容"

            return content

        except Exception as e:
            return f"{self.provider_name} API调用失败: {e!s}"

    def _chat_completion_stream(
        self,
        messages: List[Dict],
        model: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        **kwargs,
    ):
        """流式聊天完成（生成器方法）"""
        if not self.is_available():
            yield f"错误: 无法初始化{self.provider_name}客户端。"
            return

        try:
            # 构建消息
            api_messages = messages.copy()
            if system_instruction:
                api_messages.insert(0, {"role": "system", "content": system_instruction})

            # 构建API参数
            api_params = {"model": model, "messages": api_messages, "stream": True}
            if temperature is not None:
                api_params["temperature"] = temperature
            if top_p is not None:
                api_params["top_p"] = top_p
            if max_tokens is not None:
                api_params["max_tokens"] = max_tokens
            if frequency_penalty is not None:
                api_params["frequency_penalty"] = frequency_penalty
            if presence_penalty is not None:
                api_params["presence_penalty"] = presence_penalty

            # 调用API
            response = self.client.chat.completions.create(**api_params)

            # 流式传输
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"{self.provider_name} API调用失败: {e!s}"


class OpenAIProvider(BaseProvider):
    """OpenAI提供商实现"""

    def __init__(self):
        super().__init__("openai")

    def _initialize_client(self):
        """初始化OpenAI客户端"""
        config = get_provider_config(self.provider_name)
        api_key = config.get("api_key")
        base_url = config.get("base_url")

        if not api_key:
            return

        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"初始化OpenAI客户端失败: {e}")

    def is_available(self) -> bool:
        """检查OpenAI服务是否可用"""
        return self.client is not None

    def chat_completion(
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
        **kwargs,
    ):
        """调用OpenAI聊天完成API"""
        if not self.is_available():
            error_msg = f"错误: 无法初始化{self.provider_name}客户端。请检查{self.provider_name.upper()}_API_KEY环境变量。"
            if stream:
                yield error_msg
                return
            return error_msg

        try:
            # 如果有系统提示词，添加到消息列表开头
            api_messages = messages.copy()
            if system_instruction:
                api_messages.insert(0, {"role": "system", "content": system_instruction})

            # 构建API参数
            api_params = {"model": model, "messages": api_messages, "stream": stream}

            # 添加可选参数
            if temperature is not None:
                api_params["temperature"] = temperature
            if top_p is not None:
                api_params["top_p"] = top_p
            if max_tokens is not None:
                api_params["max_tokens"] = max_tokens
            if frequency_penalty is not None:
                api_params["frequency_penalty"] = frequency_penalty
            if presence_penalty is not None:
                api_params["presence_penalty"] = presence_penalty

            response = self.client.chat.completions.create(**api_params)

            if stream:
                # 流式传输
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                # 非流式传输 - 直接访问response.choices
                # 注意：ChatCompletion对象虽然有__iter__方法，但不应该被迭代
                # 应该直接访问choices属性

                # 确保response有choices属性
                if not hasattr(response, "choices"):
                    print(f"[ERROR] {self.provider_name} response没有choices属性!")
                    print(f"[ERROR] Response type: {type(response)}")
                    return "错误: API响应格式异常（无choices属性）"

                if len(response.choices) == 0:
                    print(f"[ERROR] {self.provider_name} response.choices为空!")
                    return "错误: API响应格式异常（choices为空）"

                if not hasattr(response.choices[0], "message"):
                    print(f"[ERROR] {self.provider_name} choices[0]没有message属性!")
                    return "错误: API响应格式异常（无message属性）"

                content = response.choices[0].message.content
                if content is None:
                    print(f"[ERROR] {self.provider_name} message.content为None!")
                    return "错误: API返回空内容"

                print(f"[DEBUG] {self.provider_name} 成功提取内容，长度: {len(content)}")
                return content

        except Exception as e:
            error_msg = f"{self.provider_name} API调用失败: {e!s}"
            print(error_msg)
            if stream:
                yield error_msg
            else:
                return error_msg


class DashScopeProvider(BaseProvider):
    """DashScope（阿里云百炼）提供商实现"""

    def __init__(self):
        super().__init__("dashscope")

    def _initialize_client(self):
        """初始化DashScope客户端"""
        config = get_provider_config(self.provider_name)
        api_key = config.get("api_key")
        base_url = config.get("base_url")

        if not api_key:
            return

        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"初始化DashScope客户端失败: {e}")

    def is_available(self) -> bool:
        """检查DashScope服务是否可用"""
        return self.client is not None

    def chat_completion(
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
        **kwargs,
    ):
        """调用DashScope聊天完成API"""
        if not self.is_available():
            error_msg = f"错误: 无法初始化{self.provider_name}客户端。请检查{self.provider_name.upper()}_API_KEY环境变量。"
            if stream:
                yield error_msg
                return
            return error_msg

        try:
            # 如果有系统提示词，添加到消息列表开头
            api_messages = messages.copy()
            if system_instruction:
                api_messages.insert(0, {"role": "system", "content": system_instruction})

            # 构建API参数
            api_params = {"model": model, "messages": api_messages, "stream": stream}

            # 添加可选参数
            if temperature is not None:
                api_params["temperature"] = temperature
            if top_p is not None:
                api_params["top_p"] = top_p
            if max_tokens is not None:
                api_params["max_tokens"] = max_tokens
            # DashScope 可能不支持 frequency_penalty 和 presence_penalty
            # 如果支持，取消下面的注释
            # if frequency_penalty is not None:
            #     api_params["frequency_penalty"] = frequency_penalty
            # if presence_penalty is not None:
            #     api_params["presence_penalty"] = presence_penalty

            response = self.client.chat.completions.create(**api_params)

            if stream:
                # 流式传输
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                # 非流式传输 - 直接访问response.choices
                # 注意：ChatCompletion对象虽然有__iter__方法，但不应该被迭代
                # 应该直接访问choices属性

                # 确保response有choices属性
                if not hasattr(response, "choices"):
                    print(f"[ERROR] {self.provider_name} response没有choices属性!")
                    print(f"[ERROR] Response type: {type(response)}")
                    return "错误: API响应格式异常（无choices属性）"

                if len(response.choices) == 0:
                    print(f"[ERROR] {self.provider_name} response.choices为空!")
                    return "错误: API响应格式异常（choices为空）"

                if not hasattr(response.choices[0], "message"):
                    print(f"[ERROR] {self.provider_name} choices[0]没有message属性!")
                    return "错误: API响应格式异常（无message属性）"

                content = response.choices[0].message.content
                if content is None:
                    print(f"[ERROR] {self.provider_name} message.content为None!")
                    return "错误: API返回空内容"

                print(f"[DEBUG] {self.provider_name} 成功提取内容，长度: {len(content)}")
                return content

        except Exception as e:
            error_msg = f"{self.provider_name} API调用失败: {e!s}"
            print(error_msg)
            if stream:
                yield error_msg
            else:
                return error_msg


class KimiProvider(BaseProvider):
    """Kimi（月之暗面）提供商实现"""

    def __init__(self):
        super().__init__("kimi")

    def _initialize_client(self):
        """初始化Kimi客户端"""
        config = get_provider_config(self.provider_name)
        api_key = config.get("api_key")
        base_url = config.get("base_url")

        if not api_key:
            return

        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"初始化Kimi客户端失败: {e}")

    def is_available(self) -> bool:
        """检查Kimi服务是否可用"""
        return self.client is not None

    def chat_completion(
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
        **kwargs,
    ):
        """调用Kimi聊天完成API"""
        if not self.is_available():
            error_msg = f"错误: 无法初始化{self.provider_name}客户端。请检查{self.provider_name.upper()}_API_KEY环境变量。"
            if stream:
                yield error_msg
                return
            return error_msg

        try:
            # 如果有系统提示词，添加到消息列表开头
            api_messages = messages.copy()
            if system_instruction:
                api_messages.insert(0, {"role": "system", "content": system_instruction})

            # 构建API参数
            api_params = {"model": model, "messages": api_messages, "stream": stream}

            # 添加可选参数
            if temperature is not None:
                api_params["temperature"] = temperature
            if top_p is not None:
                api_params["top_p"] = top_p
            if max_tokens is not None:
                api_params["max_tokens"] = max_tokens
            if frequency_penalty is not None:
                api_params["frequency_penalty"] = frequency_penalty
            if presence_penalty is not None:
                api_params["presence_penalty"] = presence_penalty

            response = self.client.chat.completions.create(**api_params)

            if stream:
                # 流式传输
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                # 非流式传输 - 直接访问response.choices
                # 注意：ChatCompletion对象虽然有__iter__方法，但不应该被迭代
                # 应该直接访问choices属性

                # 确保response有choices属性
                if not hasattr(response, "choices"):
                    print(f"[ERROR] {self.provider_name} response没有choices属性!")
                    print(f"[ERROR] Response type: {type(response)}")
                    return "错误: API响应格式异常（无choices属性）"

                if len(response.choices) == 0:
                    print(f"[ERROR] {self.provider_name} response.choices为空!")
                    return "错误: API响应格式异常（choices为空）"

                if not hasattr(response.choices[0], "message"):
                    print(f"[ERROR] {self.provider_name} choices[0]没有message属性!")
                    return "错误: API响应格式异常（无message属性）"

                content = response.choices[0].message.content
                if content is None:
                    print(f"[ERROR] {self.provider_name} message.content为None!")
                    return "错误: API返回空内容"

                print(f"[DEBUG] {self.provider_name} 成功提取内容，长度: {len(content)}")
                return content

        except Exception as e:
            error_msg = f"{self.provider_name} API调用失败: {e!s}"
            print(error_msg)
            if stream:
                yield error_msg
            else:
                return error_msg


class ProviderFactory:
    """提供商工厂类"""

    _providers = {
        "cerebras": CerebrasProvider,
        "deepseek": DeepSeekProvider,
        "openai": OpenAIProvider,
        "dashscope": DashScopeProvider,
        "kimi": KimiProvider,
    }

    @classmethod
    def create_provider(cls, provider_name: str) -> BaseProvider:
        """
        创建提供商实例

        Args:
            provider_name: 提供商名称

        Returns:
            BaseProvider: 提供商实例
        """
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"不支持的提供商: {provider_name}")

        return provider_class()

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """获取可用的提供商列表"""
        from .config import get_enabled_providers

        return get_enabled_providers()

    @classmethod
    def register_provider(cls, provider_name: str, provider_class):
        """注册新的提供商"""
        if not issubclass(provider_class, BaseProvider):
            raise ValueError("提供商类必须继承自BaseProvider")
        cls._providers[provider_name] = provider_class
