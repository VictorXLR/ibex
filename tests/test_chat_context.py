#!/usr/bin/env python3
"""
Test script to verify what context the AI model receives during chat
"""

import asyncio
import sys
from pathlib import Path

# Add the python directory to the path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from ibex.ai import AIManager

async def test_chat_context():
    """Test what context is provided to the AI during chat"""

    print("🔍 Testing AI Chat Context Gathering")
    print("=" * 50)

    try:
        # Initialize AI manager
        ai_manager = AIManager()

        if not ai_manager.is_available():
            print("❌ AI not available - please configure a provider first")
            return

        print(f"✅ AI Provider: {ai_manager.provider}")
        print(f"✅ AI Model: {ai_manager.model}")
        print()

        # Test different types of queries to see what context is gathered
        test_queries = [
            "What is this project about?",
            "Show me the main code structure",
            "How does the AI functionality work?",
            "What are the configuration options?",
            "Can you help me with the git integration?"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n🧪 Test {i}: '{query}'")
            print("-" * 30)

            # Get the context that would be provided
            context = await ai_manager._get_relevant_context(query)

            print("📋 Context provided to AI:")
            print(context)
            print()

            # Show context length
            context_lines = context.split('\n')
            print(f"📊 Context Statistics:")
            print(f"  - Total lines: {len(context_lines)}")
            print(f"  - Character count: {len(context)}")
            print()

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_context())
