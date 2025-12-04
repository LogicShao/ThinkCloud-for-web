# 🚀 ThinkCloud for Web

一个基于 Gradio 的多提供商 LLM 聊天客户端，支持 Cerebras、DeepSeek、OpenAI、DashScope (阿里云百炼) 和 Kimi (月之暗面) 等多种
AI 提供商。

**✨ 特色功能：🧠 深度思考模式** - 通过四阶段推理系统（规划→分析→整合→审查）深入分析复杂问题，支持网络搜索增强和结构化输出。

**⚙️ 高级参数控制** - 支持 System Instruction、Temperature、Top P、Max Tokens 等全面参数调节。

**🏗️ 模块化架构** - 遵循 SOLID 原则的模块化深度思考系统，易于扩展和维护。

![Version](https://img.shields.io/badge/version-3.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📋 功能特性

### 核心功能

- 🚀 **多提供商支持** - Cerebras、DeepSeek、OpenAI、DashScope (阿里云百炼)、Kimi (月之暗面)
- 🎨 **美观的 Gradio Web 界面** - 响应式设计，支持移动端
- 🔄 **多轮对话历史** - 自动保存对话上下文
- 🔧 **灵活的模型选择** - 35+ 模型可选，智能提供商切换
- ⚡ **实时状态监控** - 提供商可用性实时显示
- 📋 **便捷的内容操作** - 一键复制、导出对话记录
- ⚙️ **全面参数控制** - System Instruction、Temperature、Top P、Max Tokens 等

### 🧠 深度思考模式 （v3.0 新特性）

- **模块化架构** - 遵循 SOLID 原则，职责分离，易于维护和扩展
- **四阶段推理流程** - Plan (规划) → Solve (分析) → Synthesize (整合) → Review (审查)
- **智能任务拆解** - 自动将复杂问题分解为 3-8 个子任务
- **提示模板系统** - 可配置的 Prompt 模板管理器，支持多语言优化
- **缓存管理** - 支持中间结果缓存，减少重复计算
- **🌐 网络搜索增强** - 自动搜索外部信息辅助分析（可选功能）
- **结构化输出** - 提供详细的思考过程和高质量答案
- **可配置选项** - 自定义子任务数量、启用/禁用审查、控制详细度
- **质量保证** - 可选的自我审查机制，提供改进建议

### 技术亮点

- 🏗️ **模块化架构** - 遵循 SOLID 原则的深度思考系统，职责分离
- 🔌 **易于扩展** - 工厂模式设计，新增提供商只需3步
- 🌐 **Web 搜索集成** - 基于 DuckDuckGo，无需 API 密钥（可选功能）
- 🛡️ **健壮的容错** - 多重 JSON 解析策略、自动降级处理
- 📊 **详细的日志** - 完整的执行过程追踪和 LLM 调用统计
- 🚦 **自动端口管理** - 智能检测并使用可用端口
- 💾 **缓存支持** - 中间结果缓存，减少重复计算

## 支持的提供商和模型

### Cerebras (10 个模型)

- `llama-3.3-70b`
- `llama-3.1-8b`
- `llama-3.1-70b`
- `llama-3.2-3b`
- `llama-3.2-1b`
- `qwen-3-235b-a22b-instruct-2507` (默认)
- `qwen-3-235b-a22b-thinking-2507`
- `zai-glm-4.6`
- `gpt-oss-120b`
- `qwen-3-32b`

### DeepSeek (3 个模型)

- `deepseek-chat`
- `deepseek-coder`
- `deepseek-reasoner`

### OpenAI (4 个模型)

- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### DashScope（阿里云百炼）(11 个模型)

- `qwen-max`
- `qwen-plus`
- `qwen-turbo`
- `qwen-long`
- `qwen-vl-max`
- `qwen-vl-plus`
- `qwen-audio-turbo`
- `qwen2-7b-instruct`
- `qwen2-72b-instruct`
- `qwen2-1.5b-instruct`
- `qwen2-57b-a14b-instruct`

### Kimi（月之暗面）(7 个模型)

- `moonshot-v1-8k` (8K 上下文)
- `moonshot-v1-32k` (32K 上下文)
- `moonshot-v1-128k` (128K 上下文)
- `kimi-k2-0905-preview` (256K 上下文，最新版本)
- `kimi-k2-turbo-preview` (高速版本，60-100 Tokens/s)
- `kimi-k2-thinking` (长思考模型，256K 上下文)
- `kimi-k2-thinking-turbo` (长思考高速版本)

## 安装和运行

### 1. 克隆项目

```bash
git clone https://github.com/LogicShao/SimpleLLMFrontend.git
cd SimpleLLMFront
```

### 2. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# （可选）安装网络搜索功能
pip install duckduckgo-search
```

**注意**: `duckduckgo-search` 是可选依赖，用于支持深度思考模式的网络搜索功能。如不需要此功能，可跳过安装。

### 3. 配置API密钥

在运行应用之前，您需要配置至少一个AI提供商的API密钥。推荐使用 `.env` 文件方式：

#### 方法一：使用.env文件（推荐）

```bash
# 复制示例文件
cp .env.example .env

# 编辑.env文件，填入您的API密钥
# 在Windows上可以使用记事本或其他编辑器编辑
```

编辑 `.env` 文件，将相应的API密钥替换为您的真实API密钥：

```env
# Cerebras API密钥（从 https://cloud.cerebras.ai/ 获取）
CEREBRAS_API_KEY=your_cerebras_api_key_here

# DeepSeek API密钥（从 https://platform.deepseek.com/ 获取）
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# OpenAI API密钥（从 https://platform.openai.com/ 获取）
OPENAI_API_KEY=your_openai_api_key_here
```

#### 方法二：设置环境变量

##### Windows (命令提示符)

```cmd
set CEREBRAS_API_KEY=your_api_key_here
set DEEPSEEK_API_KEY=your_api_key_here
set OPENAI_API_KEY=your_api_key_here
set DASHSCOPE_API_KEY=your_api_key_here
```

##### Windows (PowerShell)

```powershell
$env:CEREBRAS_API_KEY="your_api_key_here"
$env:DEEPSEEK_API_KEY="your_api_key_here"
$env:OPENAI_API_KEY="your_api_key_here"
$env:DASHSCOPE_API_KEY="your_api_key_here"
```

##### Linux/Mac

```bash
export CEREBRAS_API_KEY=your_api_key_here
export DEEPSEEK_API_KEY=your_api_key_here
export OPENAI_API_KEY=your_api_key_here
export DASHSCOPE_API_KEY=your_api_key_here
```

### 4. 运行应用

```bash
python main.py
```

应用将在 `http://localhost:7860` 启动，并自动在默认浏览器中打开。

## 📖 使用说明

### 基础对话模式

1. **配置 API 密钥**：确保已正确设置至少一个提供商的 API 密钥
2. **选择提供商**：从左侧面板的"选择提供商"下拉菜单中选择
3. **选择模型**：根据提供商自动显示可用模型列表
4. **开始对话**：在输入框中输入问题，点击"🚀 发送"或按 Enter 键
5. **查看历史**：所有对话历史都会保存在聊天界面中
6. **导出对话**：点击"📥 导出对话"按钮保存对话记录
7. **清除对话**：点击"🗑️ 清除对话"按钮重置对话历史

### 🧠 深度思考模式

**适用场景**：

- ✅ 复杂分析问题（如"分析某公司的商业模式优劣势"）
- ✅ 多角度综合问题（如"从经济、社会、技术角度分析某现象"）
- ✅ 设计规划问题（如"设计一个在线教育平台"）
- ✅ 深度研究问题（如"量子计算的发展现状和未来趋势"）

**使用步骤**：

1. **启用深度思考**
    - 在左侧控制面板找到 **"🧠 深度思考模式"** 区域
    - 勾选 **"启用深度思考"** 复选框

2. **配置选项**（可选）
    - 点击 **"高级选项"** 展开配置面板
    - **启用自我审查**：对最终答案进行质量检查（推荐）
    - **显示思考过程**：展示详细的推理步骤
    - **最大子任务数**：调整问题拆解的粒度（3-8，默认 6）

3. **提问并等待**
    - 输入您的复杂问题
    - 系统将自动执行：规划 → 分析 → 整合 → 审查
    - 等待时间约 30-180 秒（取决于模型速度和配置）

4. **查看结果**
    - **💡 深度思考结果**：结构化的最终答案
    - **🧠 思考过程摘要**：问题拆解和各阶段分析
    - **🔍 质量审查**：发现的问题和改进建议（如启用）
    - **统计信息**：LLM 调用次数、各子任务置信度

**配置建议**：

| 场景    | 模型推荐                             | 子任务数 | 启用审查 | 预计时间     |
|-------|----------------------------------|------|------|----------|
| 快速探索  | `llama-3.3-70b`                  | 3-4  | ❌    | 30-60s   |
| 深度分析  | `qwen-3-235b-a22b-thinking-2507` | 5-6  | ✅    | 60-120s  |
| 专业级输出 | `gpt-4o`                         | 6-8  | ✅    | 120-180s |

**示例问题**：

```
问题：请从技术架构、用户体验和商业模式三个角度，
     深入分析抖音和快手的差异与竞争策略。

深度思考模式将自动：
1. 规划：拆解为技术、UX、商业三个分析维度
2. 分析：逐个深入研究每个维度
3. 整合：综合三个维度生成连贯答案
4. 审查：检查答案质量并提供改进建议
```

**性能参考**：

- **LLM 调用次数**：5-9 次（1 规划 + N 分析 + 1 整合 + 1 审查）
- **Token 消耗**：约 12,000 tokens/次
- **成本估算**：< $0.01/次（基于 Cerebras）

详细文档请参考：

- 📘 [深度思考功能完整文档](doc/deep_thinking_feature.md)
- 🚀 [快速开始指南](doc/deep_thinking_quickstart.md)
- 🌐 [网络搜索功能文档](doc/web_search_feature.md) ← **NEW!**

## 🖥️ 界面说明

### 左侧控制面板

- **🏢 选择提供商**：选择 AI 服务提供商（Cerebras、DeepSeek、OpenAI、DashScope）
- **🤖 选择模型**：根据提供商自动显示可用模型
- **📊 系统状态**：实时显示可用提供商和对话轮数
- **⚙️ 模型参数**：
    - 📝 System Instruction（系统提示词）
    - 🌡️ Temperature（温度）
    - 🔧 高级参数（Top P、Max Tokens、频率/存在惩罚）
- **🧠 深度思考模式**：
    - 启用深度思考开关
    - 高级选项（审查、思考过程、子任务数）
- **💡 功能提示**：快速参考指南

### 右侧聊天区域

- **💬 对话界面**：显示对话历史，支持复制每条消息
- **✍️ 输入消息**：输入您的问题（支持多行输入）
- **🚀 发送按钮**：提交问题
- **🗑️ 清除对话**：重置对话历史
- **📥 导出对话**：保存对话记录

## 故障排除

### 常见问题

1. **API密钥未设置**
    - 错误信息："没有配置任何有效的API密钥"
    - 解决方案：创建 `.env` 文件并填入至少一个提供商的API密钥

2. **提供商不可用**
    - 错误信息："提供商 'xxx' 未配置或不可用"
    - 解决方案：检查对应提供商的API密钥是否正确配置

3. **API调用失败**
    - 错误信息："xxx API调用失败: ..."
    - 解决方案：检查API密钥是否正确，网络连接是否正常

4. **端口被占用**
    - 错误信息："Address already in use"
    - 解决方案：修改 `main.py` 中的 `server_port` 参数

## 🧪 测试

### 运行测试

```bash
# 测试 UI 组件
python tests/test_ui.py

# 测试端口查找功能
python tests/test_port_finder.py

# 测试模型选择器
python tests/test_model_selector.py

# 测试深度思考模块
python tests/test_deep_think.py

# 运行特定的深度思考测试
python tests/test_deep_think.py --test basic      # 基础功能测试
python tests/test_deep_think.py --test no-review  # 无审查模式测试
python tests/test_deep_think.py --test format     # 输出格式化测试
```

### 语法验证

```bash
# 验证所有源文件语法
python -m py_compile main.py src/*.py
```

## 📁 项目结构

```
SimpleLLMFront/
├── src/                          # 源代码模块
│   ├── __init__.py               # 包标识
│   ├── CLAUDE.md                 # 模块级 AI 指引
│   ├── api_service.py            # 多提供商 API 编排（单例模式）
│   ├── chat_manager.py           # 对话历史管理
│   ├── config.py                 # 配置、提供商/模型映射、端口工具
│   ├── providers.py              # 提供商实现（工厂模式）
│   ├── event_handlers.py         # 事件处理器
│   ├── ui_client.py              # UI 客户端总协调器
│   ├── ui_composer.py            # UI 布局构建器
│   ├── response_handlers.py      # 响应处理器
│   ├── logging.py                # 日志配置
│   └── deep_think/               # 深度思考系统（模块化架构）
│       ├── __init__.py           # 向后兼容接口
│       ├── core/                 # 核心接口和模型
│       │   ├── __init__.py
│       │   ├── interfaces.py    # 抽象基类和接口定义
│       │   └── models.py        # 数据模型定义
│       ├── stages/               # 阶段处理器
│       │   ├── __init__.py
│       │   ├── base.py          # 阶段基类
│       │   ├── planner.py       # Plan 阶段
│       │   ├── solver.py        # Solve 阶段
│       │   ├── synthesizer.py   # Synthesize 阶段
│       │   └── reviewer.py      # Review 阶段
│       ├── prompts/              # 提示模板系统
│       │   ├── __init__.py
│       │   ├── base.py          # 模板基类
│       │   ├── templates.py     # 具体模板实现
│       │   └── manager.py       # 模板管理器
│       ├── orchestrator.py       # 深度思考编排器
│       ├── formatter.py         # 结果格式化工具
│       └── utils.py             # 工具函数
├── main.py                       # Gradio UI 和应用入口
├── tests/                        # 测试脚本
│   ├── __pycache__/
│   ├── test_ui.py                # UI 组件测试
│   ├── test_port_finder.py       # 端口管理测试
│   ├── test_model_selector.py    # 模型选择器测试
│   ├── test_deep_think.py        # 深度思考模块测试
│   ├── test_deepseek_fix.py      # DeepSeek 修复测试
│   └── test_web_search.py        # 网络搜索功能测试
├── doc/                          # 功能文档
│   ├── QUICKSTART.md             # 快速开始
│   ├── CHEATSHEET.md             # 快速参考
│   ├── UV_RUFF_GUIDE.md          # UV 和 Ruff 使用指南
│   ├── deep_thinking_feature.md  # 深度思考完整文档
│   ├── deep_thinking_quickstart.md # 深度思考快速开始
│   ├── web_search_feature.md     # 网络搜索功能文档
│   ├── parameter_control_feature.md # 参数控制功能文档
│   ├── performance_optimization_guide.md # 性能优化指南
│   ├── logging_guide.md          # 日志系统指南
│   └── UI_RESTRUCTURE.md         # UI 重构说明
├── logs/                         # 日志文件目录
├── assets/                       # 静态资源
├── scripts/                      # 脚本文件
├── .venv/                        # 虚拟环境（gitignore）
├── .claude/                      # AI 上下文索引（gitignore）
├── .pytest_cache/                # 测试缓存（gitignore）
├── .idea/                        # IDE 配置（gitignore）
├── __pycache__/                  # Python 缓存（gitignore）
├── .env                          # API 密钥配置（gitignored）
├── .env.example                  # 环境变量示例
├── requirements.txt              # 依赖列表
├── pyproject.toml                # 项目配置（UV）
├── uv.lock                       # UV 依赖锁定文件
├── Makefile                      # Makefile 任务自动化
└── README.md                     # 本文件
```

### 核心模块说明

- **主应用**：`main.py` - 应用启动入口和初始化
- **UI 客户端**：`src/ui_client.py` - 总协调器，组合 UIComposer、EventHandlers、ResponseHandlers
- **UI 构建器**：`src/ui_composer.py` - 纯 UI 布局构建器
- **事件处理器**：`src/event_handlers.py` - 用户交互事件处理
- **响应处理器**：`src/response_handlers.py` - 标准响应和深度思考响应处理
- **API 服务**：`src/api_service.py` - 多提供商编排（全局单例）
- **提供商管理**：`src/providers.py` - 抽象基类和 5 个具体实现
- **配置管理**：`src/config.py` - 提供商配置、模型映射、端口工具
- **对话管理**：`src/chat_manager.py` - 历史记录和消息处理
- **深度思考**：`src/deep_think/` - 模块化深度思考系统
- **依赖管理**：`requirements.txt` / `pyproject.toml` / `uv.lock`
- **环境配置**：`.env` 文件（使用 python-dotenv）

## 🛠️ 技术栈

- **前端框架**：Gradio 4.x
- **后端 SDK**：
    - Cerebras Cloud SDK
    - OpenAI SDK（用于 DeepSeek、OpenAI、DashScope）
- **架构模式**：
    - 工厂模式（Provider Factory）
    - 单例模式（API Service）
    - 策略模式（Deep Thinking Orchestrator）
- **数据结构**：Python dataclass
- **环境管理**：python-dotenv
- **日志系统**：Python logging
- **Python 版本**：3.8+

## 🌟 核心架构

### 提供商架构

```python
BaseProvider(抽象基类)
↓
├── CerebrasProvider  # Cerebras Cloud SDK
├── DeepSeekProvider  # OpenAI SDK + DeepSeek endpoint
├── OpenAIProvider  # OpenAI SDK
└── DashScopeProvider  # OpenAI SDK + 阿里云 endpoint
```

### 深度思考流程

```
用户问题
    ↓
DeepThinkOrchestrator
    ↓
Plan (规划) → Solve (分析) → Synthesize (整合) → Review (审查)
    ↓                 ↓                 ↓              ↓
  拆解子任务      逐个深入分析      整合所有结论    质量检查
    ↓
格式化输出 → 用户
```

## 🔮 未来规划

### 短期计划

- [ ] 添加流式输出支持（实时显示思考过程）
- [ ] 支持对话中途切换深度思考模式
- [ ] 优化深度思考的 Prompt 模板
- [ ] 添加更多预设的深度思考场景

### 中期计划

- [ ] 集成外部工具（搜索引擎、RAG、代码执行）
- [ ] 实现异步执行提升性能
- [ ] 添加思考过程可视化（流程图）
- [ ] 支持自定义 Prompt 模板

### 长期计划

- [ ] 多模态支持（图片、文档分析）
- [ ] 对话式深度思考（中途用户介入）
- [ ] 思考过程缓存和复用
- [ ] 分布式深度思考（多模型协作）

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码风格

- 遵循 PEP 8 规范
- 使用类型注解
- 编写清晰的文档字符串
- 添加必要的测试

## 📄 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/LogicShao/SimpleLLMFrontend/issues)
- **文档**: [完整文档](doc/)
- **快速开始**: [深度思考快速指南](doc/deep_thinking_quickstart.md)

## 🙏 致谢

感谢以下 AI 提供商的支持：

- [Cerebras](https://cloud.cerebras.ai/) - 超快推理速度
- [DeepSeek](https://platform.deepseek.com/) - 强大的中文能力
- [OpenAI](https://platform.openai.com/) - 业界领先的 GPT 系列
- [DashScope (阿里云百炼)](https://dashscope.aliyuncs.com/) - 通义千问系列模型

---

**⭐ 如果这个项目对您有帮助，请给我们一个 Star！**