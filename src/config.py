"""
配置模块 - 管理应用配置、提供商和模型列表
"""

import os
import socket

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 提供商配置
PROVIDER_CONFIG = {
    "cerebras": {
        "api_key": os.environ.get("CEREBRAS_API_KEY"),
        "base_url": "https://api.cerebras.ai",
        "enabled": True
    },
    "deepseek": {
        "api_key": os.environ.get("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com",
        "enabled": True
    },
    "openai": {
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "base_url": "https://api.openai.com/v1",
        "enabled": True
    },
    "dashscope": {
        "api_key": os.environ.get("DASHSCOPE_API_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "enabled": True
    }
}

# 提供商支持的模型映射
PROVIDER_MODELS = {
    "cerebras": [
        # Llama系列
        "llama-3.3-70b",
        "llama-3.1-8b",
        "llama-3.1-70b",
        "llama-3.2-3b",
        "llama-3.2-1b",

        # 其他模型
        "qwen-3-235b-a22b-instruct-2507",
        "qwen-3-235b-a22b-thinking-2507",
        "zai-glm-4.6",
        "gpt-oss-120b",
        "qwen-3-32b"
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-reasoner"
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ],
    "dashscope": [
        "qwen-max",
        "qwen-plus",
        "qwen-turbo",
        "qwen-long",
        "qwen-vl-max",
        "qwen-vl-plus",
        "qwen-audio-turbo",
        "qwen2-7b-instruct",
        "qwen2-72b-instruct",
        "qwen2-1.5b-instruct",
        "qwen2-57b-a14b-instruct"
    ]
}

# 默认提供商和模型
DEFAULT_PROVIDER = "cerebras"
DEFAULT_MODEL = "qwen-3-235b-a22b-thinking-2507"

# 服务器配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 7860

# 界面配置
CHATBOT_HEIGHT = 500
MAX_INPUT_LINES = 5

# 提供商显示名称映射
PROVIDER_DISPLAY_NAMES = {
    "cerebras": "Cerebras",
    "deepseek": "DeepSeek",
    "openai": "OpenAI",
    "dashscope": "DashScope"
}


# 获取所有支持的模型
def get_supported_models():
    """获取所有启用的提供商支持的模型列表"""
    all_models = []
    for provider, config in PROVIDER_CONFIG.items():
        if config["enabled"] and config["api_key"]:
            all_models.extend(PROVIDER_MODELS.get(provider, []))
    return all_models


# 获取带提供商信息的模型列表
def get_models_with_provider():
    """
    获取带提供商信息的模型列表，格式：[(display_name, model_id), ...]

    Returns:
        list: [(显示名称, 模型ID), ...] 例如：[("🔹 Cerebras | llama-3.3-70b", "llama-3.3-70b")]
    """
    models_with_provider = []

    # 按提供商分组
    for provider, config in PROVIDER_CONFIG.items():
        if config["enabled"] and config["api_key"]:
            provider_name = PROVIDER_DISPLAY_NAMES.get(provider, provider.capitalize())
            models = PROVIDER_MODELS.get(provider, [])

            for model in models:
                # 格式：🔹 提供商 | 模型名称
                display_name = f"🔹 {provider_name} | {model}"
                models_with_provider.append((display_name, model))

    return models_with_provider


# 获取分组的模型字典
def get_models_grouped_by_provider():
    """
    获取按提供商分组的模型字典

    Returns:
        dict: {提供商显示名称: [模型列表]}
    """
    grouped_models = {}

    for provider, config in PROVIDER_CONFIG.items():
        if config["enabled"] and config["api_key"]:
            provider_name = PROVIDER_DISPLAY_NAMES.get(provider, provider.capitalize())
            models = PROVIDER_MODELS.get(provider, [])
            grouped_models[f"📂 {provider_name}"] = models

    return grouped_models


# 从显示名称提取模型ID
def extract_model_id(display_name):
    """
    从显示名称中提取实际的模型ID

    Args:
        display_name: 显示名称，例如 "🔹 Cerebras | llama-3.3-70b"

    Returns:
        str: 模型ID，例如 "llama-3.3-70b"
    """
    if " | " in display_name:
        return display_name.split(" | ")[-1]
    return display_name


# 获取模型的显示名称
def get_model_display_name(model_id):
    """
    获取模型的显示名称（带提供商信息）

    Args:
        model_id: 模型ID

    Returns:
        str: 显示名称，例如 "🔹 Cerebras | llama-3.3-70b"
    """
    provider = get_model_provider(model_id)
    if provider:
        provider_name = PROVIDER_DISPLAY_NAMES.get(provider, provider.capitalize())
        return f"🔹 {provider_name} | {model_id}"
    return model_id


# 获取启用的提供商列表
def get_enabled_providers():
    """获取已配置且启用的提供商列表"""
    enabled_providers = []
    for provider, config in PROVIDER_CONFIG.items():
        if config["enabled"] and config["api_key"]:
            enabled_providers.append(provider)
    return enabled_providers


# 检查API密钥配置
def check_api_key(provider=None):
    """
    检查API密钥是否配置

    Args:
        provider: 指定提供商，None表示检查所有提供商

    Returns:
        bool: 是否至少有一个提供商配置了API密钥
    """
    if provider:
        config = PROVIDER_CONFIG.get(provider, {})
        if not config.get("api_key"):
            print(f"警告: {provider.upper()}_API_KEY 环境变量未设置")
            print(f"请创建.env文件并添加: {provider.upper()}_API_KEY=your_api_key_here")
            return False
        return True

    # 检查所有提供商
    has_valid_provider = False
    for provider, config in PROVIDER_CONFIG.items():
        if config["enabled"] and config["api_key"]:
            has_valid_provider = True
            break

    if not has_valid_provider:
        print("警告: 没有配置任何有效的API密钥")
        print("请至少配置以下环境变量之一:")
        for provider in PROVIDER_CONFIG:
            print(f"  - {provider.upper()}_API_KEY")
        return False

    return True


# 获取提供商配置
def get_provider_config(provider):
    """获取指定提供商的配置"""
    return PROVIDER_CONFIG.get(provider, {})


# 获取模型对应的提供商
def get_model_provider(model):
    """根据模型名称获取对应的提供商"""
    for provider, models in PROVIDER_MODELS.items():
        if model in models:
            return provider
    return None


# 端口管理工具函数
def is_port_available(port, host="0.0.0.0"):
    """
    检查指定端口是否可用

    Args:
        port: 要检查的端口号
        host: 主机地址，默认为 0.0.0.0

    Returns:
        bool: 端口可用返回True，否则返回False
    """
    try:
        # 创建socket对象
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # 尝试绑定端口（不设置SO_REUSEADDR，确保检测准确）
            sock.bind((host, port))
            return True
    except OSError:
        # 端口被占用或其他错误
        return False


def find_available_port(start_port=7860, max_attempts=100, host="0.0.0.0"):
    """
    自动查找可用端口

    从起始端口开始，依次尝试找到第一个可用的端口

    Args:
        start_port: 起始端口号，默认为7860
        max_attempts: 最大尝试次数，默认为100
        host: 主机地址，默认为 0.0.0.0

    Returns:
        int: 找到的可用端口号，如果没有找到返回None
    """
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port, host):
            return port

    print(f"[WARN] 警告: 在 {start_port}-{start_port + max_attempts - 1} 范围内未找到可用端口")
    return None


def get_server_port(preferred_port=SERVER_PORT, host=SERVER_HOST):
    """
    获取服务器端口，优先使用首选端口，如果被占用则自动查找可用端口

    Args:
        preferred_port: 首选端口号，默认为配置中的SERVER_PORT
        host: 主机地址，默认为配置中的SERVER_HOST

    Returns:
        int: 可用的端口号
    """
    # 首先检查首选端口
    if is_port_available(preferred_port, host):
        print(f"[OK] 使用端口: {preferred_port}")
        return preferred_port

    # 首选端口被占用，查找可用端口
    print(f"[WARN] 端口 {preferred_port} 已被占用，正在查找可用端口...")
    available_port = find_available_port(preferred_port + 1, max_attempts=100, host=host)

    if available_port:
        print(f"[OK] 找到可用端口: {available_port}")
        return available_port
    else:
        # 实在找不到，返回None让系统随机分配
        print("[WARN] 未找到可用端口，将使用系统随机分配的端口")
        return None
