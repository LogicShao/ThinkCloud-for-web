# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A multi-provider LLM chat client built with Gradio supporting Cerebras, DeepSeek, OpenAI, and DashScope (Alibaba Cloud).
Features a clean Gradio interface with intelligent model selection, automatic port management, and **Deep Thinking Mode
** for complex multi-stage reasoning.

## Project Structure

```
SimpleLLMFront/
├── src/                    # Source modules
│   ├── api_service.py      # Multi-provider API orchestration (singleton pattern)
│   ├── chat_manager.py     # Conversation history management
│   ├── config.py           # Configuration, provider/model mappings, port utilities
│   ├── providers.py        # Provider implementations (factory pattern)
│   └── deep_think.py       # Deep thinking orchestrator for multi-stage reasoning
├── main.py                 # Gradio UI and application entry point
├── tests/                  # Test scripts
│   ├── test_ui.py          # UI component tests
│   ├── test_port_finder.py # Port management tests
│   ├── test_model_selector.py # Model selector tests
│   └── test_deep_think.py  # Deep thinking module tests
├── doc/                    # Feature documentation
│   └── deep_thinking_feature.md # Deep thinking mode documentation
└── .env                    # API keys (gitignored)
```

**Import Convention**: All imports in `main.py` use `src.` prefix (e.g., `from src.config import ...`).

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys (at least one required)
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application
```bash
# Start the Gradio web interface (auto port detection)
python main.py

# The app automatically finds available ports starting from 7860
# Opens in browser at http://localhost:<port>
```

### Testing
```bash
# Test UI components
python tests/test_ui.py

# Test port finder functionality
python tests/test_port_finder.py

# Test model selector with provider info
python tests/test_model_selector.py

# Test deep thinking module
python tests/test_deep_think.py
python tests/test_deep_think.py --test basic      # Basic functionality test
python tests/test_deep_think.py --test no-review  # Test without review mode
python tests/test_deep_think.py --test format     # Test output formatting

# Syntax validation (all source files)
python -m py_compile main.py src/*.py
```

## Architecture

### Core Components

- **MultiProviderAPIService** (`src/api_service.py`): Singleton service managing multiple AI providers. Routes requests
  based on model selection and initializes all available providers on startup.

- **DeepThinkOrchestrator** (`src/deep_think.py`): Multi-stage reasoning orchestrator that breaks down complex questions
  into subtasks, analyzes each systematically, synthesizes results, and optionally reviews the final answer. Supports
  configurable depth (3-8 subtasks) and optional quality review.

- **Provider Factory Pattern** (`src/providers.py`): Abstract `BaseProvider` class with concrete implementations:
    - `CerebrasProvider`: Uses Cerebras Cloud SDK
    - `DeepSeekProvider`: OpenAI SDK with DeepSeek endpoint
    - `OpenAIProvider`: Standard OpenAI SDK
    - `DashScopeProvider`: OpenAI SDK with Alibaba Cloud endpoint

- **Configuration** (`src/config.py`): Centralized configuration including:
    - Provider settings and API keys (loaded from `.env` via python-dotenv)
    - Model-to-provider mapping (`PROVIDER_MODELS` - 28+ models across 4 providers)
    - Port management utilities (`get_server_port()`, `is_port_available()`)
    - Provider display name mapping (`PROVIDER_DISPLAY_NAMES`)

- **Chat Manager** (`src/chat_manager.py`):
    - `ChatManager`: Maintains conversation history in memory
    - `MessageProcessor`: Converts between Gradio and API message formats (currently transparent as both use same
      format)

- **Gradio Interface** (`main.py`): Clean UI with:
    - Two-level selection: Provider dropdown → Model dropdown
    - Real-time provider status display
    - Message history with copy buttons
    - Export conversation functionality
  - Deep thinking mode controls:
      - Enable/disable deep thinking
      - Toggle self-review
      - Show/hide thinking process
      - Adjust max subtasks (3-8)

### Model Selection Flow

```
User selects provider "Cerebras" in dropdown
       ↓
update_models() triggered → fetches PROVIDER_MODELS["cerebras"]
       ↓
Model dropdown updates with cerebras models
       ↓
User selects model "llama-3.3-70b"
       ↓
get_model_provider("llama-3.3-70b") → identifies "cerebras"
       ↓
MultiProviderAPIService routes to CerebrasProvider
       ↓
API call with model="llama-3.3-70b"
```

**Key Flow**: Provider selection updates available models via `update_models()` in event handlers. The
`get_model_provider()` function reverse-maps models to providers for API routing.

### Port Management

The application automatically finds available ports to avoid conflicts:

- **Default**: 7860
- **Fallback Range**: 7861-7959 (scans sequentially)
- **Final Fallback**: System-assigned random port (port=None)

**Key Functions** (`src/config.py`):

- `is_port_available(port)`: Check if a port is free
- `find_available_port(start_port)`: Scan for next available port
- `get_server_port(start_port, host)`: Main entry point used by `main.py`

### Message Format

Both Gradio and all provider APIs use the standard OpenAI message format:

```python
{"role": "user|assistant", "content": "..."}
```

The `MessageProcessor` class exists for potential future format conversions but currently passes messages through
transparently.

## Configuration

### Environment Variables (.env)

At least one provider API key must be set:

```env
CEREBRAS_API_KEY=csk-...        # https://cloud.cerebras.ai/
DEEPSEEK_API_KEY=sk-...         # https://platform.deepseek.com/
OPENAI_API_KEY=sk-...           # https://platform.openai.com/
DASHSCOPE_API_KEY=sk-...        # https://dashscope.aliyuncs.com/
```

### Provider Configuration

Located in `src/config.py`:

- `PROVIDER_CONFIG`: API keys, base URLs, enabled status for each provider
- `PROVIDER_MODELS`: Model lists per provider (10 Cerebras, 3 DeepSeek, 4 OpenAI, 11 DashScope)
- `PROVIDER_DISPLAY_NAMES`: UI display names mapping
- `DEFAULT_MODEL`: "qwen-3-235b-a22b-thinking-2507"
- `DEFAULT_PROVIDER`: "cerebras"

## Adding New Providers

Follow these steps to add a new AI provider:

1. **Create provider class** in `src/providers.py`:
   ```python
   class NewProvider(BaseProvider):
       def _initialize_client(self):
           # Initialize SDK client
           pass

       def is_available(self) -> bool:
           # Check if API key is configured
           return self.client is not None

       def chat_completion(self, messages, model) -> str:
           # Call provider API and return response
           pass
   ```

2. **Register in ProviderFactory** (`src/providers.py`):
   ```python
   _providers = {
       "newprovider": NewProvider,
       # ... existing providers
   }
   ```

3. **Add configuration** (`src/config.py`):
   ```python
   PROVIDER_CONFIG["newprovider"] = {
       "api_key": os.environ.get("NEWPROVIDER_API_KEY"),
       "base_url": "https://api.newprovider.com/v1",
       "enabled": True
   }

   PROVIDER_MODELS["newprovider"] = ["model-1", "model-2"]

   PROVIDER_DISPLAY_NAMES["newprovider"] = "NewProvider"
   ```

4. **Set environment variable**: Add `NEWPROVIDER_API_KEY` to `.env` file

## Error Handling

The application provides clear error messages for common issues:

- **Missing API keys**: Identifies which provider needs configuration with specific env var name
- **Failed API calls**: Returns descriptive error strings displayed directly in chat interface
- **Port conflicts**: Automatically scans for alternative ports with console notifications
- **Provider unavailability**: Gracefully handled with status indicators in UI

All errors are logged to console and displayed to users in a user-friendly format.

## Deep Thinking Mode

The application includes a sophisticated deep thinking system for complex problem-solving:

### Features

1. **Four-Stage Reasoning Pipeline**:
    - **Plan**: Clarifies question and breaks it into 3-8 subtasks
    - **Solve**: Analyzes each subtask with context from previous results
    - **Synthesize**: Integrates all conclusions into a coherent answer
    - **Review** (optional): Self-critiques the final answer for quality

2. **Configurable Options**:
    - Enable/disable deep thinking mode
    - Toggle quality review stage
    - Show/hide detailed thinking process
    - Adjust maximum subtasks (3-8)

3. **Structured Data Models** (using dataclasses):
    - `Plan`: Clarified question, subtasks, reasoning approach
    - `SubtaskResult`: Analysis, conclusion, confidence, limitations
    - `DeepThinkResult`: Complete thinking session with all stages
    - `ReviewResult`: Quality assessment and improvement suggestions

### Usage

**Via UI**:

1. Check "启用深度思考" (Enable Deep Thinking) in left panel
2. Optionally adjust settings in "高级选项" (Advanced Options) accordion
3. Ask your question as usual

**Via Code**:

```python
from src.deep_think import DeepThinkOrchestrator, format_deep_think_result

orchestrator = DeepThinkOrchestrator(
    api_service=api_service,
    model="qwen-3-235b-a22b-thinking-2507",
    max_subtasks=6,
    enable_review=True
)

result = orchestrator.run("Your complex question here")
formatted = format_deep_think_result(result, include_process=True)
```

### When to Use

**Recommended for**:

- Complex analytical questions requiring multiple perspectives
- Problems needing structured breakdown (e.g., "design a system for X")
- Research-oriented questions
- Multi-faceted comparisons or evaluations

**Not recommended for**:

- Simple factual queries
- Quick yes/no questions
- Creative writing tasks (poetry, stories)

### Performance

- **LLM Calls**: 5-9 calls per deep thinking session (1 plan + N solve + 1 synthesize + 1 review)
- **Response Time**: 30-180 seconds depending on model speed
- **Cost**: ~12,000 tokens per session (varies by question complexity)

### Extensibility

The system includes extension points for future tool integration:

- `SubtaskResult.needs_external_info`: Flag for external data needs
- `SubtaskResult.suggested_tools`: Recommended tools (search, RAG, code execution)

See `doc/deep_thinking_feature.md` for comprehensive documentation.

All errors are logged to console and displayed to users in a user-friendly format.

## Important Implementation Details

### Singleton Pattern

`api_service` in `src/api_service.py` is a **global singleton instance**. Do not create multiple
`MultiProviderAPIService` instances. Always import and use the existing instance:
```python
from src.api_service import api_service
```

### Provider Initialization

Providers are initialized once during `MultiProviderAPIService.__init__()`. The service prints status messages to
console:

- `[SUCCESS]` indicates provider is ready
- `[FAILED]` indicates missing API key or initialization error

### Event Handler Pattern

Gradio event handlers in `main.py` use a two-step pattern for chat:

1. `user_message()`: Adds user input to history, returns updated chatbot
2. `bot_message()`: Calls API and appends assistant response
3. `update_status()`: Refreshes provider status display

This separation allows proper UI updates between user input and bot response.

### Test Scripts

All test scripts in `tests/` are standalone and can be run independently. They do not require a running application
instance.
