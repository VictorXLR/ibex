# IBEX Examples

This directory contains example code demonstrating IBEX usage patterns and AI integration.

## Examples

### `ai_usage_example.py`
Demonstrates how to use the IBEX AI module programmatically.

**Topics Covered:**
- AIManager initialization
- Provider configuration
- Chat completion calls
- Context-aware interactions
- File access from AI
- Error handling

**Usage:**
```bash
# Set up API keys (if using OpenAI or Claude)
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Run the example
python examples/ai_usage_example.py
```

## Example Patterns

### Basic AI Usage

```python
from ibex.ai import AIManager

# Initialize with Ollama (local)
ai = AIManager(provider='ollama', model='llama2')

# Chat completion
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain IBEX in one sentence."}
]
response = await ai.chat(messages)
print(response)
```

### Using with Configuration

```python
from ibex.ai import AIManager, ConfigManager

# Load from project config
config_manager = ConfigManager(project_root='.')
ai = AIManager(config_manager=config_manager)

# Use default provider from config
response = await ai.chat(messages)
```

### LLM Change Analysis

```python
from ibex.llm import LLMManager

# Initialize
llm = LLMManager('.', provider='ollama')

# Analyze changes
changes = [
    {"file": "auth.py", "hash": "abc123"}
]
analysis = await llm.analyze_changes(changes, "Add user authentication")
print(analysis)

# Store in database
llm.store_semantic_change(
    "commit_hash",
    analysis,
    changes,
    "Add user authentication"
)

# Retrieve history
history = llm.get_semantic_history()
for entry in history:
    print(f"{entry['timestamp']}: {entry['description']}")
```

### File Watching

```python
from ibex.core import IbexWatcher

# Start watching
watcher = IbexWatcher('.', intent="Implement dashboard")
watcher.start()

# Detect changes
count = watcher.detect_current_changes()
print(f"Detected {count} changes")

# Create stake
await watcher.create_stake("checkpoint-1", "Initial implementation")

# Stop watching
watcher.stop()
```

## More Examples

For more examples, see:
- [TESTING.md](../TESTING.md) - Test examples showing various usage patterns
- [STRUCTURE.md](../STRUCTURE.md) - Architecture and code organization
- [README.md](../README.md) - Main documentation

## Contributing Examples

If you have useful example code to share:

1. Create a new `.py` file in this directory
2. Add clear comments and docstrings
3. Update this README
4. Submit a pull request

Make sure examples:
- Are self-contained
- Include error handling
- Document prerequisites
- Show best practices
