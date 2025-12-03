"""
UI客户端 - 协调界面组件、事件处理器和响应处理器
主入口类，整合各个模块
"""

from src.api_service import api_service
from src.chat_manager import ChatManager
from src.event_handlers import EventHandlers
from src.response_handlers import DeepThinkHandler, ResponseHandler
from src.ui_composer import UIComposer


class UIClient:
    """UI客户端类 - 整合UI组件和事件处理"""

    def __init__(self):
        """初始化UI客户端"""
        self.chat_manager = ChatManager()
        self.response_handler = ResponseHandler(self.chat_manager)
        self.deep_think_handler = DeepThinkHandler(self.chat_manager)
        self.event_handlers = EventHandlers(
            self.chat_manager, self.response_handler, self.deep_think_handler
        )
        self.ui_composer = UIComposer()

    def create_interface(self):
        """创建Gradio界面"""
        return self.ui_composer.create_interface(
            header_markdown_fn=self._get_header_markdown,
            status_html_fn=self._get_status_html,
            event_handlers=self.event_handlers,
            update_models_fn=self._update_models,
            update_status_fn=self._get_status_html,
        )

    def _get_header_markdown(self):
        """获取头部Markdown内容"""
        return """
        # 🚀 ThinkCloud for Web

        探索下一代 AI 对话体验 - 支持多提供商 + 深度思考模式

        ---

        **🤖 支持的提供商:** Cerebras • DeepSeek • OpenAI • DashScope • Kimi

        **⚡ 模型系列:** Llama • Qwen • DeepSeek • GPT • Moonshot

        **✨ 特性:** 深度思考 • 智能参数调节 • 多轮对话
        """

    def _get_status_html(self):
        """获取状态HTML信息"""
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
        return f"""
        <div>
            <p><strong>可用提供商：</strong>{providers_text}</p>
            <p><strong>对话轮数：</strong>{history_count}</p>
        </div>
        """

    def _update_models(self, provider_name):
        """更新模型列表"""
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
