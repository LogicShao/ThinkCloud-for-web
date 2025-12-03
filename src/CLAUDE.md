# src/ 模块文档

[根目录](../CLAUDE.md) > **src**

> SimpleLLMFront 核心源代码模块

---

## 模块职责

`src/` 目录包含项目的所有核心业务逻辑：

- **配置管理**：环境变量、提供商/模型映射、端口工具
- **API 编排**：多提供商统一接口（单例模式）
- **提供商实现**：各 AI 提供商的具体实现（工厂模式）
- **对话管理**：历史记录、消息格式转换
- **深度思考**：多阶段推理编排器

## 模块概览

### 依赖关系图

```
config.py (配置层)
    ↓
providers.py (提供商层)
    ↓
api_service.py (服务层 - 单例)
    ↓
deep_think/ (应用层 - 模块化)
    ├── core/ (核心接口和模型)
    ├── stages/ (阶段处理器)
    ├── prompts/ (提示模板)
    ├── orchestrator.py (编排器)
    ├── formatter.py (格式化工具)
    └── utils.py (工具函数)
    ↓
chat_manager.py (辅助层)
```

### 模块清单

| 文件/目录                        | 职责      | 关键类/函数                                          | 说明          |
|------------------------------|---------|-------------------------------------------------|-------------|
| `__init__.py`                | 包标识     | -                                               | 空文件         |
| `config.py`                  | 配置管理    | `PROVIDER_CONFIG`, `get_server_port()`          | 环境变量、端口工具   |
| `providers.py`               | 提供商实现   | `BaseProvider`, `ProviderFactory`               | 工厂模式        |
| `api_service.py`             | API 编排  | `MultiProviderAPIService` (单例)                  | 全局单例        |
| `chat_manager.py`            | 对话管理    | `ChatManager`, `MessageProcessor`               | 历史记录管理      |
| `deep_think/`                | 深度思考系统  | 模块化架构，包含多个子模块                                   | 遵循SOLID原则   |
| `deep_think/core/`           | 核心接口和模型 | `ILLMService`, `IStageProcessor`, 数据模型          | 抽象基类和数据结构   |
| `deep_think/stages/`         | 阶段处理器   | `PlannerStageProcessor`, `SolverStageProcessor` | 各阶段具体实现     |
| `deep_think/prompts/`        | 提示模板系统  | `BasePromptTemplate`, `PromptTemplateManager`   | 模板管理和格式化    |
| `deep_think/orchestrator.py` | 编排器     | `DeepThinkOrchestrator`                         | 协调各阶段执行     |
| `deep_think/formatter.py`    | 格式化工具   | `DeepThinkResultFormatter`                      | 结果格式化       |
| `deep_think/utils.py`        | 工具函数    | `DefaultJSONParser`, `MemoryCacheManager`       | JSON解析、缓存管理 |

---

## config.py

### 模块职责

- 加载环境变量（`.env`）
- 管理提供商配置和模型列表
- 提供端口检测和自动查找功能
- 定义模型参数默认值

### 关键配置

#### 提供商配置

```python
PROVIDER_CONFIG = {
    "cerebras": {
        "api_key": os.environ.get("CEREBRAS_API_KEY"),
        "base_url": "https://api.cerebras.ai",
        "enabled": True
    },
    # ... 其他提供商
}
```

#### 模型映射

```python
PROVIDER_MODELS = {
    "cerebras": ["llama-3.3-70b", ...],  # 10 个模型
    "deepseek": ["deepseek-chat", ...],  # 3 个模型
    "openai": ["gpt-4o", ...],           # 4 个模型
    "dashscope": ["qwen-max", ...],      # 11 个模型
    "kimi": ["moonshot-v1-8k", "kimi-k2-0905-preview", ...],  # 7 个模型
}
```

### 关键函数

#### 端口管理

```python
def is_port_available(port, host="0.0.0.0") -> bool:
    """检查端口是否可用"""

def find_available_port(start_port=7860, max_attempts=100, host="0.0.0.0") -> int:
    """从起始端口开始查找可用端口"""

def get_server_port(preferred_port=SERVER_PORT, host=SERVER_HOST) -> int:
    """获取服务器端口（主入口）"""
```

#### 提供商工具

```python
def get_enabled_providers() -> List[str]:
    """获取已配置且启用的提供商列表"""

def get_model_provider(model: str) -> str:
    """根据模型名称反向查找提供商"""

def check_api_key(provider=None) -> bool:
    """检查 API 密钥是否配置"""
```

### 使用示例

```python
from src.config import (
    PROVIDER_CONFIG,
    PROVIDER_MODELS,
    get_server_port,
    get_model_provider
)

# 获取可用端口
port = get_server_port(7860, "0.0.0.0")

# 查找模型对应的提供商
provider = get_model_provider("llama-3.3-70b")  # "cerebras"

# 获取提供商配置
config = PROVIDER_CONFIG["cerebras"]
```

### 注意事项

- 使用 `python-dotenv` 加载环境变量
- 端口检测使用 socket 绑定测试
- 模型-提供商映射是双向的（正向和反向查找）

---

## providers.py

### 模块职责

- 定义提供商抽象基类 `BaseProvider`
- 实现 4 个具体提供商（Cerebras、DeepSeek、OpenAI、DashScope）
- 提供工厂类 `ProviderFactory` 用于创建提供商实例

### 架构模式

#### 抽象基类

```python
class BaseProvider(ABC):
    """AI提供商抽象基类"""

    @abstractmethod
    def _initialize_client(self):
        """初始化客户端"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查提供商是否可用"""
        pass

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict],
        model: str,
        system_instruction: str = None,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        frequency_penalty: float = None,
        presence_penalty: float = None,
        stream: bool = False,
        **kwargs
    ):
        """调用聊天完成 API"""
        pass
```

#### 工厂类

```python
class ProviderFactory:
    """提供商工厂类"""

    _providers = {
        "cerebras": CerebrasProvider,
        "deepseek": DeepSeekProvider,
        "openai": OpenAIProvider,
        "dashscope": DashScopeProvider,
        "kimi": KimiProvider
    }

    @classmethod
    def create_provider(cls, provider_name: str) -> BaseProvider:
        """创建提供商实例"""
        pass

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """获取可用的提供商列表"""
        pass

    @classmethod
    def register_provider(cls, provider_name: str, provider_class):
        """注册新的提供商（扩展点）"""
        pass
```

### 具体实现

#### CerebrasProvider

- **SDK**: `cerebras.cloud.sdk.Cerebras`
- **特点**: 最快推理速度，低成本
- **模型**: Llama、Qwen 系列

#### DeepSeekProvider

- **SDK**: `openai.OpenAI` (兼容接口)
- **特点**: 强大的中文能力和推理
- **模型**: deepseek-chat、deepseek-coder、deepseek-reasoner

#### OpenAIProvider

- **SDK**: `openai.OpenAI`
- **特点**: 业界领先的 GPT 系列
- **模型**: gpt-4o、gpt-4o-mini、gpt-4-turbo、gpt-3.5-turbo

#### DashScopeProvider

- **SDK**: `openai.OpenAI` (兼容接口)
- **特点**: 阿里云通义千问系列
- **模型**: qwen-max、qwen-plus、qwen-turbo 等

#### KimiProvider

- **SDK**: `openai.OpenAI` (兼容接口)
- **特点**: 月之暗面 Kimi 系列，支持超长上下文
- **模型**:
    - V1 系列: moonshot-v1-8k、moonshot-v1-32k、moonshot-v1-128k
    - K2 系列:
        - kimi-k2-0905-preview (256K 上下文)
        - kimi-k2-turbo-preview (高速版本，60-100 Tokens/s)
        - kimi-k2-thinking (长思考模型，256K 上下文)
        - kimi-k2-thinking-turbo (长思考高速版本)

### 统一接口

所有提供商实现相同的 `chat_completion` 接口：

```python
# 非流式传输
response: str = provider.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    model="llama-3.3-70b",
    temperature=0.7,
    stream=False
)

# 流式传输
stream_generator = provider.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    model="llama-3.3-70b",
    stream=True
)

for chunk in stream_generator:
    print(chunk, end="")
```

### 添加新提供商

1. 创建新类继承 `BaseProvider`
2. 实现 3 个抽象方法
3. 注册到 `ProviderFactory._providers`
4. 更新 `config.py` 配置

示例：

```python
class NewProvider(BaseProvider):
    def __init__(self):
        super().__init__("newprovider")

    def _initialize_client(self):
        config = get_provider_config(self.provider_name)
        api_key = config.get("api_key")
        if api_key:
            self.client = NewSDK(api_key=api_key)

    def is_available(self) -> bool:
        return self.client is not None

    def chat_completion(self, messages, model, **kwargs):
        # 调用 API
        response = self.client.chat(messages=messages, model=model)
        return response.content
```

---

## api_service.py

### 模块职责

- 管理多个提供商实例（单例模式）
- 根据模型名称自动路由到对应提供商
- 统一 API 调用接口
- 提供商状态监控

### 核心类

#### MultiProviderAPIService

```python
class MultiProviderAPIService:
    """多提供商 API 服务类（全局单例）"""

    def __init__(self):
        self.providers = {}  # Dict[str, BaseProvider]
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化所有可用提供商"""
        # 打印初始化状态：[SUCCESS] 或 [FAILED]

    def chat_completion(
            self,
            messages,
            model,
            system_instruction=None,
            temperature=None,
            top_p=None,
            max_tokens=None,
            frequency_penalty=None,
            presence_penalty=None,
            stream=False,
            **kwargs
    ):
        """
        调用聊天完成 API

        自动根据 model 路由到对应提供商
        支持流式和非流式传输
        """

    def is_available(self, provider_name=None) -> bool:
        """检查服务是否可用"""

    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""

    def get_provider_status(self) -> str:
        """获取所有提供商的状态信息"""
```

### 全局单例

**重要**：`api_service` 是全局单例实例，定义在文件底部：

```python
# src/api_service.py 底部
api_service = MultiProviderAPIService()
```

**使用方式**：

```python
# 正确
from src.api_service import api_service

response = api_service.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    model="llama-3.3-70b"
)

# 错误：不要创建新实例
# service = MultiProviderAPIService()  # ❌
```

### 路由逻辑

```python
# 1. 从模型名称获取提供商
provider_name = get_model_provider(model)  # "cerebras"

# 2. 检查提供商是否可用
if provider_name not in self.providers:
    return "错误: 提供商未配置"

# 3. 获取提供商实例
provider = self.providers[provider_name]

# 4. 调用提供商 API
result = provider.chat_completion(messages, model, ...)
```

### 错误处理

- **模型不存在**: 返回错误消息（不抛出异常）
- **提供商不可用**: 返回错误消息（提示检查 API 密钥）
- **API 调用失败**: 捕获异常，返回友好错误消息
- **流式传输**: 错误通过生成器 yield

### 状态监控

```python
status = api_service.get_provider_status()
# 输出: "cerebras: [OK] 可用 | deepseek: [OK] 可用 | openai: [FAIL] 不可用"
```

---

## chat_manager.py

### 模块职责

- 维护对话历史记录（内存存储）
- 提供消息格式转换工具（预留功能）
- 辅助对话管理功能

### 核心类

#### ChatManager

```python
class ChatManager:
    """聊天管理器"""

    def __init__(self):
        self.history = []  # List[Dict]

    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.history.append({"role": role, "content": content})

    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """获取用于 API 调用的消息格式"""
        return self.history.copy()

    def get_gradio_messages(self) -> List[Dict[str, Any]]:
        """获取 Gradio messages 格式的消息"""
        # 当前与 API 格式相同

    def clear_history(self):
        """清空对话历史"""
        self.history.clear()

    def get_history_length(self) -> int:
        """获取历史消息数量"""
        return len(self.history)
```

#### MessageProcessor

```python
class MessageProcessor:
    """消息处理器（预留格式转换）"""

    @staticmethod
    def convert_to_api_messages(gradio_messages: List[Dict]) -> List[Dict]:
        """Gradio messages → API messages"""
        # 当前透传，预留未来格式转换

    @staticmethod
    def convert_from_api_messages(api_messages: List[Dict]) -> List[Dict]:
        """API messages → Gradio messages"""
        # 当前透传

    @staticmethod
    def extract_user_messages(gradio_messages: List[Dict]) -> List[str]:
        """提取用户消息内容"""

    @staticmethod
    def extract_assistant_messages(gradio_messages: List[Dict]) -> List[str]:
        """提取助手消息内容"""
```

### 消息格式

当前统一使用 OpenAI 标准格式：

```python
{
    "role": "user" | "assistant" | "system",
    "content": "消息内容"
}
```

`MessageProcessor` 为未来可能的格式差异预留，当前所有提供商和 Gradio 都使用相同格式。

### 使用示例

```python
from src.chat_manager import ChatManager, MessageProcessor

# 创建管理器
manager = ChatManager()

# 添加对话
manager.add_message("user", "你好")
manager.add_message("assistant", "你好！有什么可以帮助你的吗？")

# 获取 API 格式消息
api_messages = manager.get_messages_for_api()

# 获取 Gradio 格式消息
gradio_messages = manager.get_gradio_messages()

# 查询状态
count = manager.get_history_length()  # 2

# 清空历史
manager.clear_history()
```

---

## deep_think/ 模块化深度思考系统

### 模块化架构

深度思考系统已重构为模块化架构，遵循 SOLID 原则：

```
src/deep_think/
├── __init__.py              # 包导出（保持向后兼容）
├── core/                    # 核心接口和抽象
│   ├── __init__.py
│   ├── interfaces.py       # 抽象基类和接口
│   └── models.py          # 数据模型定义
├── stages/                  # 阶段处理器
│   ├── __init__.py
│   ├── base.py            # 阶段基类
│   ├── planner.py         # Plan阶段
│   ├── solver.py          # Solve阶段
│   ├── synthesizer.py     # Synthesize阶段
│   └── reviewer.py        # Review阶段
├── prompts/                # 提示模板
│   ├── __init__.py
│   ├── base.py            # 模板基类
│   ├── templates.py       # 具体模板
│   └── manager.py         # 模板管理器
├── orchestrator.py         # 编排器（重构）
├── formatter.py           # 格式化工具
└── utils.py               # 工具函数
```

### 设计原则应用

1. **单一职责原则 (S)**: 每个模块/类只负责一个功能
2. **开闭原则 (O)**: 通过接口和抽象基类支持扩展
3. **里氏替换原则 (L)**: 阶段处理器可替换基类
4. **接口隔离原则 (I)**: 每个接口小而专一
5. **依赖倒置原则 (D)**: 依赖抽象而非具体实现

### 核心接口

#### ILLMService (LLM服务接口)

```python
class ILLMService(ABC):
    @abstractmethod
    def chat_completion(self, messages, model, **kwargs) -> Any:
        pass
```

#### IStageProcessor (阶段处理器接口)

```python
class IStageProcessor(ABC):
    @abstractmethod
    def get_stage(self) -> ThinkingStage:
        pass

    @abstractmethod
    def execute(self, context: StageContext, **kwargs) -> StageResult:
        pass
```

#### IPromptTemplate (提示模板接口)

```python
class IPromptTemplate(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def format(self, **kwargs) -> str:
        pass
```

### 数据模型

#### ThinkingStage (思考阶段枚举)

```python
class ThinkingStage(Enum):
    PLAN = "plan"
    SOLVE = "solve"
    SYNTHESIZE = "synthesize"
    REVIEW = "review"
```

#### Plan (规划结果)

```python
@dataclass
class Plan:
    clarified_question: str
    subtasks: List[Subtask]
    plan_text: str
    reasoning_approach: str = ""
```

#### SubtaskResult (子任务结果)

```python
@dataclass
class SubtaskResult:
    subtask_id: int
    description: str
    analysis: str
    intermediate_conclusion: str
    confidence: float
    limitations: List[str] = field(default_factory=list)
    needs_external_info: bool = False
    suggested_tools: List[str] = field(default_factory=list)
```

#### DeepThinkResult (完整结果)

```python
@dataclass
class DeepThinkResult:
    original_question: str
    final_answer: str
    plan: Plan
    subtask_results: List[SubtaskResult]
    review: Optional[ReviewResult] = None
    total_llm_calls: int = 0
    thinking_process_summary: str = ""
```

### 阶段处理器

#### BaseStageProcessor (基类)

```python
class BaseStageProcessor(IStageProcessor):
    def __init__(self, llm_service, json_parser, verbose=True):
        self.llm_service = llm_service
        self.json_parser = json_parser
        self.verbose = verbose

    @abstractmethod
    def get_stage(self) -> ThinkingStage:
        pass

    @abstractmethod
    def execute(self, context: StageContext, **kwargs) -> StageResult:
        pass
```

#### 具体阶段处理器

- **PlannerStageProcessor**: 规划阶段，负责问题澄清和子任务拆解
- **SolverStageProcessor**: 解决阶段，负责逐个分析子任务
- **SynthesizerStageProcessor**: 整合阶段，负责综合所有结论生成最终答案
- **ReviewerStageProcessor**: 审查阶段，负责对最终答案进行质量审查

### 提示模板系统

#### BasePromptTemplate (基类)

```python
class BasePromptTemplate(IPromptTemplate):
    def __init__(self, name: str, stage: ThinkingStage, template: str):
        self._name = name
        self._stage = stage
        self._template = template

    def format(self, **kwargs) -> str:
        return self._template.format(**kwargs)
```

#### 具体模板

- **PlanPromptTemplate**: 规划阶段提示模板
- **SubtaskPromptTemplate**: 子任务分析提示模板
- **SynthesizePromptTemplate**: 整合阶段提示模板
- **ReviewPromptTemplate**: 审查阶段提示模板

#### PromptTemplateManager (管理器)

```python
class PromptTemplateManager:
    def __init__(self):
        self._templates: Dict[str, IPromptTemplate] = {}
        self._stage_templates: Dict[ThinkingStage, IPromptTemplate] = {}
        self._initialize_default_templates()

    def register_template(self, template: IPromptTemplate) -> None:
        pass

    def get_template_by_stage(self, stage: ThinkingStage) -> Optional[IPromptTemplate]:
        pass
```

### 编排器 (DeepThinkOrchestrator)

```python
class DeepThinkOrchestrator(IOrchestrator):
    def __init__(
        self,
        api_service: ILLMService,
        model: str,
        max_subtasks: int = 6,
        enable_review: bool = True,
        verbose: bool = True,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        # 初始化所有组件
        self.json_parser = DefaultJSONParser()
        self.cache_manager = MemoryCacheManager()
        self.prompt_manager = PromptTemplateManager()
        self._initialize_stage_processors()

    def run(self, question: str, **kwargs) -> DeepThinkResult:
        # 1. 创建执行上下文
        context = self._create_context()

        # 2. 执行规划阶段
        plan = self._execute_plan_stage(context, question)

        # 3. 执行解决阶段
        subtask_results = self._execute_solve_stage(context, question, plan)

        # 4. 执行整合阶段
        final_answer = self._execute_synthesize_stage(context, question, plan, subtask_results)

        # 5. 执行审查阶段（可选）
        review_result = None
        if self.enable_review:
            review_result = self._execute_review_stage(context, question, final_answer)

        # 6. 返回完整结果
        return DeepThinkResult(...)
```

### 工具类

#### DefaultJSONParser (JSON解析器)

```python
class DefaultJSONParser(IJSONParser):
    def parse(self, response: str) -> Dict[str, Any]:
        # 支持容错处理：直接解析、提取代码块、查找花括号内容
        pass
```

#### MemoryCacheManager (缓存管理器)

```python
class MemoryCacheManager(ICacheManager):
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        pass

    def set(self, key: str, value: Any) -> None:
        pass
```

### 格式化工具

#### DeepThinkResultFormatter

```python
class DeepThinkResultFormatter(IResultFormatter):
    def format(self, result: DeepThinkResult, **kwargs) -> str:
        # 格式化深度思考结果为用户友好的Markdown输出
        pass

# 兼容旧接口
def format_deep_think_result(result: DeepThinkResult, include_process: bool = True) -> str:
    formatter = DeepThinkResultFormatter()
    return formatter.format(result, include_process=include_process)
```

### 工作流程

```
用户问题
    ↓
【Stage 1: Plan】→ PlannerStageProcessor
    ↓
    问题澄清 + 子任务拆解 → Plan
    ↓
【Stage 2: Solve】→ SolverStageProcessor
    ↓
    ├─ 子任务 1 分析 → SubtaskResult
    ├─ 子任务 2 分析（基于前序结果）
    ├─ 子任务 3 分析
    └─ ...
    ↓
【Stage 3: Synthesize】→ SynthesizerStageProcessor
    ↓
    整合所有子任务结论 → 最终答案
    ↓
【Stage 4: Review】（可选）→ ReviewerStageProcessor
    ↓
    质量审查 + 改进建议 → ReviewResult
    ↓
DeepThinkResult → DeepThinkResultFormatter → 用户输出
```

### 使用示例（保持向后兼容）

```python
# 旧代码仍然有效
from src.deep_think import DeepThinkOrchestrator, format_deep_think_result

# 创建编排器
orchestrator = DeepThinkOrchestrator(
    api_service=api_service,
    model="qwen-3-235b-a22b-thinking-2507",
    max_subtasks=6,
    enable_review=True,
    verbose=True
)

# 执行深度思考
question = "如何提高编程技能？请从理论学习、实践项目、持续改进三个角度分析。"
result = orchestrator.run(question)

# 格式化输出
formatted = format_deep_think_result(result, include_process=True)
print(formatted)
```

### 扩展新功能

#### 添加新的阶段处理器

```python
class CustomStageProcessor(BaseStageProcessor):
    def get_stage(self) -> ThinkingStage:
        return ThinkingStage.CUSTOM

    def execute(self, context: StageContext, **kwargs) -> StageResult:
        # 自定义逻辑
        pass
```

#### 添加新的提示模板

```python
class CustomPromptTemplate(BasePromptTemplate):
    def __init__(self):
        template = """自定义模板内容 {param1} {param2}"""
        super().__init__("custom_prompt", ThinkingStage.CUSTOM, template)
```

#### 注册到系统

```python
# 在编排器中扩展
orchestrator.prompt_manager.register_template(CustomPromptTemplate())
```

### 性能指标

- **LLM 调用次数**: 5-9 次（1 规划 + N 分析 + 1 整合 + 1 审查）
- **Token 消耗**: 约 12,000 tokens/会话
- **响应时间**: 30-180 秒
- **内存缓存**: 支持中间结果缓存，减少重复计算
- **扩展性**: 模块化设计，易于添加新阶段和功能

### 优势

1. **可维护性**: 模块分离，职责清晰
2. **可测试性**: 每个模块可独立测试
3. **可扩展性**: 通过接口和抽象基类支持扩展
4. **灵活性**: 可替换具体实现，如使用不同的JSON解析器或缓存策略
5. **向后兼容**: 保持原有API不变，现有代码无需修改

---

## 模块间依赖

### 导入关系

```python
# config.py - 无依赖
import os
from dotenv import load_dotenv

# providers.py - 依赖 config
from .config import get_provider_config
from cerebras.cloud.sdk import Cerebras
from openai import OpenAI

# api_service.py - 依赖 config, providers
from .config import get_model_provider
from .providers import ProviderFactory

# chat_manager.py - 无依赖
from typing import List, Dict, Any

# deep_think/ - 依赖 api_service（通过参数注入）
# deep_think/core/ - 核心接口和模型
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# deep_think/stages/ - 阶段处理器
from ..core.interfaces import ILLMService, IJSONParser, IStageProcessor
from ..core.models import StageContext, StageResult, ThinkingStage

# deep_think/prompts/ - 提示模板
from ..core.interfaces import IPromptTemplate
from ..core.models import ThinkingStage

# deep_think/orchestrator.py - 编排器
from .core.interfaces import ILLMService, IOrchestrator
from .core.models import DeepThinkResult, Plan, ReviewResult, StageContext, SubtaskResult
from .prompts.manager import PromptTemplateManager
from .stages import PlannerStageProcessor, SolverStageProcessor, SynthesizerStageProcessor, ReviewerStageProcessor
from .utils import DefaultJSONParser, MemoryCacheManager, generate_cache_key

# deep_think/formatter.py - 格式化工具
from .core.interfaces import IResultFormatter
from .core.models import DeepThinkResult

# deep_think/utils.py - 工具函数
import hashlib
import json
import threading
from typing import Any, Dict
from .core.interfaces import ICacheManager, IJSONParser
```

### 初始化顺序

```
1. config.py 加载环境变量
2. providers.py 定义提供商类
3. api_service.py 创建全局单例（初始化提供商）
4. chat_manager.py 独立初始化
5. deep_think/ 模块初始化：
   a. core/ 定义接口和模型
   b. prompts/ 初始化模板管理器
   c. utils/ 初始化工具类
   d. stages/ 初始化阶段处理器
   e. orchestrator.py 创建编排器实例
6. 应用层使用 DeepThinkOrchestrator 接收 api_service 实例
```

---

## 开发指南

### 修改配置

**添加新模型**：

```python
# src/config.py
PROVIDER_MODELS["cerebras"].append("new-model-name")
```

**添加新提供商**：

1. 在 `providers.py` 创建类
2. 注册到 `ProviderFactory`
3. 在 `config.py` 添加配置

### 修改深度思考

#### 调整 Prompt 模板

```python
# src/deep_think/prompts/templates.py
class PlanPromptTemplate(BasePromptTemplate):
    def __init__(self):
        template = """修改后的 Prompt..."""
        super().__init__("plan_prompt", ThinkingStage.PLAN, template)


# 或者通过模板管理器动态注册
from src.deep_think.prompts.manager import PromptTemplateManager
from src.deep_think.prompts.base import BasePromptTemplate
from src.deep_think.core.models import ThinkingStage


class CustomPromptTemplate(BasePromptTemplate):
    def __init__(self):
        template = """自定义模板内容"""
        super().__init__("custom_prompt", ThinkingStage.PLAN, template)


manager = PromptTemplateManager()
manager.register_template(CustomPromptTemplate())
```

#### 修改阶段逻辑

```python
# src/deep_think/stages/planner.py
class CustomPlannerStageProcessor(PlannerStageProcessor):
    def execute(self, context: StageContext, **kwargs) -> StageResult:
        # 自定义规划逻辑
        pass


# 在编排器中使用自定义处理器
orchestrator.planner = CustomPlannerStageProcessor(
    llm_service=orchestrator.api_service,
    json_parser=orchestrator.json_parser,
    prompt_template=orchestrator.prompt_manager.get_template_by_stage(ThinkingStage.PLAN),
    max_subtasks=orchestrator.max_subtasks,
    verbose=orchestrator.verbose,
)
```

#### 添加新的阶段

```python
# 1. 定义新的阶段枚举
from src.deep_think.core.models import ThinkingStage
# 注意：需要扩展ThinkingStage枚举或使用字符串标识

# 2. 创建新的阶段处理器
from src.deep_think.stages.base import BaseStageProcessor


class CustomStageProcessor(BaseStageProcessor):
    def get_stage(self) -> str:  # 或扩展ThinkingStage
        return "custom_stage"

    def execute(self, context: StageContext, **kwargs) -> StageResult:
        # 自定义阶段逻辑
        pass

# 3. 在编排器中集成新阶段
```

### 测试建议

- **单元测试**:
    - 测试 `config.py` 工具函数
    - 测试各个阶段处理器的独立功能
    - 测试提示模板的格式化
- **集成测试**:
    - 测试 `api_service.py` 提供商路由
    - 测试阶段处理器与LLM服务的集成
- **端到端测试**:
    - 测试 `deep_think/` 模块完整流程
    - 测试编排器的整体协调功能

---

## 常见问题 (FAQ)

### Q: 如何切换默认模型？

修改 `src/config.py`:

```python
DEFAULT_MODEL = "your-model-name"
DEFAULT_PROVIDER = "your-provider-name"
```

### Q: 如何禁用某个提供商？

修改 `src/config.py`:

```python
PROVIDER_CONFIG["provider_name"]["enabled"] = False
```

### Q: 为什么不能创建多个 api_service 实例？

因为采用单例模式，避免重复初始化提供商。正确用法：

```python
from src.api_service import api_service  # 使用全局实例
```

### Q: 如何添加自定义参数到 API 调用？

通过 `**kwargs` 传递：

```python
response = api_service.chat_completion(
    messages=messages,
    model=model,
    custom_param="value",  # 自定义参数
    **kwargs
)
```

### Q: 深度思考可以使用流式传输吗？

暂不支持，因为多阶段推理需要完整响应才能进入下一阶段。未来可实现阶段性流式输出。

---

## 相关文件清单

### 核心文件

- `__init__.py` - 包标识
- `config.py` - 配置管理
- `providers.py` - 提供商实现
- `api_service.py` - API 编排
- `chat_manager.py` - 对话管理
- `deep_think.py` - 深度思考

### 依赖的外部文件

- `../.env` - API 密钥配置
- `../main.py` - UI 入口（使用 src.*）

### 相关文档

- `../doc/deep_thinking_feature.md` - 深度思考完整文档
- `../CLAUDE.md` - 根级 AI 指引

---

## 变更记录 (Changelog)

### 2025-12-01 15:07:03

- 初始化 src/ 模块文档
- 详细说明各模块职责和接口
- 添加使用示例和开发指南

---

[返回根目录](../CLAUDE.md)
