"""
测试优化后的模型选择功能
"""

import io
import sys

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src.config import (
    extract_model_id,
    get_model_display_name,
    get_model_provider,
    get_models_grouped_by_provider,
    get_models_with_provider,
)


def test_models_with_provider():
    """测试带提供商信息的模型列表"""
    print("\n" + "=" * 60)
    print("测试1: 带提供商信息的模型列表")
    print("=" * 60)

    models = get_models_with_provider()
    print(f"✅ 找到 {len(models)} 个模型")

    # 显示前5个模型
    print("\n前5个模型示例:")
    for i, (display, model_id) in enumerate(models[:5], 1):
        print(f"  {i}. {display}")
        print(f"     → 模型ID: {model_id}")

    return len(models) > 0


def test_grouped_models():
    """测试分组的模型字典"""
    print("\n" + "=" * 60)
    print("测试2: 按提供商分组的模型")
    print("=" * 60)

    grouped = get_models_grouped_by_provider()
    print(f"✅ 找到 {len(grouped)} 个提供商")

    for provider_name, models in grouped.items():
        print(f"\n{provider_name}:")
        print(f"  模型数量: {len(models)}")
        print(f"  示例: {models[0] if models else 'N/A'}")

    return len(grouped) > 0


def test_extract_model_id():
    """测试提取模型ID"""
    print("\n" + "=" * 60)
    print("测试3: 提取模型ID")
    print("=" * 60)

    test_cases = [
        "🔹 Cerebras | llama-3.3-70b",
        "🔹 DeepSeek | deepseek-chat",
        "🔹 OpenAI | gpt-4o",
        "plain-model-name",
    ]

    all_passed = True
    for display_name in test_cases:
        extracted = extract_model_id(display_name)
        print(f"输入: {display_name}")
        print(f"输出: {extracted}")

        # 验证提取正确
        if " | " in display_name:
            expected = display_name.split(" | ")[-1]
            if extracted == expected:
                print("✅ 正确")
            else:
                print(f"❌ 错误，期望: {expected}")
                all_passed = False
        else:
            if extracted == display_name:
                print("✅ 正确（无提供商前缀）")
            else:
                print("❌ 错误")
                all_passed = False
        print()

    return all_passed


def test_get_display_name():
    """测试获取显示名称"""
    print("\n" + "=" * 60)
    print("测试4: 获取模型显示名称")
    print("=" * 60)

    test_models = ["llama-3.3-70b", "deepseek-chat", "gpt-4o", "qwen-max"]

    all_passed = True
    for model_id in test_models:
        display_name = get_model_display_name(model_id)
        provider = get_model_provider(model_id)

        print(f"模型ID: {model_id}")
        print(f"提供商: {provider}")
        print(f"显示名: {display_name}")

        # 验证格式
        if provider and f" | {model_id}" in display_name:
            print("✅ 格式正确")
        elif not provider:
            print("⚠️  未找到提供商（可能未配置）")
        else:
            print("❌ 格式错误")
            all_passed = False
        print()

    return all_passed


def test_round_trip():
    """测试往返转换（显示名 → 模型ID → 显示名）"""
    print("\n" + "=" * 60)
    print("测试5: 往返转换测试")
    print("=" * 60)

    models = get_models_with_provider()
    if not models:
        print("❌ 没有可用的模型")
        return False

    # 测试前3个模型
    all_passed = True
    for display, original_id in models[:3]:
        extracted_id = extract_model_id(display)
        reconstructed_display = get_model_display_name(extracted_id)

        print(f"原始显示名: {display}")
        print(f"提取的ID: {extracted_id}")
        print(f"重建显示名: {reconstructed_display}")

        if extracted_id == original_id and display == reconstructed_display:
            print("✅ 往返转换成功")
        else:
            print("❌ 往返转换失败")
            all_passed = False
        print()

    return all_passed


def test_ui_integration():
    """测试UI集成"""
    print("\n" + "=" * 60)
    print("测试6: UI组件集成")
    print("=" * 60)

    try:
        from main import LLMClient

        client = LLMClient()
        client.create_interface()

        print("✅ UI组件创建成功")
        print("✅ 模型选择器已集成")
        return True
    except Exception as e:
        print(f"❌ UI集成失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 模型选择功能测试")
    print("=" * 60)

    results = []

    # 运行各项测试
    try:
        results.append(("带提供商信息的模型列表", test_models_with_provider()))
        results.append(("按提供商分组", test_grouped_models()))
        results.append(("提取模型ID", test_extract_model_id()))
        results.append(("获取显示名称", test_get_display_name()))
        results.append(("往返转换", test_round_trip()))
        results.append(("UI集成", test_ui_integration()))
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
        print("\n✨ 模型选择功能优化完成:")
        print("   • 模型显示格式：🔹 提供商 | 模型名称")
        print("   • 支持的提供商：Cerebras、DeepSeek、OpenAI、DashScope")
        print("   • 自动提取模型ID进行API调用")
        print("   • 精美的深色主题样式")
        print("\n🚀 运行 'python main.py' 查看效果！")
        return True
    else:
        print("⚠️  部分测试未通过，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
