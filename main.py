"""
ThinkCloud for Web - 多提供商 LLM 客户端
支持深度思考模式的智能对话系统
"""

from src.config import (
    SERVER_HOST,
    SERVER_PORT,
    check_api_key,
    get_server_port,
)
from src.ui_client import UIClient


def main():
    """主函数 - 应用启动入口"""
    print("[START] 启动 ThinkCloud for Web...")

    # 检查API配置
    if not check_api_key():
        print("\n[WARN] 请先配置至少一个API密钥环境变量")
        print("   创建.env文件并添加以下变量之一:")
        print("   - CEREBRAS_API_KEY=your_api_key_here")
        print("   - DEEPSEEK_API_KEY=your_api_key_here")
        print("   - OPENAI_API_KEY=your_api_key_here")
        print("   - DASHSCOPE_API_KEY=your_api_key_here")
        print("   - KIMI_API_KEY=your_api_key_here")
        print("\n您仍然可以启动界面，但需要配置API密钥才能正常使用。")

    # 自动查找可用端口
    print("\n[PORT] 检查端口可用性...")
    available_port = get_server_port(SERVER_PORT, SERVER_HOST)

    # 创建并启动应用
    client = UIClient()
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
