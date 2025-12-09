# FastAPI 本地 LLM 客户端使用指南

## 📖 概述

ThinkCloud FastAPI 服务提供了一个完全兼容 OpenAI API 格式的本地 LLM
客户端接口，支持多提供商（Cerebras、DeepSeek、OpenAI、DashScope、Kimi）和 35+ 模型。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增依赖：

- `fastapi>=0.104.0` - Web 框架
- `uvicorn[standard]>=0.24.0` - ASGI 服务器
- `pydantic>=2.0.0` - 数据验证

### 2. 配置环境变量

确保 `.env` 文件中配置了至少一个提供商的 API 密钥：

```env
CEREBRAS_API_KEY=your_cerebras_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
KIMI_API_KEY=your_kimi_api_key
```

### 3. 启动服务

**方式一：使用启动脚本（推荐）**

```bash
python fastapi_main.py
```

**方式二：使用 uvicorn 直接启动**

```bash
uvicorn src.fastapi_server:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后会显示：

```
🚀 ThinkCloud FastAPI Server 启动成功！
📍 地址: http://localhost:8000
📖 API 文档: http://localhost:8000/docs
🔗 OpenAPI Schema: http://localhost:8000/openapi.json
💚 健康检查: http://localhost:8000/health
🤖 可用提供商: cerebras, deepseek, openai, dashscope, kimi
📊 模型总数: 35
```

### 4. 测试服务

```bash
python test_fastapi.py
```

测试脚本会自动测试所有 API 端点。

## 📡 API 端点

### 基础端点

#### 1. 根路径

```bash
GET /
```

返回服务基本信息。

#### 2. 健康检查

```bash
GET /health
```

返回服务状态和提供商可用性：

```json
{
  "status": "healthy",
  "providers": {
    "cerebras": true,
    "deepseek": true,
    "openai": false
  },
  "models_count": 35
}
```

### 模型管理

#### 3. 列出所有模型

```bash
GET /v1/models
```

返回所有可用模型列表（OpenAI 格式）：

```json
{
  "object": "list",
  "data": [
    {
      "id": "llama-3.3-70b",
      "object": "model",
      "created": 1234567890,
      "owned_by": "cerebras"
    },
    ...
  ]
}
```

#### 4. 获取指定模型信息

```bash
GET /v1/models/{model_id}
```

示例：

```bash
curl http://localhost:8000/v1/models/llama-3.3-70b
```

### 聊天补全

#### 5. 创建聊天补全（核心端点）

```bash
POST /v1/chat/completions
```

**请求格式（OpenAI 兼容）：**

```json
{
  "model": "llama-3.3-70b",
  "messages": [
    {"role": "user", "content": "你好，请介绍一下你自己"}
  ],
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 1000,
  "stream": false
}
```

**参数说明：**

- `model` **(必填)**: 模型名称（见下方支持的模型列表）
- `messages` **(必填)**: 消息列表
    - `role`: `system` / `user` / `assistant`
    - `content`: 消息内容
- `temperature`: 温度参数（0.0-2.0），控制随机性
- `top_p`: 核采样参数（0.0-1.0）
- `max_tokens`: 最大生成 token 数
- `stream`: 是否使用流式传输（true/false）
- `frequency_penalty`: 频率惩罚（-2.0 到 2.0）
- `presence_penalty`: 存在惩罚（-2.0 到 2.0）

**非流式响应：**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "llama-3.3-70b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是一个AI助手..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

**流式响应（SSE 格式）：**

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3.3-70b","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3.3-70b","choices":[{"index":0,"delta":{"content":"你"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3.3-70b","choices":[{"index":0,"delta":{"content":"好"},"finish_reason":null}]}

...

data: [DONE]
```

## 💡 使用示例

### Python 示例（使用 requests）

#### 非流式请求

```python
import requests
import json

url = "http://localhost:8000/v1/chat/completions"
payload = {
    "model": "llama-3.3-70b",
    "messages": [
        {"role": "user", "content": "什么是量子计算？"}
    ],
    "temperature": 0.7,
    "max_tokens": 500,
    "stream": False
}

response = requests.post(url, json=payload)
result = response.json()

print(result['choices'][0]['message']['content'])
```

#### 流式请求

```python
import requests
import json

url = "http://localhost:8000/v1/chat/completions"
payload = {
    "model": "llama-3.3-70b",
    "messages": [
        {"role": "user", "content": "写一首关于春天的诗"}
    ],
    "temperature": 0.8,
    "stream": True
}

response = requests.post(url, json=payload, stream=True)

for line in response.iter_lines():
    if line:
        line_text = line.decode('utf-8')
        if line_text.startswith('data: '):
            data_str = line_text[6:]
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    print(delta['content'], end='', flush=True)
            except json.JSONDecodeError:
                pass
```

### 使用 OpenAI Python SDK

**完全兼容 OpenAI SDK！**只需修改 `base_url`：

```python
from openai import OpenAI

# 连接到本地 FastAPI 服务
client = OpenAI(
    api_key="dummy-key",  # 本地服务不需要真实密钥
    base_url="http://localhost:8000/v1"
)

# 非流式
response = client.chat.completions.create(
    model="llama-3.3-70b",
    messages=[
        {"role": "user", "content": "你好"}
    ],
    temperature=0.7
)
print(response.choices[0].message.content)

# 流式
stream = client.chat.completions.create(
    model="llama-3.3-70b",
    messages=[
        {"role": "user", "content": "写一首诗"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### cURL 示例

#### 非流式请求

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b",
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "stream": false
  }'
```

#### 流式请求

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }' \
  --no-buffer
```

## 🤖 支持的模型

### Cerebras (10 个模型)

- `llama-3.3-70b` - 最快推理速度
- `llama-3.1-70b`
- `llama-3.1-8b`
- `llama-3.2-1b`
- `llama-3.2-3b`
- `qwen-2.5-coder-14b`
- `qwen-2.5-coder-32b`
- `qwen-2.5-coder-7b`
- `qwen-2.5-14b`
- `qwen-2.5-7b`

### DeepSeek (3 个模型)

- `deepseek-chat` - 通用对话模型
- `deepseek-coder` - 代码专用模型
- `deepseek-reasoner` - 深度推理模型

### OpenAI (4 个模型)

- `gpt-4o` - 最新旗舰模型
- `gpt-4o-mini` - 轻量版本
- `gpt-4-turbo` - GPT-4 加速版
- `gpt-3.5-turbo` - 经典模型

### DashScope / Qwen (11 个模型)

- `qwen-max` - 最强模型
- `qwen-plus` - 平衡性能
- `qwen-turbo` - 快速响应
- `qwen-3-235b-a22b-thinking-2507` - 深度思考模型
- `qwen-3-350b` - 超大参数模型
- `qwen-3-32b` / `qwen-3-14b` / `qwen-3-7b` - 不同规模
- `qwen-2.5-coder-32b-instruct` - 代码优化
- 等...

### Kimi / Moonshot (7 个模型)

- `moonshot-v1-8k` - 8K 上下文
- `moonshot-v1-32k` - 32K 上下文
- `moonshot-v1-128k` - 128K 上下文
- `kimi-k2-0905-preview` - K2 预览版（256K）
- `kimi-k2-turbo-preview` - K2 高速版（60-100 Tokens/s）
- `kimi-k2-thinking` - K2 长思考模型（256K）
- `kimi-k2-thinking-turbo` - K2 长思考高速版

## 🔧 高级配置

### 生产环境部署

**使用 Gunicorn + Uvicorn Worker：**

```bash
pip install gunicorn

gunicorn src.fastapi_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

**使用 Docker：**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.fastapi_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量配置

在 `.env` 文件中：

```env
# API 密钥
CEREBRAS_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
OPENAI_API_KEY=your_key
DASHSCOPE_API_KEY=your_key
KIMI_API_KEY=your_key

# 服务器配置（可选）
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_RELOAD=True
```

### 自定义端口

在 `fastapi_main.py` 中修改：

```python
config = {
    "host": "0.0.0.0",
    "port": 8080,  # 自定义端口
    ...
}
```

## 📊 性能指标

| 模型            | 提供商       | 平均延迟 | 吞吐量       | 适用场景      |
|---------------|-----------|------|-----------|-----------|
| llama-3.3-70b | Cerebras  | ~2s  | 极高        | 快速对话、实时应用 |
| deepseek-chat | DeepSeek  | ~3s  | 高         | 通用对话、中文优化 |
| gpt-4o        | OpenAI    | ~5s  | 中         | 复杂推理、专业输出 |
| qwen-max      | DashScope | ~4s  | 高         | 中文任务、知识问答 |
| kimi-k2-turbo | Kimi      | ~2s  | 60-100T/s | 快速响应、长上下文 |

## 🔒 安全建议

1. **生产环境务必添加认证**：

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/v1/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    # 验证 token
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    ...
```

2. **限流保护**：

```bash
pip install slowapi

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/chat/completions")
@limiter.limit("10/minute")
async def create_chat_completion(...):
    ...
```

3. **HTTPS 部署**：使用 Nginx 或 Caddy 反向代理。

## ❓ 常见问题

### Q1: 如何切换默认模型？

在请求中指定 `model` 参数即可，无需配置。

### Q2: 支持多轮对话吗？

支持！在 `messages` 数组中添加历史消息：

```json
{
  "messages": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    {"role": "user", "content": "介绍一下量子计算"}
  ]
}
```

### Q3: 如何处理错误？

所有错误返回统一格式：

```json
{
  "error": {
    "message": "错误描述",
    "type": "error_type",
    "code": 400
  }
}
```

### Q4: 能否与现有 OpenAI 代码无缝集成？

可以！只需修改 `base_url`：

```python
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)
```

### Q5: 流式响应如何处理？

使用 SSE（Server-Sent Events）格式，逐行读取 `data:` 开头的内容。

## 📚 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [OpenAI API 参考](https://platform.openai.com/docs/api-reference)
- [项目根文档](../CLAUDE.md)
- [深度思考功能](deep_thinking_feature.md)

## 🔄 更新日志

### v1.0.0 (2025-12-09)

- ✅ 初始版本发布
- ✅ 完全兼容 OpenAI API 格式
- ✅ 支持 5 个提供商，35+ 模型
- ✅ 支持流式和非流式响应
- ✅ 提供完整测试套件
- ✅ 集成现有 MultiProviderAPIService

## 📞 支持

如有问题或建议，请提交 Issue 或 Pull Request。

---

**享受使用 ThinkCloud FastAPI 服务！** 🚀
