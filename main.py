"""
ThinkCloud for Web - 多提供商 LLM 客户端
支持深度思考模式的智能对话系统
"""

from datetime import datetime

import gradio as gr

from src.api_service import api_service
from src.chat_manager import ChatManager, MessageProcessor
from src.config import (
    CHATBOT_HEIGHT,
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_INSTRUCTION,
    MAX_INPUT_LINES,
    MODEL_PARAMETERS,
    SERVER_HOST,
    SERVER_PORT,
    check_api_key,
    get_server_port,
)
from src.deep_think import DeepThinkOrchestrator, format_deep_think_result


class LLMClient:
    """LLM客户端主类"""

    def __init__(self):
        self.chat_manager = ChatManager()
        self.message_processor = MessageProcessor()

    def create_interface(self):
        """创建Gradio界面"""
        with gr.Blocks(title="ThinkCloud for Web - AI 智能对话") as demo:
            # 标题和描述
            gr.Markdown(self._get_header_markdown())

            # 主要内容区域
            with gr.Row(equal_height=True):
                # 左侧控制面板
                with gr.Column(scale=1, min_width=280):
                    gr.Markdown("### 🎛️ 控制中心")

                    # 获取分组的模型数据
                    from src.config import PROVIDER_DISPLAY_NAMES, get_enabled_providers

                    enabled_providers = get_enabled_providers()
                    provider_choices = [
                        PROVIDER_DISPLAY_NAMES.get(p, p.capitalize()) for p in enabled_providers
                    ]

                    # 获取默认提供商和模型
                    from src.config import get_model_provider

                    default_provider_id = get_model_provider(DEFAULT_MODEL)
                    default_provider_name = (
                        PROVIDER_DISPLAY_NAMES.get(
                            default_provider_id, default_provider_id.capitalize()
                        )
                        if default_provider_id
                        else provider_choices[0]
                    )

                    # 第一级：选择提供商
                    provider_dropdown = gr.Dropdown(
                        choices=provider_choices,
                        value=default_provider_name,
                        label="🏢 选择提供商",
                        info="选择AI服务提供商",
                        interactive=True,
                    )

                    # 第二级：选择模型
                    from src.config import PROVIDER_MODELS

                    # 获取默认提供商的模型列表
                    default_models = (
                        PROVIDER_MODELS.get(default_provider_id, []) if default_provider_id else []
                    )

                    model_dropdown = gr.Dropdown(
                        choices=default_models,
                        value=DEFAULT_MODEL
                        if DEFAULT_MODEL in default_models
                        else (default_models[0] if default_models else ""),
                        label="🤖 选择模型",
                        info="选择具体的AI模型",
                        interactive=True,
                    )

                    # 系统状态显示（优化版）
                    gr.Markdown("### 📊 系统状态")
                    status_html = gr.HTML(value=self._get_status_html())

                    # 模型参数配置
                    gr.Markdown("### ⚙️ 模型参数")

                    # 流式传输控制
                    enable_streaming = gr.Checkbox(
                        label="🌊 启用流式传输", value=True, info="逐字显示回复内容（更流畅的体验）"
                    )

                    # System Instruction
                    system_instruction = gr.Textbox(
                        label="📝 系统提示词 (System Instruction)",
                        placeholder=DEFAULT_SYSTEM_INSTRUCTION,
                        value="",
                        lines=3,
                        max_lines=5,
                        info="为模型设置角色和行为规范（留空使用默认值）",
                    )

                    # Temperature 滑块
                    temperature = gr.Slider(
                        minimum=MODEL_PARAMETERS["temperature"]["min"],
                        maximum=MODEL_PARAMETERS["temperature"]["max"],
                        value=MODEL_PARAMETERS["temperature"]["default"],
                        step=MODEL_PARAMETERS["temperature"]["step"],
                        label="🌡️ Temperature（温度）",
                        info=MODEL_PARAMETERS["temperature"]["description"],
                    )

                    # 高级参数折叠区
                    with gr.Accordion("🔧 高级参数", open=False):
                        top_p = gr.Slider(
                            minimum=MODEL_PARAMETERS["top_p"]["min"],
                            maximum=MODEL_PARAMETERS["top_p"]["max"],
                            value=MODEL_PARAMETERS["top_p"]["default"],
                            step=MODEL_PARAMETERS["top_p"]["step"],
                            label="🎯 Top P（核采样）",
                            info=MODEL_PARAMETERS["top_p"]["description"],
                        )

                        max_tokens = gr.Slider(
                            minimum=MODEL_PARAMETERS["max_tokens"]["min"],
                            maximum=MODEL_PARAMETERS["max_tokens"]["max"],
                            value=MODEL_PARAMETERS["max_tokens"]["default"],
                            step=MODEL_PARAMETERS["max_tokens"]["step"],
                            label="📏 Max Tokens（最大长度）",
                            info=MODEL_PARAMETERS["max_tokens"]["description"],
                        )

                        frequency_penalty = gr.Slider(
                            minimum=MODEL_PARAMETERS["frequency_penalty"]["min"],
                            maximum=MODEL_PARAMETERS["frequency_penalty"]["max"],
                            value=MODEL_PARAMETERS["frequency_penalty"]["default"],
                            step=MODEL_PARAMETERS["frequency_penalty"]["step"],
                            label="🔁 Frequency Penalty（频率惩罚）",
                            info=MODEL_PARAMETERS["frequency_penalty"]["description"],
                        )

                        presence_penalty = gr.Slider(
                            minimum=MODEL_PARAMETERS["presence_penalty"]["min"],
                            maximum=MODEL_PARAMETERS["presence_penalty"]["max"],
                            value=MODEL_PARAMETERS["presence_penalty"]["default"],
                            step=MODEL_PARAMETERS["presence_penalty"]["step"],
                            label="✨ Presence Penalty（存在惩罚）",
                            info=MODEL_PARAMETERS["presence_penalty"]["description"],
                        )

                    # 深度思考模式配置
                    gr.Markdown("### 🧠 深度思考模式")
                    deep_think_enabled = gr.Checkbox(
                        label="启用深度思考", value=False, info="使用多阶段推理深入分析问题"
                    )

                    with gr.Accordion("高级选项", open=False):
                        enable_review = gr.Checkbox(
                            label="启用自我审查", value=True, info="对答案进行质量审查"
                        )
                        show_thinking_process = gr.Checkbox(
                            label="显示思考过程", value=True, info="展示详细的推理步骤"
                        )
                        max_subtasks = gr.Slider(
                            minimum=3,
                            maximum=8,
                            value=6,
                            step=1,
                            label="最大子任务数",
                            info="问题拆解的最大任务数量",
                        )

                    gr.Markdown("""
                    💡 **功能提示**

                    • 支持 Markdown 格式
                    • 支持代码高亮
                    • 支持多轮对话
                    • 可随时切换模型
                    • 🧠 深度思考模式可解决复杂问题
                    """)

                # 右侧聊天区域
                with gr.Column(scale=3, min_width=600):
                    # 聊天界面
                    chatbot = gr.Chatbot(
                        label="💬 对话界面",
                        height=CHATBOT_HEIGHT,
                        type="messages",
                        show_copy_button=True,
                    )

            # 输入区域（与上方对齐）
            with gr.Row():
                with gr.Column(scale=1, min_width=280):
                    pass  # 占位，与左侧控制面板对齐

                with gr.Column(scale=3, min_width=600), gr.Row():
                    msg = gr.Textbox(
                        label="✍️ 输入消息",
                        placeholder="💭 请输入您的问题...",
                        scale=5,
                        max_lines=MAX_INPUT_LINES,
                        show_copy_button=False,
                        container=False,
                    )
                    submit_btn = gr.Button(
                        "🚀 发送", variant="primary", scale=1, size="sm", min_width=80
                    )

            # 控制按钮区域（与上方对齐）
            with gr.Row():
                with gr.Column(scale=1, min_width=280):
                    pass  # 占位

                with gr.Column(scale=3, min_width=600), gr.Row():
                    clear_btn = gr.Button("🗑️ 清除对话", variant="secondary", size="sm", scale=1)
                    export_btn = gr.Button("📥 导出对话", variant="secondary", size="sm", scale=1)
                    gr.Markdown("*Powered by ThinkCloud*")

            # 绑定事件
            self._setup_event_handlers(
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
            )

        return demo

    def _get_header_markdown(self):
        """获取头部Markdown内容"""
        return """
        # 🚀 ThinkCloud for Web

        探索下一代 AI 对话体验 - 支持多提供商 + 深度思考模式

        ---

        **🤖 支持的提供商:** Cerebras • DeepSeek • OpenAI • DashScope

        **⚡ 模型系列:** Llama • Qwen • DeepSeek • GPT

        **✨ 特性:** 深度思考 • 智能参数调节 • 多轮对话
        """

    def _get_initial_status(self):
        """获取初始状态信息"""
        return api_service.get_provider_status()

    def _get_status_html(self):
        """生成HTML格式的系统状态显示"""
        from src.config import PROVIDER_DISPLAY_NAMES, get_enabled_providers

        enabled_providers = get_enabled_providers()
        history_count = self.chat_manager.get_history_length()

        # 构建提供商列表
        provider_list = []
        for provider in enabled_providers:
            provider_name = PROVIDER_DISPLAY_NAMES.get(provider, provider.capitalize())
            provider_list.append(f"✓ {provider_name}")

        providers_text = ", ".join(provider_list)

        # 构建状态HTML
        status_html = f"""
        <div>
            <p><strong>可用提供商：</strong>{providers_text}</p>
            <p><strong>对话轮数：</strong>{history_count}</p>
        </div>
        """

        return status_html

    def _setup_event_handlers(
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
    ):
        """设置事件处理器"""

        def update_models(provider_name):
            """当提供商变更时更新模型列表"""
            from src.config import PROVIDER_DISPLAY_NAMES, PROVIDER_MODELS

            # 从显示名称获取提供商ID
            provider_id = None
            for pid, display_name in PROVIDER_DISPLAY_NAMES.items():
                if display_name == provider_name:
                    provider_id = pid
                    break

            # 获取该提供商的模型列表
            models = PROVIDER_MODELS.get(provider_id, []) if provider_id else []

            # 返回更新后的下拉框配置
            return gr.update(choices=models, value=models[0] if models else "")

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
            last_user_msg = None
            for msg in reversed(history):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break

            if not last_user_msg:
                yield history
                return

            # 处理系统提示词（如果为空则使用默认值）
            actual_sys_inst = sys_inst.strip() if sys_inst and sys_inst.strip() else None

            # 获取当前时间
            start_time = datetime.now()
            time_str = start_time.strftime("%H:%M:%S")

            def format_duration(duration_seconds):
                """格式化时间差"""
                if duration_seconds < 1:
                    return f"{duration_seconds:.2f}s"
                elif duration_seconds < 60:
                    return f"{duration_seconds:.1f}s"
                else:
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    return f"{minutes}m {seconds}s"

            def add_duration_to_response(response, start_time):
                """在回复内容底部添加响应时间"""
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                duration_str = format_duration(duration)
                return f"{response}\n\n---\n⏱️ **响应时间:** {duration_str}"

            # 根据模式选择不同的处理方式
            if deep_think_mode:
                # 深度思考模式（暂不支持流式传输）
                try:
                    orchestrator = DeepThinkOrchestrator(
                        api_service=api_service,
                        model=model,
                        max_subtasks=int(max_tasks),
                        enable_review=review_enabled,
                        verbose=True,
                        system_instruction=actual_sys_inst,
                        temperature=temp,
                        top_p=top_p_val,
                        max_tokens=int(max_tok) if max_tok else None,
                    )

                    result = orchestrator.run(last_user_msg)

                    # 格式化结果
                    response = format_deep_think_result(result, include_process=show_process)

                except Exception as e:
                    response = (
                        f"深度思考模式执行失败: {e!s}\n\n请尝试关闭深度思考模式或检查模型配置。"
                    )

                # 添加响应时间
                response = add_duration_to_response(response, start_time)

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
                # 使用 yield 而不是 return，因为这是生成器函数
                yield history

            else:
                # 标准模式
                # 构建API消息 - 直接使用Gradio的history格式
                api_messages = []
                for msg in history:
                    if msg["role"] in ["user", "assistant"]:
                        api_messages.append({"role": msg["role"], "content": msg["content"]})

                if enable_stream:
                    # 流式传输模式
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
                            system_instruction=actual_sys_inst,
                            temperature=temp,
                            top_p=top_p_val,
                            max_tokens=int(max_tok) if max_tok else None,
                            frequency_penalty=freq_pen,
                            presence_penalty=pres_pen,
                            stream=True,
                        )

                        # 逐步更新回复
                        for chunk in stream_generator:
                            response_text += chunk
                            # 更新最后一条助手消息
                            history[-1]["content"] = response_text
                            yield history

                        # 流式传输完成，添加响应时间
                        response_text = add_duration_to_response(response_text, start_time)
                        history[-1]["content"] = response_text
                        yield history

                    except Exception as e:
                        error_msg = f"流式传输失败: {e!s}"
                        error_msg = add_duration_to_response(error_msg, start_time)
                        history[-1]["content"] = error_msg
                        response_text = error_msg
                        yield history

                    # 添加完整回复到聊天历史管理器
                    self.chat_manager.add_message("assistant", response_text)

                else:
                    # 非流式传输模式
                    try:
                        # 调用API
                        response = api_service.chat_completion(
                            messages=api_messages,
                            model=model,
                            system_instruction=actual_sys_inst,
                            temperature=temp,
                            top_p=top_p_val,
                            max_tokens=int(max_tok) if max_tok else None,
                            frequency_penalty=freq_pen,
                            presence_penalty=pres_pen,
                            stream=False,
                        )
                    except Exception as e:
                        response = f"API调用失败: {e!s}"

                    # 添加响应时间
                    response = add_duration_to_response(response, start_time)

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
                    # 使用 yield 而不是 return，因为这是生成器函数
                    yield history

        def clear_conversation():
            """清除对话"""
            self.chat_manager.clear_history()
            return [], self._get_status_html()

        def export_conversation():
            """导出对话"""
            if not self.chat_manager.history:
                return self._get_status_html()

            export_text = "多提供商 LLM 对话记录\n" + "=" * 50 + "\n"
            for msg in self.chat_manager.history:
                role = "用户" if msg["role"] == "user" else "助手"
                export_text += f"{role}: {msg['content']}\n\n"

            return export_text

        def update_status():
            """更新状态信息（HTML格式）"""
            return self._get_status_html()

        # 提供商变更事件 - 更新模型列表
        provider_dropdown.change(
            update_models, inputs=[provider_dropdown], outputs=[model_dropdown]
        )

        # 绑定事件
        msg.submit(user_message, [msg, chatbot, model_dropdown], [msg, chatbot], queue=False).then(
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
        ).then(update_status, None, [status_html])

        submit_btn.click(
            user_message, [msg, chatbot, model_dropdown], [msg, chatbot], queue=False
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
        ).then(update_status, None, [status_html])

        clear_btn.click(clear_conversation, None, [chatbot, status_html], queue=False)

        export_btn.click(export_conversation, None, [status_html], queue=False)

        # 页面加载时更新状态
        demo.load(update_status, None, status_html)


def main():
    """主函数"""
    print("[START] 启动 ThinkCloud for Web...")

    # 检查API配置
    if not check_api_key():
        print("\n[WARN] 请先配置至少一个API密钥环境变量")
        print("   创建.env文件并添加以下变量之一:")
        print("   - CEREBRAS_API_KEY=your_api_key_here")
        print("   - DEEPSEEK_API_KEY=your_api_key_here")
        print("   - OPENAI_API_KEY=your_api_key_here")
        print("   - DASHSCOPE_API_KEY=your_api_key_here")
        print("\n您仍然可以启动界面，但需要配置API密钥才能正常使用。")

    # 自动查找可用端口
    print("\n[PORT] 检查端口可用性...")
    available_port = get_server_port(SERVER_PORT, SERVER_HOST)

    # 创建并启动应用
    client = LLMClient()
    demo = client.create_interface()

    # 启动服务器
    print("\n[LAUNCH] 启动Web服务器...")
    print(f"   主机: {SERVER_HOST}")
    print(f"   端口: {available_port if available_port else '系统分配'}")
    print("   浏览器将自动打开")
    print("=" * 60)

    demo.launch(
        server_name=SERVER_HOST,
        server_port=available_port,
        share=False,
        inbrowser=True,
        show_error=True,
    )


if __name__ == "__main__":
    main()
