#!/usr/bin/env python3
"""
Simple test for Ollama qwen3-coder:30b model
"""

import asyncio
import sys
from pathlib import Path

# Add the python directory to the path
project_root = Path(__file__).parent
python_dir = project_root / "python"
sys.path.insert(0, str(python_dir))

async def simple_test():
    """Simple test of Ollama with qwen3-coder:30b"""
    try:
        from ibex.ai.providers.ollama_provider import OllamaProvider

        print("🔧 Testing Ollama qwen3-coder:30b...")

        # Create provider
        provider = OllamaProvider("qwen3-coder:30b")

        # Check availability
        if not provider.is_available():
            print("❌ Ollama not available")
            return

        print("✅ Ollama available")

        # Test chat
        messages = [
            {"role": "system", "content": "You are a coding assistant using the qwen3-coder model."},
            {"role": "user", "content": "Hello! Please confirm you are the qwen3-coder:30b model and tell me what programming languages you specialize in."}
        ]

        print("⏳ Sending request (this may take a moment)...")
        response = await provider.chat_completion(messages)

        print("\n🎯 Response from qwen3-coder:30b:")
        print("-" * 50)
        print(response)
        print("-" * 50)

        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
