"""
响应处理器 - 处理LLM响应逻辑
包含标准模式响应处理和深度思考模式响应处理
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from src.api_service import api_service
from src.chat_manager import ChatManager
from src.deep_think import DeepThinkOrchestrator, format_deep_think_result


class ResponseHandler:
    """标准响应处理器"""

    def __init__(self, chat_manager: ChatManager):
        """
        初始化响应处理器

        Args:
            chat_manager: 聊天管理器实例
        """
        self.chat_manager = chat_manager

    def handle_standard_response(
            self,
            history: List[Dict[str, Any]],
            model: str,
            enable_stream: bool,
            start_time: datetime,
            system_instruction: Optional[str] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            max_tokens: Optional[int] = None,
            frequency_penalty: Optional[float] = None,
            presence_penalty: Optional[float] = None,
    ):
        """
        处理标准模式响应（流式或非流式）

        Args:
            history: 对话历史
            model: 模型名称
            enable_stream: 是否启用流式传输
            start_time: 开始时间
            system_instruction: 系统提示词
            temperature: 温度参数
            top_p: Top P参数
            max_tokens: 最大Token数
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚

        Yields:
            List[Dict]: 更新后的对话历史
        """
        # 构建API消息
        api_messages = []
        for msg in history:
            if msg["role"] in ["user", "assistant"]:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

        time_str = start_time.strftime("%H:%M:%S")

        if enable_stream:
            # 流式传输模式
            yield from self._handle_streaming_response(
                history=history,
                api_messages=api_messages,
                model=model,
                start_time=start_time,
                time_str=time_str,
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
        else:
            # 非流式传输模式
            yield from self._handle_non_streaming_response(
                history=history,
                api_messages=api_messages,
                model=model,
                start_time=start_time,
                time_str=time_str,
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )

    def _handle_streaming_response(
            self,
            history: List[Dict[str, Any]],
            api_messages: List[Dict[str, str]],
            model: str,
            start_time: datetime,
            time_str: str,
            system_instruction: Optional[str] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            max_tokens: Optional[int] = None,
            frequency_penalty: Optional[float] = None,
            presence_penalty: Optional[float] = None,
    ):
        """处理流式传输响应"""
        # 先添加一个空的助手消息
        history.append(
            {
                "role": "assistant",
                "content": "",
                "metadata": {"timestamp": time_str, "title": f"🤖 {time_str}"},
            }
        )

        response_text = ""
        try:
            # 调用API，启用流式传输
            stream_generator = api_service.chat_completion(
                messages=api_messages,
                model=model,
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens if max_tokens else None,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stream=True,
            )

            # 逐步更新回复
            for chunk in stream_generator:
                response_text += chunk
                # 更新最后一条助手消息
                history[-1]["content"] = response_text
                yield history

            # 流式传输完成，添加响应时间
            response_text = self._add_duration_to_response(response_text, start_time)
            history[-1]["content"] = response_text
            yield history

        except Exception as e:
            error_msg = f"流式传输失败: {e!s}"
            error_msg = self._add_duration_to_response(error_msg, start_time)
            history[-1]["content"] = error_msg
            response_text = error_msg
            yield history

        # 添加完整回复到聊天历史管理器
        self.chat_manager.add_message("assistant", response_text)

    def _handle_non_streaming_response(
            self,
            history: List[Dict[str, Any]],
            api_messages: List[Dict[str, str]],
            model: str,
            start_time: datetime,
            time_str: str,
            system_instruction: Optional[str] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            max_tokens: Optional[int] = None,
            frequency_penalty: Optional[float] = None,
            presence_penalty: Optional[float] = None,
    ):
        """处理非流式传输响应"""
        try:
            # 调用API
            response = api_service.chat_completion(
                messages=api_messages,
                model=model,
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens if max_tokens else None,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stream=False,
            )
        except Exception as e:
            response = f"API调用失败: {e!s}"

        # 添加响应时间
        response = self._add_duration_to_response(response, start_time)

        # 添加助手回复到历史
        self.chat_manager.add_message("assistant", response)

        # 更新Gradio界面
        history.append(
            {
                "role": "assistant",
                "content": response,
                "metadata": {"timestamp": time_str, "title": f"🤖 {time_str}"},
            }
        )
        yield history

    @staticmethod
    def _add_duration_to_response(response: str, start_time: datetime) -> str:
        """在回复内容底部添加响应时间"""
        from datetime import datetime as dt

        end_time = dt.now()
        duration = (end_time - start_time).total_seconds()
        duration_str = ResponseHandler._format_duration(duration)
        return f"{response}\n\n---\n⏱️ **响应时间:** {duration_str}"

    @staticmethod
    def _format_duration(duration_seconds: float) -> str:
        """格式化时间差"""
        if duration_seconds < 1:
            return f"{duration_seconds:.2f}s"
        elif duration_seconds < 60:
            return f"{duration_seconds:.1f}s"
        else:
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            return f"{minutes}m {seconds}s"


class DeepThinkHandler:
    """深度思考响应处理器"""

    def __init__(self, chat_manager: ChatManager):
        """
        初始化深度思考响应处理器

        Args:
            chat_manager: 聊天管理器实例
        """
        self.chat_manager = chat_manager

    def handle_deep_think_response(
            self,
            history: List[Dict[str, Any]],
            model: str,
            last_user_msg: str,
            start_time: datetime,
            enable_review: bool,
            show_process: bool,
            max_tasks: int,
            time_str: str,
            system_instruction: Optional[str] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            max_tokens: Optional[int] = None,
    ):
        """
        处理深度思考模式响应

        Args:
            history: 对话历史
            model: 模型名称
            last_user_msg: 最后一条用户消息
            start_time: 开始时间
            enable_review: 是否启用审查
            show_process: 是否显示过程
            max_tasks: 最大子任务数
            time_str: 时间字符串
            system_instruction: 系统提示词
            temperature: 温度参数
            top_p: Top P参数
            max_tokens: 最大Token数

        Yields:
            List[Dict]: 更新后的对话历史
        """
        try:
            orchestrator = DeepThinkOrchestrator(
                api_service=api_service,
                model=model,
                max_subtasks=int(max_tasks),
                enable_review=enable_review,
                verbose=True,
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens if max_tokens else None,
            )

            result = orchestrator.run(last_user_msg)

            # 格式化结果
            response = format_deep_think_result(result, include_process=show_process)

        except Exception as e:
            response = f"深度思考模式执行失败: {e!s}\n\n请尝试关闭深度思考模式或检查模型配置。"

        # 添加响应时间
        response = ResponseHandler._add_duration_to_response(response, start_time)

        # 添加助手回复到历史
        self.chat_manager.add_message("assistant", response)

        # 更新Gradio界面（非流式）
        history.append(
            {
                "role": "assistant",
                "content": response,
                "metadata": {"timestamp": time_str, "title": f"🤖 {time_str}"},
            }
        )
        yield history
