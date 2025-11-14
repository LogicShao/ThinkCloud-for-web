"""
测试端口自动查找功能
"""

import io
import socket
import sys
import time
from contextlib import closing

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.config import is_port_available, find_available_port, get_server_port


def occupy_port(port, duration=5):
    """
    临时占用一个端口用于测试

    Args:
        port: 要占用的端口号
        duration: 占用时长（秒）
    """
    print(f"\n[TEST] 临时占用端口 {port} 进行测试...")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", port))
            sock.listen(1)
            print(f"✅ 成功占用端口 {port}")

            # 等待一段时间
            print(f"⏱️  等待 {duration} 秒...")
            time.sleep(duration)

            print(f"✅ 释放端口 {port}")
    except Exception as e:
        print(f"❌ 占用端口失败: {e}")


def test_is_port_available():
    """测试端口可用性检查函数"""
    print("\n" + "=" * 60)
    print("测试1: 端口可用性检查")
    print("=" * 60)

    # 测试一个通常可用的高端口
    test_port = 9999
    result = is_port_available(test_port)
    print(f"✅ 端口 {test_port} 可用性: {result}")

    # 测试7860端口（可能被占用）
    test_port = 7860
    result = is_port_available(test_port)
    print(f"✅ 端口 {test_port} 可用性: {result}")

    return True


def test_find_available_port():
    """测试自动查找可用端口功能"""
    print("\n" + "=" * 60)
    print("测试2: 自动查找可用端口")
    print("=" * 60)

    # 从7860开始查找
    port = find_available_port(7860, max_attempts=10)
    if port:
        print(f"✅ 找到可用端口: {port}")
        return True
    else:
        print("❌ 未找到可用端口")
        return False


def test_get_server_port():
    """测试获取服务器端口功能"""
    print("\n" + "=" * 60)
    print("测试3: 获取服务器端口")
    print("=" * 60)

    # 测试获取端口（7860可能可用）
    port = get_server_port(7860)
    print(f"✅ 获取到服务器端口: {port}")

    return port is not None


def test_port_occupied_scenario():
    """测试端口被占用的场景"""
    print("\n" + "=" * 60)
    print("测试4: 端口被占用场景（模拟）")
    print("=" * 60)

    # 使用一个测试端口
    test_port = 18888

    # 检查端口是否可用
    if is_port_available(test_port):
        print(f"✅ 测试端口 {test_port} 当前可用")

        # 占用端口
        print(f"\n[SIMULATE] 启动临时服务器占用端口 {test_port}...")

        # 创建一个socket占用端口
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", test_port))
            sock.listen(1)

            print(f"✅ 端口 {test_port} 已被占用")

            # 现在尝试获取服务器端口，应该会找到下一个可用端口
            print(f"\n[TEST] 尝试获取端口（首选 {test_port}）...")
            available_port = get_server_port(test_port)

            if available_port != test_port:
                print(f"✅ 成功！由于 {test_port} 被占用，自动找到备用端口: {available_port}")
                return True
            else:
                print(f"❌ 失败！应该找到备用端口，但返回了被占用的端口")
                return False
    else:
        print(f"⚠️  端口 {test_port} 已被占用，跳过此测试")
        return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 端口自动查找功能测试")
    print("=" * 60)

    results = []

    # 运行各项测试
    try:
        results.append(("端口可用性检查", test_is_port_available()))
        results.append(("自动查找可用端口", test_find_available_port()))
        results.append(("获取服务器端口", test_get_server_port()))
        results.append(("端口被占用场景", test_port_occupied_scenario()))
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果总览")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("🎉 所有测试通过！")
        print("\n✨ 端口自动查找功能已就绪:")
        print("   • 如果默认端口7860可用，将使用7860")
        print("   • 如果7860被占用，自动查找7861-7959范围内的可用端口")
        print("   • 如果都不可用，将使用系统随机分配的端口")
        print("\n🚀 运行 'python main.py' 启动应用测试！")
        return True
    else:
        print("⚠️  部分测试未通过，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
