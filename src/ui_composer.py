"""
UI布局构建器 - 纯UI创建，不涉及业务逻辑
遵循单一职责原则，只负责创建和布局Gradio界面组件
"""

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
            # 标题和描述
            gr.Markdown(header_markdown_fn())

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
                        PROVIDER_DISPLAY_NAMES.get(default_provider_id, default_provider_id.capitalize())
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
                        PROVIDER_MODELS.get(default_provider_id, [])
                        if default_provider_id
                        else []
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
                    status_html = gr.HTML(value=status_html_fn())

                    # 模型参数配置
                    gr.Markdown("### ⚙️ 模型参数")

                    # 流式传输控制
                    enable_streaming = gr.Checkbox(
                        label="🌊 启用流式传输", value=True, info="逐字显示回复内容（更流畅的体验）"
                    )

                    # System Instruction
                    system_instruction = gr.Textbox(
                        label="📝 系统提示词 (System Instruction)",
                        placeholder="你是一个乐于助人的AI助手...",
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
                        info="控制生成文本的随机性（值越小越确定）",
                    )

                    # 高级参数折叠区
                    with gr.Accordion("🔧 高级参数", open=False):
                        top_p = gr.Slider(
                            minimum=MODEL_PARAMETERS["top_p"]["min"],
                            maximum=MODEL_PARAMETERS["top_p"]["max"],
                            value=MODEL_PARAMETERS["top_p"]["default"],
                            step=MODEL_PARAMETERS["top_p"]["step"],
                            label="🎯 Top P（核采样）",
                            info="控制词汇选择范围（值越小候选词越少）",
                        )

                        max_tokens = gr.Slider(
                            minimum=MODEL_PARAMETERS["max_tokens"]["min"],
                            maximum=MODEL_PARAMETERS["max_tokens"]["max"],
                            value=MODEL_PARAMETERS["max_tokens"]["default"],
                            step=MODEL_PARAMETERS["max_tokens"]["step"],
                            label="📏 Max Tokens（最大长度）",
                            info="生成文本的最大Token数量",
                        )

                        frequency_penalty = gr.Slider(
                            minimum=MODEL_PARAMETERS["frequency_penalty"]["min"],
                            maximum=MODEL_PARAMETERS["frequency_penalty"]["max"],
                            value=MODEL_PARAMETERS["frequency_penalty"]["default"],
                            step=MODEL_PARAMETERS["frequency_penalty"]["step"],
                            label="🔁 Frequency Penalty（频率惩罚）",
                            info="惩罚重复词语（正值减少重复）",
                        )

                        presence_penalty = gr.Slider(
                            minimum=MODEL_PARAMETERS["presence_penalty"]["min"],
                            maximum=MODEL_PARAMETERS["presence_penalty"]["max"],
                            value=MODEL_PARAMETERS["presence_penalty"]["default"],
                            step=MODEL_PARAMETERS["presence_penalty"]["step"],
                            label="✨ Presence Penalty（存在惩罚）",
                            info="惩罚主题重复（正值增加多样性）",
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

                    gr.Markdown(
                        """
                    💡 **功能提示**

                    • 支持 Markdown 格式
                    • 支持代码高亮
                    • 支持多轮对话
                    • 可随时切换模型
                    • 🧠 深度思考模式可解决复杂问题
                    """
                    )

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
