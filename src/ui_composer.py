"""
UI布局构建器 - 纯UI创建，不涉及业务逻辑
遵循单一职责原则,只负责创建和布局Gradio界面组件
"""

import os
import gradio as gr

from src.config import (
    CHATBOT_HEIGHT,
    DEFAULT_MODEL,
    MAX_INPUT_LINES,
    MODEL_PARAMETERS,
)


class UIComposer:
    """UI布局构建类"""

    def __init__(self):
        pass

    def create_interface(
        self,
        header_markdown_fn,
        status_html_fn,
        event_handlers,
        update_models_fn,
        update_status_fn,
    ):
        """
        创建Gradio界面

        Args:
            header_markdown_fn: 头部Markdown回调函数
            status_html_fn: 状态HTML生成回调函数
            event_handlers: 事件处理器实例
            update_models_fn: 更新模型列表函数
            update_status_fn: 更新状态信息函数

        Returns:
            gradio.Blocks: Gradio界面实例
        """
        with gr.Blocks(title="ThinkCloud for Web - AI 智能对话") as demo:
            # 添加自定义CSS样式(通过HTML)
            gr.HTML("""
            <style>
                /* 紧凑化样式 */
                .gradio-container { max-width: 100% !important; }
                .block { padding: 0.5rem !important; }
                h3 { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
                .form { gap: 0.5rem !important; }
                .accordion { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
                input[type="range"] { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
                input[type="checkbox"] { margin: 0.2rem !important; }
                .footer-text { text-align: center !important; font-size: 0.9rem !important; color: #666 !important; margin: 0 !important; }
                .gap { gap: 0.5rem !important; }
                .flex-col { gap: 0.5rem !important; }
            </style>
            """, visible=False)

            # 标题和描述
            gr.Markdown(header_markdown_fn())

            # 主要内容区域
            with gr.Row(equal_height=True):
                # 左侧控制面板
                with gr.Column(scale=1, min_width=220):
                    gr.Markdown("### ⚙️ 控制中心")

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

                    # 提供商和模型选择
                    provider_dropdown = gr.Dropdown(
                        choices=provider_choices,
                        value=default_provider_name,
                        label="🤖 提供商",
                        info=None,
                        interactive=True,
                    )

                    from src.config import PROVIDER_MODELS

                    default_models = (
                        PROVIDER_MODELS.get(default_provider_id, []) if default_provider_id else []
                    )

                    model_dropdown = gr.Dropdown(
                        choices=default_models,
                        value=DEFAULT_MODEL
                        if DEFAULT_MODEL in default_models
                        else (default_models[0] if default_models else ""),
                        label="🎯 模型",
                        info=None,
                        interactive=True,
                    )

                    # 系统状态
                    gr.Markdown("### 📊 状态")
                    status_html = gr.HTML(value=status_html_fn())

                    gr.Markdown("### 🎛️ 参数")

                    # 控制选项（水平排列）
                    with gr.Row():
                        enable_streaming = gr.Checkbox(
                            label="流式", value=True, scale=1
                        )
                        deep_think_enabled = gr.Checkbox(
                            label="深思", value=False, scale=1
                        )

                    # 系统提示词(折叠状态)
                    with gr.Accordion("💬 系统提示", open=False):
                        system_instruction = gr.Textbox(
                            label="",
                            placeholder="设置AI角色和行为(可选)",
                            value="",
                            lines=2,
                            container=False,
                        )

                    # 主要参数
                    temperature = gr.Slider(
                        minimum=MODEL_PARAMETERS["temperature"]["min"],
                        maximum=MODEL_PARAMETERS["temperature"]["max"],
                        value=MODEL_PARAMETERS["temperature"]["default"],
                        step=MODEL_PARAMETERS["temperature"]["step"],
                        label="🌡️ 温度",
                        info=None,
                    )

                    # 高级参数
                    with gr.Accordion("⚙️ 高级参数", open=False):
                        top_p = gr.Slider(
                            minimum=MODEL_PARAMETERS["top_p"]["min"],
                            maximum=MODEL_PARAMETERS["top_p"]["max"],
                            value=MODEL_PARAMETERS["top_p"]["default"],
                            step=MODEL_PARAMETERS["top_p"]["step"],
                            label="Top P",
                            info=None,
                        )

                        max_tokens = gr.Slider(
                            minimum=MODEL_PARAMETERS["max_tokens"]["min"],
                            maximum=MODEL_PARAMETERS["max_tokens"]["max"],
                            value=MODEL_PARAMETERS["max_tokens"]["default"],
                            step=MODEL_PARAMETERS["max_tokens"]["step"],
                            label="最大长度",
                            info=None,
                        )

                        frequency_penalty = gr.Slider(
                            minimum=MODEL_PARAMETERS["frequency_penalty"]["min"],
                            maximum=MODEL_PARAMETERS["frequency_penalty"]["max"],
                            value=MODEL_PARAMETERS["frequency_penalty"]["default"],
                            step=MODEL_PARAMETERS["frequency_penalty"]["step"],
                            label="频率惩罚",
                            info=None,
                        )

                        presence_penalty = gr.Slider(
                            minimum=MODEL_PARAMETERS["presence_penalty"]["min"],
                            maximum=MODEL_PARAMETERS["presence_penalty"]["max"],
                            value=MODEL_PARAMETERS["presence_penalty"]["default"],
                            step=MODEL_PARAMETERS["presence_penalty"]["step"],
                            label="存在惩罚",
                            info=None,
                        )

                    # 深度思考选项
                    with gr.Accordion("🧠 深度思考", open=False):
                        with gr.Row():
                            enable_review = gr.Checkbox(
                                label="审查", value=True, scale=1
                            )
                            enable_web_search = gr.Checkbox(
                                label="搜索", value=False, scale=1
                            )
                        show_thinking_process = gr.Checkbox(
                            label="显示推理过程", value=True
                        )
                        max_subtasks = gr.Slider(
                            minimum=3,
                            maximum=8,
                            value=6,
                            step=1,
                            label="子任务数",
                            info=None,
                        )

                    # 简化的功能提示
                    with gr.Accordion("💡 功能提示", open=False):
                        gr.Markdown(
                            """
                        • Markdown & 代码高亮
                        • 多轮对话 & 随时切换模型
                        • 🧠 深度思考模式
                        • 🌐 网络搜索(即将开放)
                        """
                        )

                # 右侧聊天区域
                with gr.Column(scale=3, min_width=600):
                    # 聊天界面
                    chatbot = gr.Chatbot(
                        label="💬 对话",
                        height=CHATBOT_HEIGHT,
                        latex_delimiters=[],
                        line_breaks=True,
                        render_markdown=True,
                        buttons=["copy_all"],
                    )

            # 输入区域
            with gr.Row():
                with gr.Column(scale=1, min_width=220):
                    pass

                with gr.Column(scale=3, min_width=600), gr.Row():
                    msg = gr.Textbox(
                        label="",
                        placeholder="💭 输入问题...",
                        scale=5,
                        max_lines=MAX_INPUT_LINES,
                        container=False,
                    )
                    submit_btn = gr.Button(
                        "📤 发送", variant="primary", scale=1, size="sm", min_width=60
                    )

            # 控制按钮区域
            with gr.Row():
                with gr.Column(scale=1, min_width=220):
                    pass

                with gr.Column(scale=3, min_width=600), gr.Row():
                    clear_btn = gr.Button("🗑️ 清除", variant="secondary", size="sm", scale=1)
                    export_btn = gr.Button("💾 导出", variant="secondary", size="sm", scale=1)
                    gr.Markdown("**ThinkCloud**", elem_classes="footer-text")

            # 绑定事件（通过事件处理器）
            event_handlers.setup_all_events(
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
                enable_web_search,
                show_thinking_process,
                max_subtasks,
                update_models_fn,
                update_status_fn,
            )

            # 页面加载时更新状态
            demo.load(update_status_fn, None, status_html)

        return demo

    def _create_input_section(self):
        """创建输入区域组件"""
        pass
