#!/usr/bin/env python3
"""
Debug AI provider initialization
"""

import sys
import os
from pathlib import Path

# Add the python directory to the path
project_root = Path(__file__).parent
python_dir = project_root / "python"
sys.path.insert(0, str(python_dir))

# Set environment variables
os.environ['IBEX_AI_PROVIDER'] = 'ollama'
os.environ['OLLAMA_MODEL'] = 'qwen3-coder:30b'

print("Environment variables:")
print(f"IBEX_AI_PROVIDER: {os.getenv('IBEX_AI_PROVIDER')}")
print(f"OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")

try:
    from ibex.ai import AIManager
    print("\n✅ AIManager import successful")

    print("Creating AIManager with ollama provider...")
    manager = AIManager('ollama', 'qwen3-coder:30b')

    print(f"Provider: {manager.provider}")
    print(f"Model: {manager.model}")
    print(f"Available: {manager.is_available()}")

    if hasattr(manager, '_provider_instance') and manager._provider_instance:
        print(f"Provider instance type: {type(manager._provider_instance)}")
        print(f"Provider instance available: {manager._provider_instance.is_available()}")
    else:
        print("❌ No provider instance created")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
