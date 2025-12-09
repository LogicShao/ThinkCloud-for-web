"""
FastAPI 服务 - 提供 OpenAI 格式兼容的 LLM 客户端接口
"""

import json
import time
import uuid
from typing import List, Optional, Union, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .api_service import api_service
from .config import PROVIDER_MODELS, get_model_provider

# 初始化 FastAPI 应用
app = FastAPI(
    title="ThinkCloud API",
    description="OpenAI 格式兼容的多提供商 LLM 客户端",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Pydantic 模型定义 ==========


class Message(BaseModel):
    """聊天消息"""

    role: str = Field(..., description="消息角色: system/user/assistant")
    content: str = Field(..., description="消息内容")


class ChatCompletionRequest(BaseModel):
    """聊天补全请求（OpenAI 格式）"""

    model: str = Field(..., description="模型名称")
    messages: List[Message] = Field(..., description="消息列表")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="温度参数")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="核采样参数")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="最大生成token数")
    stream: bool = Field(default=False, description="是否使用流式传输")
    frequency_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0, description="频率惩罚"
    )
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="存在惩罚")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="停止序列")
    n: Optional[int] = Field(default=1, description="生成数量")
    user: Optional[str] = Field(default=None, description="用户标识")


class ChatCompletionResponseChoice(BaseModel):
    """聊天补全响应选项"""

    index: int
    message: Message
    finish_reason: str  # stop, length, content_filter


class Usage(BaseModel):
    """Token 使用统计"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """聊天补全响应（OpenAI 格式）"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Usage


class ChatCompletionStreamChoice(BaseModel):
    """流式响应选项"""

    index: int
    delta: dict  # {"role": "assistant", "content": "..."}
    finish_reason: Optional[str] = None


class ChatCompletionStreamResponse(BaseModel):
    """流式响应（OpenAI 格式）"""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]


class Model(BaseModel):
    """模型信息"""

    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelList(BaseModel):
    """模型列表"""

    object: str = "list"
    data: List[Model]


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str
    providers: dict
    models_count: int


# ========== 辅助函数 ==========


def generate_id() -> str:
    """生成唯一 ID"""
    return f"chatcmpl-{uuid.uuid4().hex[:16]}"


def estimate_tokens(text: str) -> int:
    """估算 token 数量（简单实现）"""
    # 简化估算：中文按字符数，英文按空格分词
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    english_words = len(text.split())
    return chinese_chars + english_words


def format_openai_message(messages: List[Message]) -> List[dict]:
    """将 Pydantic 模型转换为字典"""
    return [{"role": msg.role, "content": msg.content} for msg in messages]


# ========== API 路由 ==========


@app.get("/", tags=["基础"])
async def root():
    """根路径"""
    return {
        "message": "ThinkCloud API Server",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", response_model=HealthResponse, tags=["基础"])
async def health_check():
    """健康检查"""
    providers_status = {}
    for provider_name in api_service.get_available_providers():
        providers_status[provider_name] = api_service.is_available(provider_name)

    # 统计所有可用模型数量
    total_models = sum(len(models) for models in PROVIDER_MODELS.values())

    return {
        "status": "healthy" if api_service.is_available() else "unhealthy",
        "providers": providers_status,
        "models_count": total_models,
    }


@app.get("/v1/models", response_model=ModelList, tags=["模型"])
async def list_models():
    """列出所有可用模型"""
    models = []
    timestamp = int(time.time())

    for provider_name, model_list in PROVIDER_MODELS.items():
        for model_id in model_list:
            models.append(
                {"id": model_id, "object": "model", "created": timestamp, "owned_by": provider_name}
            )

    return {"object": "list", "data": models}


@app.get("/v1/models/{model_id}", response_model=Model, tags=["模型"])
async def retrieve_model(model_id: str):
    """获取指定模型信息"""
    provider_name = get_model_provider(model_id)

    if not provider_name:
        raise HTTPException(status_code=404, detail=f"模型 '{model_id}' 不存在")

    return {
        "id": model_id,
        "object": "model",
        "created": int(time.time()),
        "owned_by": provider_name,
    }


@app.post("/v1/chat/completions", tags=["聊天"])
async def create_chat_completion(request: ChatCompletionRequest):
    """
    创建聊天补全（支持流式和非流式）

    完全兼容 OpenAI API 格式
    """
    # 验证模型
    provider_name = get_model_provider(request.model)
    if not provider_name:
        raise HTTPException(status_code=400, detail=f"不支持的模型: {request.model}")

    # 检查提供商是否可用
    if not api_service.is_available(provider_name):
        raise HTTPException(status_code=503, detail=f"提供商 '{provider_name}' 不可用，请检查配置")

    # 转换消息格式
    messages = format_openai_message(request.messages)

    # 流式响应
    if request.stream:
        return StreamingResponse(
            stream_chat_completion(request, messages), media_type="text/event-stream"
        )

    # 非流式响应
    return await non_stream_chat_completion(request, messages)


async def non_stream_chat_completion(
    request: ChatCompletionRequest, messages: List[dict]
) -> ChatCompletionResponse:
    """非流式聊天补全"""
    try:
        # 调用 API 服务
        response_content = api_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stream=False,
        )

        # 估算 token 使用量
        prompt_text = " ".join([msg["content"] for msg in messages])
        prompt_tokens = estimate_tokens(prompt_text)
        completion_tokens = estimate_tokens(response_content)

        # 构造 OpenAI 格式响应
        return ChatCompletionResponse(
            id=generate_id(),
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(role="assistant", content=response_content),
                    finish_reason="stop",
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API 调用失败: {str(e)}")


async def stream_chat_completion(
    request: ChatCompletionRequest, messages: List[dict]
) -> AsyncIterator[str]:
    """流式聊天补全"""
    try:
        # 生成唯一 ID
        completion_id = generate_id()
        timestamp = int(time.time())

        # 发送初始消息（角色声明）
        initial_chunk = ChatCompletionStreamResponse(
            id=completion_id,
            object="chat.completion.chunk",
            created=timestamp,
            model=request.model,
            choices=[
                ChatCompletionStreamChoice(
                    index=0, delta={"role": "assistant", "content": ""}, finish_reason=None
                )
            ],
        )
        yield f"data: {initial_chunk.model_dump_json()}\n\n"

        # 调用 API 服务（流式）
        stream_generator = api_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stream=True,
        )

        # 流式发送内容
        for chunk_content in stream_generator:
            if chunk_content:
                chunk = ChatCompletionStreamResponse(
                    id=completion_id,
                    object="chat.completion.chunk",
                    created=timestamp,
                    model=request.model,
                    choices=[
                        ChatCompletionStreamChoice(
                            index=0, delta={"content": chunk_content}, finish_reason=None
                        )
                    ],
                )
                yield f"data: {chunk.model_dump_json()}\n\n"

        # 发送结束消息
        final_chunk = ChatCompletionStreamResponse(
            id=completion_id,
            object="chat.completion.chunk",
            created=timestamp,
            model=request.model,
            choices=[ChatCompletionStreamChoice(index=0, delta={}, finish_reason="stop")],
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        error_response = {
            "error": {
                "message": f"流式传输失败: {str(e)}",
                "type": "stream_error",
                "code": "stream_error",
            }
        }
        yield f"data: {json.dumps(error_response)}\n\n"


# ========== 错误处理 ==========


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    return {
        "error": {"message": exc.detail, "type": "invalid_request_error", "code": exc.status_code}
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    return {
        "error": {"message": f"内部服务器错误: {str(exc)}", "type": "server_error", "code": 500}
    }


# ========== 启动信息 ==========


@app.on_event("startup")
async def startup_event():
    """启动时打印信息"""
    print("\n" + "=" * 60)
    print("🚀 ThinkCloud FastAPI Server 启动成功！")
    print("=" * 60)
    print(f"📖 API 文档: http://localhost:8000/docs")
    print(f"🔗 OpenAPI Schema: http://localhost:8000/openapi.json")
    print(f"💚 健康检查: http://localhost:8000/health")
    print(f"🤖 可用提供商: {', '.join(api_service.get_available_providers())}")
    print(f"📊 模型总数: {sum(len(models) for models in PROVIDER_MODELS.values())}")
    print("=" * 60 + "\n")
