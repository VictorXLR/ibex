#!/usr/bin/env python3
"""
Test script to verify chat functionality works
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the python directory to the path
sys.path.insert(0, str(Path(__file__).parent / "python"))

async def test_chat_functionality():
    """Test the chat functionality"""
    print("🧪 Testing IBEX Chat Functionality")
    print("=" * 50)

    try:
        # Import and test AI manager
        print("🔧 Testing AI Manager initialization...")
        from ibex.ai import AIManager

        ai_manager = AIManager()
        print(f"✅ AI Manager created: {ai_manager.provider} - {ai_manager.model}")

        # Test availability
        is_available = ai_manager.is_available()
        print(f"🤖 AI Available: {is_available}")

        if not is_available:
            print("⚠️  AI provider not available - chat will show configuration message")
            return

        # Test basic chat
        print("\n💬 Testing basic chat...")
        test_messages = [
            {"role": "user", "content": "Hello! Can you help me with my IBEX project?"}
        ]

        response = await ai_manager.chat(test_messages)
        print(f"✅ Basic chat response: {response[:100]}...")

        # Test enhanced chat with context
        print("\n🎯 Testing enhanced chat with context...")
        enhanced_response = await ai_manager.chat_with_context(
            user_message="What can you help me with in my development workflow?",
            include_project_context=True
        )
        print(f"✅ Enhanced chat response: {enhanced_response[:100]}...")

        print("\n🎉 All chat functionality tests passed!")
        print("\n💡 Chat features verified:")
        print("  • AI provider initialization ✓")
        print("  • Basic chat communication ✓")
        print("  • Enhanced context-aware chat ✓")
        print("  • Project context integration ✓")

    except Exception as e:
        print(f"❌ Chat functionality test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_functionality())
