"""
FastAPI 服务测试脚本

测试所有 API 端点的功能
"""

import requests
import json
import time


class FastAPITester:
    """FastAPI 服务测试类"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def print_section(self, title):
        """打印分节标题"""
        print("\n" + "=" * 60)
        print(f"🧪 {title}")
        print("=" * 60)

    def test_root(self):
        """测试根路径"""
        self.print_section("测试根路径 GET /")
        try:
            response = self.session.get(f"{self.base_url}/")
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False

    def test_health(self):
        """测试健康检查"""
        self.print_section("测试健康检查 GET /health")
        try:
            response = self.session.get(f"{self.base_url}/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False

    def test_list_models(self):
        """测试模型列表"""
        self.print_section("测试模型列表 GET /v1/models")
        try:
            response = self.session.get(f"{self.base_url}/v1/models")
            print(f"状态码: {response.status_code}")
            data = response.json()
            print(f"模型总数: {len(data['data'])}")
            print(f"前 5 个模型:")
            for model in data["data"][:5]:
                print(f"  - {model['id']} ({model['owned_by']})")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False

    def test_retrieve_model(self, model_id="llama-3.3-70b"):
        """测试获取指定模型"""
        self.print_section(f"测试获取模型 GET /v1/models/{model_id}")
        try:
            response = self.session.get(f"{self.base_url}/v1/models/{model_id}")
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False

    def test_chat_completion_non_stream(self, model="llama-3.3-70b"):
        """测试非流式聊天补全"""
        self.print_section(f"测试非流式聊天补全 POST /v1/chat/completions (model={model})")
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
                "temperature": 0.7,
                "max_tokens": 100,
                "stream": False,
            }

            print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            start_time = time.time()
            response = self.session.post(f"{self.base_url}/v1/chat/completions", json=payload)
            elapsed_time = time.time() - start_time

            print(f"\n状态码: {response.status_code}")
            print(f"响应时间: {elapsed_time:.2f} 秒")

            if response.status_code == 200:
                data = response.json()
                print(f"\n响应 ID: {data['id']}")
                print(f"模型: {data['model']}")
                print(f"内容: {data['choices'][0]['message']['content']}")
                print(f"Token 使用: {data['usage']}")
                return True
            else:
                print(f"❌ 错误响应: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 错误: {e}")
            return False

    def test_chat_completion_stream(self, model="llama-3.3-70b"):
        """测试流式聊天补全"""
        self.print_section(
            f"测试流式聊天补全 POST /v1/chat/completions (stream=true, model={model})"
        )
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "用一句话介绍 Python 编程语言"}],
                "temperature": 0.7,
                "max_tokens": 100,
                "stream": True,
            }

            print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            print("\n流式响应内容:")
            print("-" * 60)

            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions", json=payload, stream=True
            )

            full_content = ""
            chunk_count = 0

            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        data_str = line_text[6:]  # 去掉 "data: " 前缀

                        if data_str == "[DONE]":
                            print("\n\n[流式传输完成]")
                            break

                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data["choices"][0]["delta"]

                            if "content" in delta:
                                content = delta["content"]
                                full_content += content
                                print(content, end="", flush=True)
                                chunk_count += 1

                        except json.JSONDecodeError:
                            continue

            elapsed_time = time.time() - start_time

            print("\n" + "-" * 60)
            print(f"✅ 接收到 {chunk_count} 个数据块")
            print(f"✅ 总响应时间: {elapsed_time:.2f} 秒")
            print(f"✅ 完整内容: {full_content}")
            return True

        except Exception as e:
            print(f"❌ 错误: {e}")
            return False

    def test_error_handling(self):
        """测试错误处理"""
        self.print_section("测试错误处理")

        # 测试不存在的模型
        print("\n1️⃣ 测试不存在的模型:")
        try:
            payload = {
                "model": "non-existent-model",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False,
            }
            response = self.session.post(f"{self.base_url}/v1/chat/completions", json=payload)
            print(f"状态码: {response.status_code}")
            print(f"错误响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ 错误: {e}")

        # 测试无效参数
        print("\n2️⃣ 测试无效温度参数:")
        try:
            payload = {
                "model": "llama-3.3-70b",
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 5.0,  # 超出范围 [0, 2]
                "stream": False,
            }
            response = self.session.post(f"{self.base_url}/v1/chat/completions", json=payload)
            print(f"状态码: {response.status_code}")
            print(f"错误响应: {response.json()}")
        except Exception as e:
            print(f"❌ 错误: {e}")

        return True

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "🎯" * 30)
        print("FastAPI 服务完整测试套件")
        print("🎯" * 30)

        results = {
            "根路径": self.test_root(),
            "健康检查": self.test_health(),
            "模型列表": self.test_list_models(),
            "获取模型": self.test_retrieve_model(),
            "非流式聊天": self.test_chat_completion_non_stream(),
            "流式聊天": self.test_chat_completion_stream(),
            "错误处理": self.test_error_handling(),
        }

        # 打印测试总结
        self.print_section("测试总结")
        passed = sum(results.values())
        total = len(results)

        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")

        print(f"\n📊 总计: {passed}/{total} 测试通过")

        if passed == total:
            print("\n🎉 所有测试通过！")
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败")

        return passed == total


def main():
    """主函数"""
    import sys

    # 检查服务是否运行
    print("检查 FastAPI 服务是否运行...")
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            print("✅ 服务正在运行\n")
        else:
            print("⚠️  服务响应异常\n")
    except requests.exceptions.RequestException:
        print("❌ 无法连接到服务！")
        print("请先启动服务: python fastapi_main.py")
        sys.exit(1)

    # 运行测试
    tester = FastAPITester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
