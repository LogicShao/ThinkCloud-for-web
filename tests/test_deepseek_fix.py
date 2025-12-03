#!/usr/bin/env python3
"""测试DeepSeek provider修复"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(__file__)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在可以正常导入
from src.api_service import api_service


def test_deepseek_chat():
    """测试DeepSeek聊天功能"""
    print("=" * 60)
    print("测试DeepSeek provider...")
    print("=" * 60)

    messages = [{"role": "user", "content": "请用一句话介绍Python"}]

    try:
        response = api_service.chat_completion(
            messages=messages, model="deepseek-chat", stream=False, max_tokens=100
        )

        print("\n✅ 测试成功!")
        print(f"响应类型: {type(response)}")
        print(f"响应长度: {len(response) if isinstance(response, str) else 'N/A'}")
        print(f"响应内容: {response[:200] if isinstance(response, str) else response}")

        if isinstance(response, str) and len(response) > 0:
            print("\n🎉 修复成功！DeepSeek返回了有效内容")
            return True
        else:
            print("\n❌ 响应为空或格式错误")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_deepseek_chat()
    sys.exit(0 if success else 1)
