#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the python directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

async def test_chat():
    try:
        print("Testing AI Manager import...")
        from python.ibex.ai import AIManager
        
        print("Creating AI Manager...")
        ai = AIManager()
        print(f"✓ AI Manager created successfully")
        print(f"  Provider: {ai.provider}")
        print(f"  Model: {ai.model}")
        print(f"  Project root: {ai.project_root}")
        
        print("\nTesting availability...")
        available = ai.is_available()
        print(f"  Available: {available}")
        
        if not available:
            print("❌ AI not available - cannot test chat")
            return
        
        print("\nTesting basic chat...")
        messages = [{"role": "user", "content": "Say 'Hello from test!'"}]
        response = await ai.chat(messages)
        print(f"✓ Basic chat successful: {response}")
        
        print("\nTesting chat_with_context...")
        response = await ai.chat_with_context(
            user_message="What can you help me with?",
            include_project_context=True
        )
        print(f"✓ Enhanced chat successful: {response[:100]}...")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())
