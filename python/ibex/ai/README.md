# IBEX AI Module

The IBEX AI module provides unified access to multiple Large Language Model providers including OpenAI, Anthropic Claude, and Ollama.

## Features

- **Multi-Provider Support**: Easy switching between OpenAI, Claude, and Ollama
- **Unified Interface**: Same API regardless of provider
- **Automatic Fallbacks**: Graceful handling when providers are unavailable
- **Configuration Management**: Environment-based configuration
- **Async Support**: Full async/await support for all operations

## Installation

The AI module requires additional dependencies:

```bash
pip install openai anthropic ollama
```

Or install all at once:
```bash
pip install -r requirements.txt
```

## Quick Start

```python
from ibex.ai import AIManager
import asyncio

async def main():
    # Initialize with default provider
    manager = AIManager()

    # Or specify provider and model
    manager = AIManager(provider="claude", model="claude-3-sonnet-20240229")

    # Chat with AI
    messages = [{"role": "user", "content": "Hello, how can you help me with coding?"}]
    response = await manager.chat(messages)
    print(response)

asyncio.run(main())
```

## Providers

### OpenAI GPT

**Setup:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Usage:**
```python
manager = AIManager(provider="openai", model="gpt-4")
```

**Available Models:**
- `gpt-4`
- `gpt-4-turbo-preview`
- `gpt-3.5-turbo`
- `gpt-3.5-turbo-16k`

### Anthropic Claude

**Setup:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Usage:**
```python
manager = AIManager(provider="claude", model="claude-3-sonnet-20240229")
```

**Available Models:**
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-2.1`
- `claude-2.0`

### Ollama (Local)

**Setup:**
1. Install Ollama: https://ollama.ai/
2. Pull models: `ollama pull codellama`

**Usage:**
```python
manager = AIManager(provider="ollama", model="codellama")
```

**Available Models:**
- `codellama` (recommended for coding)
- `llama2`
- `mistral`
- `codellama:7b`
- `codellama:13b`
- `codellama:34b`

## CLI Usage

The AI module integrates with the IBEX CLI:

```bash
# List available providers
ibex ai providers

# Configure AI settings
ibex ai config --provider claude --model claude-3-sonnet-20240229

# Test configuration
ibex ai config --test

# Chat with AI
ibex ai chat "Explain Python decorators"

# List models for a provider
ibex ai models openai
```

## Advanced Usage

### Custom Prompts

```python
from ibex.ai.utils import create_commit_message_prompt

# Create a commit message prompt
changes = [
    {"summary": "Added user authentication"},
    {"summary": "Implemented JWT tokens"}
]
intent = "Security improvements"

messages = create_commit_message_prompt(changes, intent)
response = await manager.chat(messages)
```

### Code Review

```python
from ibex.ai.utils import create_code_review_prompt

code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
"""

messages = create_code_review_prompt(code, "Recursive factorial function")
review = await manager.chat(messages)
```

### Provider Management

```python
# Check available providers
providers = manager.list_providers()
print("Available:", providers)

# Validate configuration
valid, message = manager.validate_config()
if not valid:
    print(f"Configuration issue: {message}")
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `IBEX_AI_PROVIDER` | Default AI provider | No |
| `OPENAI_API_KEY` | OpenAI API key | For OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic API key | For Claude |
| `OPENAI_MODEL` | Default OpenAI model | No |
| `ANTHROPIC_MODEL` | Default Claude model | No |
| `OLLAMA_MODEL` | Default Ollama model | No |

## Error Handling

The AI module provides comprehensive error handling:

```python
try:
    response = await manager.chat(messages)
except ImportError as e:
    print(f"Provider not installed: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
except RuntimeError as e:
    print(f"API error: {e}")
```

## Examples

See `example.py` for complete usage examples including:
- Basic chat with all providers
- Commit message generation
- Code review
- Error handling

## Architecture

```
ibex/ai/
├── __init__.py          # Main AIManager class
├── providers/           # Provider implementations
│   ├── __init__.py
│   ├── base_provider.py # Abstract base class
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   └── ollama_provider.py
├── utils.py             # Utility functions
├── example.py           # Usage examples
└── README.md            # This file
```

## Contributing

To add a new provider:

1. Create a new provider class inheriting from `BaseProvider`
2. Implement the required methods
3. Add it to the `AIManager._setup_provider()` method
4. Update the requirements.txt if needed
5. Add documentation and examples

## License

This module is part of the IBEX project and follows the same license terms.
