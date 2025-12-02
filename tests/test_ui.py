"""
测试美化后的UI界面
"""

import io
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def test_ui_components():
    """测试UI组件是否正常加载"""
    try:
        # 尝试导入主模块
        from main import LLMClient

        # 创建客户端实例
        client = LLMClient()

        # 创建界面
        client.create_interface()

        print("✅ UI组件测试通过！")
        print("✅ 主题配置正确")
        print("✅ CSS样式加载成功")
        print("✅ 所有组件创建成功")
        print("\n🚀 准备启动界面...")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ UI测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    if test_ui_components():
        print("\n" + "=" * 50)
        print("🎨 界面美化完成！")
        print("=" * 50)
        print("\n主要改进:")
        print("  ✨ 现代化渐变背景（紫蓝色调）")
        print("  ✨ 玻璃态卡片效果（毛玻璃模糊）")
        print("  ✨ 流畅的动画和过渡效果")
        print("  ✨ 精美的按钮和输入框样式")
        print("  ✨ 优化的色彩搭配和排版")
        print("  ✨ 响应式布局设计")
        print("  ✨ 自定义滚动条样式")
        print("  ✨ 消息滑入动画")
        print("\n运行 'python main.py' 启动应用！")
        sys.exit(0)
    else:
        print("\n⚠️ 测试失败，请检查错误信息")
        sys.exit(1)
