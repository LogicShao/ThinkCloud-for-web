"""
事件处理器 - 处理所有Gradio事件绑定和响应逻辑
与UI布局分离，专注于业务逻辑
"""

from datetime import datetime
from typing import List, Dict, Any, Callable, Optional

from src.chat_manager import ChatManager
from src.response_handlers import ResponseHandler, DeepThinkHandler


class EventHandlers:
    """事件处理器类 - 处理所有Gradio事件"""

    def __init__(
            self,
            chat_manager: ChatManager,
            response_handler: ResponseHandler,
            deep_think_handler: DeepThinkHandler,
    ):
        """
        初始化事件处理器

        Args:
            chat_manager: 聊天管理器实例
            response_handler: 标准响应处理器
            deep_think_handler: 深度思考响应处理器
        """
        self.chat_manager = chat_manager
        self.response_handler = response_handler
        self.deep_think_handler = deep_think_handler

    def setup_all_events(
            self,
            demo,
            msg,
            chatbot,
            provider_dropdown,
            model_dropdown,
            submit_btn,
            clear_btn,
            export_btn,
            status_html,
            enable_streaming,
            system_instruction,
            temperature,
            top_p,
            max_tokens,
            frequency_penalty,
            presence_penalty,
            deep_think_enabled,
            enable_review,
            show_thinking_process,
            max_subtasks,
            update_models_fn: Callable,
            update_status_fn: Callable,
    ):
        """
        绑定所有事件处理器

        Args:
            demo: Gradio Blocks实例
            msg: 消息输入框
            chatbot: 聊天界面
            provider_dropdown: 提供商下拉框
            model_dropdown: 模型下拉框
            submit_btn: 提交按钮
            clear_btn: 清除按钮
            export_btn: 导出按钮
            status_html: 状态显示
            enable_streaming: 流式传输复选框
            system_instruction: 系统提示词输入框
            temperature: 温度滑块
            top_p: Top P滑块
            max_tokens: 最大Token滑块
            frequency_penalty: 频率惩罚滑块
            presence_penalty: 存在惩罚滑块
            deep_think_enabled: 深度思考复选框
            enable_review: 审查复选框
            show_thinking_process: 显示过程复选框
            max_subtasks: 最大子任务数滑块
            update_models_fn: 更新模型列表函数
            update_status_fn: 更新状态信息函数
        """

        def user_message(user_msg, history, model):
            """处理用户消息"""
            if not user_msg.strip():
                return "", history

            # 添加用户消息到历史
            self.chat_manager.add_message("user", user_msg)

            # 获取当前时间
            current_time = datetime.now().strftime("%H:%M:%S")

            # 更新Gradio界面，在消息中添加时间戳
            new_history = [
                *history,
                {
                    "role": "user",
                    "content": user_msg,
                    "metadata": {"timestamp": current_time, "title": f"🕐 {current_time}"},
                },
            ]
            return "", new_history

        def bot_message(
                history,
                model,
                enable_stream,
                sys_inst,
                temp,
                top_p_val,
                max_tok,
                freq_pen,
                pres_pen,
                deep_think_mode,
                review_enabled,
                show_process,
                max_tasks,
        ):
            """获取机器人回复"""
            if not history:
                yield history
                return

            # 获取最后一条用户消息
            last_user_msg = self._extract_last_user_message(history)

            if not last_user_msg:
                yield history
                return

            # 处理系统提示词（如果为空则使用默认值）
            actual_sys_inst = sys_inst.strip() if sys_inst and sys_inst.strip() else None

            # 获取开始时间
            start_time = datetime.now()
            time_str = start_time.strftime("%H:%M:%S")

            # 根据模式选择不同的处理方式
            if deep_think_mode:
                # 深度思考模式
                yield from self.deep_think_handler.handle_deep_think_response(
                    history=history,
                    model=model,
                    last_user_msg=last_user_msg,
                    start_time=start_time,
                    enable_review=review_enabled,
                    show_process=show_process,
                    max_tasks=max_tasks,
                    time_str=time_str,
                    system_instruction=actual_sys_inst,
                    temperature=temp,
                    top_p=top_p_val,
                    max_tokens=max_tok,
                )
            else:
                # 标准模式
                yield from self.response_handler.handle_standard_response(
                    history=history,
                    model=model,
                    enable_stream=enable_stream,
                    start_time=start_time,
                    system_instruction=actual_sys_inst,
                    temperature=temp,
                    top_p=top_p_val,
                    max_tokens=max_tok,
                    frequency_penalty=freq_pen,
                    presence_penalty=pres_pen,
                )

        def clear_conversation():
            """清除对话"""
            self.chat_manager.clear_history()
            return [], update_status_fn()

        def export_conversation():
            """导出对话"""
            if not self.chat_manager.history:
                return update_status_fn()

            export_text = "多提供商 LLM 对话记录\n" + "=" * 50 + "\n"
            for msg in self.chat_manager.history:
                role = "用户" if msg["role"] == "user" else "助手"
                export_text += f"{role}: {msg['content']}\n\n"

            return export_text

        # 提供商变更事件 - 更新模型列表
        provider_dropdown.change(update_models_fn, inputs=[provider_dropdown], outputs=[model_dropdown])

        # 消息提交事件
        msg.submit(
            user_message,
            [msg, chatbot, model_dropdown],
            [msg, chatbot],
            queue=False,
        ).then(
            bot_message,
            [
                chatbot,
                model_dropdown,
                enable_streaming,
                system_instruction,
                temperature,
                top_p,
                max_tokens,
                frequency_penalty,
                presence_penalty,
                deep_think_enabled,
                enable_review,
                show_thinking_process,
                max_subtasks,
            ],
            [chatbot],
        ).then(update_status_fn, None, [status_html])

        # 提交按钮点击事件
        submit_btn.click(
            user_message,
            [msg, chatbot, model_dropdown],
            [msg, chatbot],
            queue=False,
        ).then(
            bot_message,
            [
                chatbot,
                model_dropdown,
                enable_streaming,
                system_instruction,
                temperature,
                top_p,
                max_tokens,
                frequency_penalty,
                presence_penalty,
                deep_think_enabled,
                enable_review,
                show_thinking_process,
                max_subtasks,
            ],
            [chatbot],
        ).then(update_status_fn, None, [status_html])

        # 清除对话事件
        clear_btn.click(clear_conversation, None, [chatbot, status_html], queue=False)

        # 导出对话事件
        export_btn.click(export_conversation, None, [status_html], queue=False)

    @staticmethod
    def _extract_last_user_message(history: List[Dict[str, Any]]) -> Optional[str]:
        """从对话历史中提取最后一条用户消息"""
        for msg in reversed(history):
            if msg["role"] == "user":
                return msg["content"]
        return None
