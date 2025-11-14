# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A multi-provider LLM chat client built with Gradio supporting Cerebras, DeepSeek, OpenAI, and DashScope (Alibaba Cloud).
Features a modern dark-themed UI with intelligent model selection and automatic port management.

## Project Structure

```
SimpleLLMFront/
├── src/                    # Source modules (NEW: reorganized structure)
│   ├── api_service.py      # Multi-provider API orchestration
│   ├── chat_manager.py     # Conversation history management
│   ├── config.py           # Configuration and utilities
│   └── providers.py        # Provider implementations (factory pattern)
├── main.py                 # Gradio UI and application entry point
├── tests/                  # Test scripts
│   ├── test_ui.py          # UI component tests
│   ├── test_port_finder.py # Port management tests
│   └── test_model_selector.py # Model selector tests
├── doc/                    # Feature documentation
└── .env                    # API keys (gitignored)
```

**IMPORTANT**: All imports in `main.py` now use `src.` prefix (e.g., `from src.config import ...`). When modifying code,
maintain this import structure.

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
# Test UI components and theme
python tests/test_ui.py

# Test port finder functionality
python tests/test_port_finder.py

# Test model selector with provider info
python tests/test_model_selector.py

# Syntax validation
python -m py_compile main.py src/*.py
```

## Architecture

### Core Components

- **MultiProviderAPIService** (`src/api_service.py`): Singleton service managing multiple AI providers, routing requests
  based on model selection. Initializes all available providers on startup.

- **Provider Factory Pattern** (`src/providers.py`): Abstract `BaseProvider` class with concrete implementations:
    - `CerebrasProvider`: Uses Cerebras Cloud SDK
    - `DeepSeekProvider`: OpenAI SDK with DeepSeek endpoint
    - `OpenAIProvider`: Standard OpenAI SDK
    - `DashScopeProvider`: OpenAI SDK with Alibaba Cloud endpoint

- **Configuration** (`src/config.py`): Centralized config including:
    - Provider settings and API keys (from `.env`)
    - Model-to-provider mapping (`PROVIDER_MODELS`)
    - Port management utilities (`get_server_port()`, `is_port_available()`)
    - Model display helpers (`get_models_with_provider()`, `extract_model_id()`)

- **Chat Manager** (`src/chat_manager.py`):
    - `ChatManager`: Maintains conversation history
    - `MessageProcessor`: Converts between Gradio and API message formats

- **Gradio Interface** (`main.py`): Dark-themed UI with:
    - Model selector displaying "🔹 Provider | model-name" format
    - Real-time provider status
    - Message history with copy buttons
    - Responsive design with glassmorphism effects

### Model Selection Flow

```
User selects: "🔹 Cerebras | llama-3.3-70b"
       ↓
extract_model_id() → "llama-3.3-70b"
       ↓
get_model_provider() → "cerebras"
       ↓
MultiProviderAPIService routes to CerebrasProvider
       ↓
API call with actual model ID
```

**Key Function**: `extract_model_id()` in `src/config.py` parses display names to extract real model IDs for API calls.

### Port Management

The application automatically finds available ports:

- Default: 7860
- If occupied: scans 7861-7959
- Fallback: system-assigned random port

Functions in `src/config.py`:

- `is_port_available(port)`: Check port availability
- `find_available_port(start_port)`: Find next available port
- `get_server_port()`: Main entry point used by `main.py`

### Message Format Conversion

Two formats are handled:

- **API Format**: `{"role": "user|assistant", "content": "..."}`
- **Gradio Format**: Same structure, used for UI display

`MessageProcessor` handles conversions transparently.

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

- `PROVIDER_CONFIG`: API keys, base URLs, enabled status
- `PROVIDER_MODELS`: Model lists per provider (28+ models total)
- `PROVIDER_DISPLAY_NAMES`: UI display names
- `DEFAULT_MODEL`: "qwen-3-235b-a22b-thinking-2507"

## UI Theme System

Modern dark theme with cyan/blue gradients:

- **Background**: Deep blue gradient (#0f172a → #1e1b4b)
- **Primary**: Cyan-blue gradient (#06b6d4 → #3b82f6)
- **Cards**: Glassmorphism with backdrop blur
- **Text**: Light gray (#e2e8f0, #cbd5e1)

CSS customization in `main.py` `_get_custom_css()` method.

## Adding New Providers

1. Create provider class in `src/providers.py`:

```python
class NewProvider(BaseProvider):
    def _initialize_client(self): ...

    def is_available(self) -> bool: ...

    def chat_completion(self, messages, model) -> str: ...
```

2. Register in `ProviderFactory._providers`:

```python
"newprovider": NewProvider
```

3. Add to `src/config.py`:

```python
PROVIDER_CONFIG["newprovider"] = {...}
PROVIDER_MODELS["newprovider"] = [...]
PROVIDER_DISPLAY_NAMES["newprovider"] = "NewProvider"
```

4. Set environment variable: `NEWPROVIDER_API_KEY`

## Error Handling

- Missing API keys: Clear error messages indicate which provider needs configuration
- Failed API calls: Return descriptive error strings shown in chat
- Port conflicts: Automatic port scanning with user notification
- Provider unavailability: Gracefully handled with status display

## Important Implementation Details

### Model ID Extraction

The UI shows "🔹 Provider | model-name" but APIs need just "model-name". Always use `extract_model_id()` before API
calls.

### Import Structure

After recent refactoring, all shared modules are in `src/` directory. Main imports:

```python
from src.api_service import api_service
from src.chat_manager import ChatManager, MessageProcessor
from src.config import get_models_with_provider, extract_model_id, ...
```

### Singleton Pattern

`api_service` in `src/api_service.py` is a global singleton - don't create multiple instances.

### Test Coverage

All major features have test scripts in `tests/` directory. Run them to verify changes don't break functionality.
