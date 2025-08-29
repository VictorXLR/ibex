"""
Example usage of the IBEX AI module
"""

import asyncio
import os
from ai import AIManager
from ai.utils import create_commit_message_prompt

async def main():
    """Example usage of AI providers"""

    # Example 1: Basic chat with default provider
    print("=== Example 1: Basic Chat ===")
    try:
        manager = AIManager()
        messages = [{"role": "user", "content": "Hello! Can you help me with coding?"}]
        response = await manager.chat(messages)
        print(f"AI Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Using specific provider (OpenAI)
    print("\n=== Example 2: OpenAI GPT-4 ===")
    try:
        openai_manager = AIManager(provider="openai", model="gpt-4")
        messages = [{"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}]
        response = await openai_manager.chat(messages)
        print(f"GPT-4 Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Using Claude
    print("\n=== Example 3: Claude ===")
    try:
        claude_manager = AIManager(provider="claude", model="claude-3-sonnet-20240229")
        messages = [{"role": "user", "content": "Explain the concept of recursion in programming"}]
        response = await claude_manager.chat(messages)
        print(f"Claude Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 4: Using Ollama (local)
    print("\n=== Example 4: Ollama ===")
    try:
        ollama_manager = AIManager(provider="ollama", model="codellama")
        messages = [{"role": "user", "content": "What are the best practices for Python code organization?"}]
        response = await ollama_manager.chat(messages)
        print(f"Ollama Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 5: Commit message generation
    print("\n=== Example 5: Commit Message Generation ===")
    try:
        # Mock changes data
        changes = [
            {"summary": "Added user authentication system"},
            {"summary": "Implemented JWT token validation"},
            {"summary": "Added password hashing with bcrypt"}
        ]
        intent = "Implementing secure user authentication"

        # Create commit message prompt
        prompt_messages = create_commit_message_prompt(changes, intent)

        # Generate commit message
        commit_manager = AIManager()
        commit_message = await commit_manager.chat(prompt_messages)
        print(f"Generated Commit Message:\n{commit_message}")
    except Exception as e:
        print(f"Error: {e}")

def setup_environment():
    """Setup environment variables for testing"""
    print("Setting up environment...")

    # Set default provider
    os.environ['IBEX_AI_PROVIDER'] = 'openai'

    # Check for API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set. OpenAI features will not work.")
    else:
        print("✓ OpenAI API key found")

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("⚠️  ANTHROPIC_API_KEY not set. Claude features will not work.")
    else:
        print("✓ Anthropic API key found")

    # Ollama doesn't require API key
    print("✓ Ollama (local) available")

if __name__ == "__main__":
    setup_environment()
    asyncio.run(main())
