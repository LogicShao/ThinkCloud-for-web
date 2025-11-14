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
        # 创建深色主题
        custom_theme = gr.themes.Base(
            primary_hue=gr.themes.colors.cyan,
            secondary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.slate,
        ).set(
            # 深色背景渐变
            body_background_fill="linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)",
            body_background_fill_dark="linear-gradient(135deg, #0a0e1a 0%, #1a1438 100%)",
            # 主按钮样式
            button_primary_background_fill="linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)",
            button_primary_background_fill_hover="linear-gradient(135deg, #0891b2 0%, #2563eb 100%)",
            button_primary_text_color="white",
            # 阴影效果
            shadow_drop="0 10px 30px rgba(0, 0, 0, 0.5)",
            shadow_drop_lg="0 20px 50px rgba(0, 0, 0, 0.7)",
            # 文字颜色
            body_text_color="*neutral_100",
            body_text_color_subdued="*neutral_400",
        )

        with gr.Blocks(
                title="多提供商 LLM 客户端",
                theme=custom_theme,
                css=self._get_custom_css()
        ) as demo:
            # 标题和描述
            gr.Markdown(self._get_header_markdown())

            # 主要内容区域
            with gr.Row(equal_height=True, elem_classes="main-row"):
                # 左侧控制面板
                with gr.Column(scale=1, min_width=280, elem_classes="control-panel"):
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
                        elem_classes="provider-selector",
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
                        elem_classes="model-selector",
                        interactive=True
                    )

                    # 系统状态显示（优化版）
                    gr.Markdown("### 📊 系统状态")
                    status_html = gr.HTML(
                        value=self._get_status_html(),
                        elem_classes="status-display"
                    )

                    gr.Markdown("""
                    <div class="info-box">
                        💡 <strong style="color: #06b6d4;">功能提示</strong><br/>
                        • 支持 Markdown 格式<br/>
                        • 支持代码高亮<br/>
                        • 支持多轮对话<br/>
                        • 可随时切换模型
                    </div>
                    """)

                # 右侧聊天区域
                with gr.Column(scale=3, min_width=600, elem_classes="chat-area"):
                    # 聊天界面
                    chatbot = gr.Chatbot(
                        label="💬 对话界面",
                        height=CHATBOT_HEIGHT,
                        type="messages",
                        show_copy_button=True,
                        avatar_images=(
                            "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
                            "https://cdn-icons-png.flaticon.com/512/4712/4712035.png"
                        ),
                        elem_classes="chat-box"
                    )

            # 输入区域（与上方对齐）
            with gr.Row(elem_classes="input-row"):
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
                            elem_classes="message-input",
                            container=False
                        )
                        submit_btn = gr.Button(
                            "🚀 发送",
                            variant="primary",
                            scale=1,
                            size="sm",
                            min_width=80,
                            elem_classes="send-button"
                        )

            # 控制按钮区域（与上方对齐）
            with gr.Row(elem_classes="control-row"):
                with gr.Column(scale=1, min_width=280):
                    pass  # 占位

                with gr.Column(scale=3, min_width=600):
                    with gr.Row():
                        clear_btn = gr.Button("🗑️ 清除对话", variant="secondary", size="sm", scale=1)
                        export_btn = gr.Button("📥 导出对话", variant="secondary", size="sm", scale=1)
                        gr.HTML(
                            "<div style='flex-grow: 1; text-align: right; color: #94a3b8; font-size: 0.85rem; padding: 0.5rem; line-height: 2rem;'>Powered by Multi-Provider LLM</div>"
                        )

            # 绑定事件
            self._setup_event_handlers(
                demo, msg, chatbot, provider_dropdown, model_dropdown,
                submit_btn, clear_btn, export_btn, status_html
            )

        return demo

    def _get_custom_css(self):
        """获取自定义CSS样式 - 深色主题"""
        return """
        /* 全局容器样式 */
        .gradio-container {
            width: 100% !important;
            max-width: none !important;
            margin: 0 auto;
            background: transparent !important;
        }

        .main {
            padding: 2rem;
            background: transparent;
        }

        /* 深色玻璃态卡片效果 */
        .control-panel, .chat-area {
            background: rgba(15, 23, 42, 0.85) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border-radius: 20px !important;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
                        0 0 1px rgba(6, 182, 212, 0.3) inset !important;
            border: 1px solid rgba(6, 182, 212, 0.2) !important;
            padding: 1.5rem !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative !important;
            z-index: 1 !important;
        }

        .control-panel:hover, .chat-area:hover {
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.6),
                        0 0 1px rgba(6, 182, 212, 0.5) inset !important;
            transform: translateY(-2px);
            border-color: rgba(6, 182, 212, 0.4) !important;
        }

        /* 控制面板有下拉菜单时，确保不遮挡 */
        .control-panel {
            overflow: visible !important;
        }

        /* 深色标题样式 */
        .gradio-markdown h1 {
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
            font-size: 2.5rem;
            margin-bottom: 1rem;
            letter-spacing: -0.025em;
            text-shadow: 0 2px 10px rgba(6, 182, 212, 0.3);
        }

        .gradio-markdown {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(20px);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(6, 182, 212, 0.2);
            margin-bottom: 2rem;
            color: #e2e8f0 !important;
        }

        .gradio-markdown h3 {
            color: #06b6d4 !important;
        }

        .gradio-markdown p, .gradio-markdown strong, .gradio-markdown div {
            color: #cbd5e1 !important;
        }

        /* 深色按钮样式 */
        .btn {
            border-radius: 12px !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
            border: none !important;
        }

        .btn-primary {
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%) !important;
            color: white !important;
        }

        .btn:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 25px rgba(6, 182, 212, 0.4) !important;
        }

        .btn:active {
            transform: translateY(0) scale(0.98) !important;
        }

        /* 深色输入框样式 */
        .input-text, textarea, input {
            border-radius: 12px !important;
            border: 2px solid rgba(6, 182, 212, 0.3) !important;
            transition: all 0.3s ease !important;
            background: rgba(30, 41, 59, 0.8) !important;
            color: #e2e8f0 !important;
            position: relative !important;
            z-index: 10 !important;
        }

        .input-text:focus, textarea:focus, input:focus {
            border-color: #06b6d4 !important;
            box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.2) !important;
            transform: translateY(-1px);
            background: rgba(30, 41, 59, 0.95) !important;
            z-index: 50 !important;
        }

        /* 深色下拉菜单样式 */
        .dropdown {
            border-radius: 12px !important;
            border: 2px solid rgba(6, 182, 212, 0.3) !important;
            background: rgba(30, 41, 59, 0.8) !important;
            color: #e2e8f0 !important;
            position: relative !important;
            z-index: 100 !important;
        }

        /* 模型选择器特殊样式 */
        .model-selector {
            font-family: "Fira Code", "Consolas", monospace !important;
            font-size: 0.9rem !important;
            position: relative !important;
            z-index: 1000 !important;
        }

        .model-selector select,
        .model-selector input {
            background: rgba(30, 41, 59, 0.9) !important;
            border: 2px solid rgba(6, 182, 212, 0.4) !important;
            color: #e2e8f0 !important;
            padding: 0.75rem !important;
            line-height: 1.5 !important;
            position: relative !important;
            z-index: 1001 !important;
        }

        .model-selector select:hover,
        .model-selector input:hover {
            border-color: #06b6d4 !important;
            background: rgba(30, 41, 59, 1) !important;
            box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.15) !important;
        }

        .model-selector select:focus,
        .model-selector input:focus {
            border-color: #06b6d4 !important;
            box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.3) !important;
            outline: none !important;
            z-index: 1002 !important;
        }

        /* 下拉选项容器样式 - 确保显示在最上层 */
        .model-selector .dropdown-content,
        .model-selector .svelte-1gfkn6j,
        .model-selector [role="listbox"],
        .model-selector ul {
            position: absolute !important;
            z-index: 9999 !important;
            background: rgba(15, 23, 42, 0.98) !important;
            border: 2px solid rgba(6, 182, 212, 0.4) !important;
            border-radius: 12px !important;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6) !important;
            max-height: 400px !important;
            overflow-y: auto !important;
        }

        /* 下拉选项样式 */
        .model-selector option {
            background: rgba(15, 23, 42, 0.98) !important;
            color: #e2e8f0 !important;
            padding: 0.5rem !important;
            border-bottom: 1px solid rgba(6, 182, 212, 0.1) !important;
        }

        .model-selector option:hover {
            background: rgba(6, 182, 212, 0.2) !important;
            color: #06b6d4 !important;
        }

        /* 选中的选项高亮 */
        .model-selector option:checked,
        .model-selector option:selected {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.3) 0%, rgba(59, 130, 246, 0.3) 100%) !important;
            color: #06b6d4 !important;
            font-weight: 600 !important;
        }

        /* 深色聊天机器人样式 */
        .chatbot {
            border-radius: 16px !important;
            border: none !important;
            background: rgba(15, 23, 42, 0.6) !important;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4) inset !important;
        }

        .message {
            border-radius: 12px !important;
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
            animation: messageSlideIn 0.3s ease-out;
        }

        @keyframes messageSlideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* 用户消息样式 - 青蓝渐变 */
        .message.user {
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%) !important;
            color: white !important;
        }

        /* AI消息样式 - 深色卡片 */
        .message.bot {
            background: rgba(30, 41, 59, 0.95) !important;
            border: 1px solid rgba(6, 182, 212, 0.3) !important;
            color: #e2e8f0 !important;
        }

        /* 深色状态面板样式 */
        .status-panel {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%) !important;
            border-radius: 12px !important;
            border: 2px solid rgba(6, 182, 212, 0.3) !important;
            font-family: "Fira Code", monospace !important;
            font-size: 0.85rem !important;
            color: #cbd5e1 !important;
        }

        /* Label 样式 */
        label {
            color: #94a3b8 !important;
        }

        /* 布局样式 */
        .control-panel {
            min-width: 280px;
            max-width: 320px;
        }

        .chat-area {
            min-width: 600px;
            flex-grow: 1;
        }

        /* 深色滚动条美化 */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.5);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #0891b2 0%, #2563eb 100%);
        }

        /* 响应式设计 */
        @media (max-width: 1024px) {
            .control-panel {
                min-width: 220px;
                max-width: 260px;
            }
            .chat-area {
                min-width: 450px;
            }
            .gradio-markdown h1 {
                font-size: 2rem;
            }
        }

        @media (max-width: 768px) {
            .control-panel, .chat-area {
                min-width: unset;
                max-width: unset;
                width: 100%;
                margin-bottom: 1rem;
            }
            .main {
                padding: 1rem;
            }
            .gradio-markdown h1 {
                font-size: 1.75rem;
            }
        }

        /* 加载动画 */
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }

        .loading {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        /* 深色提示框 */
        .info-box {
            background: rgba(6, 182, 212, 0.1) !important;
            border: 1px solid rgba(6, 182, 212, 0.3) !important;
            color: #cbd5e1 !important;
        }

        /* 提供商选择器样式 */
        .provider-selector {
            font-family: "Fira Code", "Consolas", monospace !important;
            font-size: 0.95rem !important;
            position: relative !important;
            z-index: 500 !important;
        }

        .provider-selector select,
        .provider-selector input {
            background: rgba(30, 41, 59, 0.9) !important;
            border: 2px solid rgba(6, 182, 212, 0.35) !important;
            color: #e2e8f0 !important;
            padding: 0.75rem !important;
            line-height: 1.5 !important;
            font-weight: 600 !important;
        }

        .provider-selector select:hover,
        .provider-selector input:hover {
            border-color: #06b6d4 !important;
            background: rgba(30, 41, 59, 1) !important;
            box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.15) !important;
        }

        /* 状态显示区域 */
        .status-display {
            margin-top: 1rem !important;
        }

        /* 发送按钮样式 */
        .send-button {
            min-width: 80px !important;
            height: 40px !important;
            font-size: 0.9rem !important;
        }

        /* 布局行样式 */
        .main-row {
            margin-bottom: 1rem !important;
        }

        .input-row {
            margin-bottom: 0.5rem !important;
        }

        .control-row {
            margin-top: 0.5rem !important;
        }
        """

    def _get_header_markdown(self):
        """获取头部Markdown内容"""
        return """
        # 🚀 多提供商 AI 聊天客户端

        <div style="font-size: 1.1rem; color: #64748b; margin-top: 1rem;">
            探索下一代 AI 对话体验 - 支持多个领先的大语言模型提供商
        </div>

        ---

        <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1.5rem;">
            <div style="flex: 1; min-width: 200px;">
                <strong>🤖 支持的提供商</strong><br/>
                Cerebras • DeepSeek • OpenAI • DashScope
            </div>
            <div style="flex: 1; min-width: 200px;">
                <strong>⚡ 模型系列</strong><br/>
                Llama • Qwen • DeepSeek • GPT
            </div>
            <div style="flex: 1; min-width: 200px;">
                <strong>✨ 特性</strong><br/>
                快速响应 • 智能切换 • 历史记录
            </div>
        </div>
        """

    def _get_initial_status(self):
        """获取初始状态信息"""
        return api_service.get_provider_status()

    def _get_status_html(self):
        """生成HTML格式的系统状态显示"""
        from src.config import get_enabled_providers, PROVIDER_DISPLAY_NAMES

        enabled_providers = get_enabled_providers()
        history_count = self.chat_manager.get_history_length()

        # 构建提供商状态HTML
        provider_badges = []
        for provider in enabled_providers:
            provider_name = PROVIDER_DISPLAY_NAMES.get(provider, provider.capitalize())
            provider_badges.append(
                f'<span style="display: inline-block; margin: 0.25rem; padding: 0.5rem 0.75rem; '
                f'background: linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%); '
                f'border: 1px solid rgba(6, 182, 212, 0.4); border-radius: 8px; '
                f'color: #06b6d4; font-weight: 600; font-size: 0.85rem;">'
                f'✓ {provider_name}</span>'
            )

        providers_html = ''.join(provider_badges)

        # 构建对话统计HTML
        status_html = f'''
        <div style="padding: 1rem; background: rgba(30, 41, 59, 0.6); border-radius: 12px;
                    border: 1px solid rgba(6, 182, 212, 0.3);">
            <div style="margin-bottom: 0.75rem;">
                <span style="color: #94a3b8; font-size: 0.85rem; font-weight: 600;">可用提供商：</span>
                <div style="margin-top: 0.5rem;">{providers_html}</div>
            </div>
            <div style="border-top: 1px solid rgba(6, 182, 212, 0.2); padding-top: 0.75rem;">
                <span style="color: #94a3b8; font-size: 0.85rem;">对话轮数：</span>
                <span style="color: #06b6d4; font-weight: 700; font-size: 1.1rem; margin-left: 0.5rem;">{history_count}</span>
            </div>
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

            # 返回更新后的模型选择器
            return gr.Dropdown(choices=models, value=models[0] if models else "", interactive=True)

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
        print("\n⚠️  请先配置至少一个API密钥环境变量")
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
