#!/usr/bin/env python3
"""
Test script for Ollama integration with IBEX
"""

import sys
import os
from pathlib import Path

# Add the python directory to the path
project_root = Path(__file__).parent
python_dir = project_root / "python"
sys.path.insert(0, str(python_dir))

async def test_ollama():
    """Test Ollama integration"""
    try:
        print("🔧 Testing Ollama API connectivity...")

        # Test direct API connectivity first
        import requests
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                print(f"✅ Ollama API connected! Available models: {models}")
            else:
                print(f"❌ Ollama API returned status {response.status_code}")
                return
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to Ollama API: {e}")
            print("💡 Make sure Ollama is running with: ollama serve")
            return

        print("\n🔧 Initializing AI Manager with Ollama...")
        from ibex.ai import AIManager

        manager = AIManager(provider="ollama", model="qwen3-coder:30b")

        print(f"📊 Provider: {manager.provider}")
        print(f"🤖 Model: {manager.model}")
        print(f"✅ Available: {manager.is_available()}")

        if not manager.is_available():
            print("❌ Ollama provider not available")
            return

        print("\n💬 Testing chat functionality...")
        messages = [{"role": "user", "content": "Say 'Hello from qwen3-coder:30b' and confirm you're working with IBEX"}]

        print("⏳ Sending request to Ollama (this may take a moment)...")
        response = await manager.chat(messages)
        print(f"\n🎯 AI Response:\n{response}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ollama())
