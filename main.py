"""
多提供商 LLM 客户端 - 主应用文件
重构版本，支持多个AI提供商和更好的模块化
"""

import gradio as gr

from src.api_service import api_service
from src.chat_manager import ChatManager, MessageProcessor
from src.config import (
    DEFAULT_MODEL, SERVER_HOST, SERVER_PORT,
    CHATBOT_HEIGHT, MAX_INPUT_LINES, check_api_key, get_server_port
)


class LLMClient:
    """LLM客户端主类"""

    def __init__(self):
        self.chat_manager = ChatManager()
        self.message_processor = MessageProcessor()

    def create_interface(self):
        """创建Gradio界面"""
        with gr.Blocks(title="多提供商 LLM 客户端") as demo:
            # 标题和描述
            gr.Markdown(self._get_header_markdown())

            # 主要内容区域
            with gr.Row(equal_height=True):
                # 左侧控制面板
                with gr.Column(scale=1, min_width=280):
                    gr.Markdown("### 🎛️ 控制中心")

                    # 获取分组的模型数据
                    from src.config import get_enabled_providers, PROVIDER_DISPLAY_NAMES

                    enabled_providers = get_enabled_providers()
                    provider_choices = [PROVIDER_DISPLAY_NAMES.get(p, p.capitalize()) for p in enabled_providers]

                    # 获取默认提供商和模型
                    from src.config import get_model_provider
                    default_provider_id = get_model_provider(DEFAULT_MODEL)
                    default_provider_name = PROVIDER_DISPLAY_NAMES.get(default_provider_id,
                                                                       default_provider_id.capitalize()) if default_provider_id else \
                    provider_choices[0]

                    # 第一级：选择提供商
                    provider_dropdown = gr.Dropdown(
                        choices=provider_choices,
                        value=default_provider_name,
                        label="🏢 选择提供商",
                        info="选择AI服务提供商",
                        interactive=True
                    )

                    # 第二级：选择模型
                    from src.config import PROVIDER_MODELS
                    # 获取默认提供商的模型列表
                    default_models = PROVIDER_MODELS.get(default_provider_id, []) if default_provider_id else []

                    model_dropdown = gr.Dropdown(
                        choices=default_models,
                        value=DEFAULT_MODEL if DEFAULT_MODEL in default_models else (
                            default_models[0] if default_models else ""),
                        label="🤖 选择模型",
                        info="选择具体的AI模型",
                        interactive=True
                    )

                    # 系统状态显示（优化版）
                    gr.Markdown("### 📊 系统状态")
                    status_html = gr.HTML(value=self._get_status_html())

                    gr.Markdown("""
                    💡 **功能提示**

                    • 支持 Markdown 格式
                    • 支持代码高亮
                    • 支持多轮对话
                    • 可随时切换模型
                    """)

                # 右侧聊天区域
                with gr.Column(scale=3, min_width=600):
                    # 聊天界面
                    chatbot = gr.Chatbot(
                        label="💬 对话界面",
                        height=CHATBOT_HEIGHT,
                        type="messages",
                        show_copy_button=True
                    )

            # 输入区域（与上方对齐）
            with gr.Row():
                with gr.Column(scale=1, min_width=280):
                    pass  # 占位，与左侧控制面板对齐

                with gr.Column(scale=3, min_width=600):
                    with gr.Row():
                        msg = gr.Textbox(
                            label="✍️ 输入消息",
                            placeholder="💭 请输入您的问题...",
                            scale=5,
                            max_lines=MAX_INPUT_LINES,
                            show_copy_button=False,
                            container=False
                        )
                        submit_btn = gr.Button(
                            "🚀 发送",
                            variant="primary",
                            scale=1,
                            size="sm",
                            min_width=80
                        )

            # 控制按钮区域（与上方对齐）
            with gr.Row():
                with gr.Column(scale=1, min_width=280):
                    pass  # 占位

                with gr.Column(scale=3, min_width=600):
                    with gr.Row():
                        clear_btn = gr.Button("🗑️ 清除对话", variant="secondary", size="sm", scale=1)
                        export_btn = gr.Button("📥 导出对话", variant="secondary", size="sm", scale=1)
                        gr.Markdown("*Powered by Multi-Provider LLM*")

            # 绑定事件
            self._setup_event_handlers(
                demo, msg, chatbot, provider_dropdown, model_dropdown,
                submit_btn, clear_btn, export_btn, status_html
            )

        return demo

    def _get_header_markdown(self):
        """获取头部Markdown内容"""
        return """
        # 🚀 多提供商 AI 聊天客户端

        探索下一代 AI 对话体验 - 支持多个领先的大语言模型提供商

        ---

        **🤖 支持的提供商:** Cerebras • DeepSeek • OpenAI • DashScope

        **⚡ 模型系列:** Llama • Qwen • DeepSeek • GPT

        **✨ 特性:** 快速响应 • 智能切换 • 历史记录
        """

    def _get_initial_status(self):
        """获取初始状态信息"""
        return api_service.get_provider_status()

    def _get_status_html(self):
        """生成HTML格式的系统状态显示"""
        from src.config import get_enabled_providers, PROVIDER_DISPLAY_NAMES

        enabled_providers = get_enabled_providers()
        history_count = self.chat_manager.get_history_length()

        # 构建提供商列表
        provider_list = []
        for provider in enabled_providers:
            provider_name = PROVIDER_DISPLAY_NAMES.get(provider, provider.capitalize())
            provider_list.append(f'✓ {provider_name}')

        providers_text = ', '.join(provider_list)

        # 构建状态HTML
        status_html = f'''
        <div>
            <p><strong>可用提供商：</strong>{providers_text}</p>
            <p><strong>对话轮数：</strong>{history_count}</p>
        </div>
        '''

        return status_html

    def _setup_event_handlers(
            self, demo, msg, chatbot, provider_dropdown, model_dropdown,
            submit_btn, clear_btn, export_btn, status_html
    ):
        """设置事件处理器"""

        def update_models(provider_name):
            """当提供商变更时更新模型列表"""
            from src.config import PROVIDER_MODELS, PROVIDER_DISPLAY_NAMES

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

            # 更新Gradio界面
            new_history = history + [{"role": "user", "content": user_msg}]
            return "", new_history

        def bot_message(history, model):
            """获取机器人回复"""
            if not history:
                return history

            # 构建API消息 - 直接使用Gradio的history格式
            api_messages = []
            for msg in history:
                if msg["role"] in ["user", "assistant"]:
                    api_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # 调用API
            response = api_service.chat_completion(api_messages, model)

            # 添加助手回复到历史
            self.chat_manager.add_message("assistant", response)

            # 更新Gradio界面
            history.append({"role": "assistant", "content": response})
            return history

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
            update_models,
            inputs=[provider_dropdown],
            outputs=[model_dropdown]
        )

        # 绑定事件
        msg.submit(
            user_message,
            [msg, chatbot, model_dropdown],
            [msg, chatbot],
            queue=False
        ).then(
            bot_message,
            [chatbot, model_dropdown],
            [chatbot]
        ).then(
            update_status,
            None,
            [status_html]
        )

        submit_btn.click(
            user_message,
            [msg, chatbot, model_dropdown],
            [msg, chatbot],
            queue=False
        ).then(
            bot_message,
            [chatbot, model_dropdown],
            [chatbot]
        ).then(
            update_status,
            None,
            [status_html]
        )

        clear_btn.click(
            clear_conversation,
            None,
            [chatbot, status_html],
            queue=False
        )

        export_btn.click(
            export_conversation,
            None,
            [status_html],
            queue=False
        )

        # 页面加载时更新状态
        demo.load(update_status, None, status_html)


def main():
    """主函数"""
    print("[START] 启动 多提供商 LLM 客户端...")

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
    print(f"\n[LAUNCH] 启动Web服务器...")
    print(f"   主机: {SERVER_HOST}")
    print(f"   端口: {available_port if available_port else '系统分配'}")
    print(f"   浏览器将自动打开")
    print("=" * 60)

    demo.launch(
        server_name=SERVER_HOST,
        server_port=available_port,
        share=False,
        inbrowser=True,
        show_error=True
    )


if __name__ == "__main__":
    main()
