"""
OpenAI provider implementation
"""

import os
from typing import List, Dict, Any, Optional
from .base_provider import BaseProvider

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    openai = None

class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider"""

    def __init__(self, model: str, api_key: Optional[str] = None):
        super().__init__(model, api_key)
        self.setup_client()

    def setup_client(self):
        """Setup OpenAI client"""
        if not HAS_OPENAI:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")

        api_key = self.api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")

        openai.api_key = api_key
        self.client = openai

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion using OpenAI"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Extract system message if present
        system_message = None
        user_messages = []

        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                user_messages.append(msg)

        # Prepare messages for OpenAI
        openai_messages = []
        if system_message:
            openai_messages.append({"role": "system", "content": system_message})
        openai_messages.extend(user_messages)

        try:
            response = await self.client.ChatCompletion.acreate(
                model=self.model,
                messages=openai_messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1024)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return HAS_OPENAI and self.client is not None

    def validate_api_key(self) -> bool:
        """Validate OpenAI API key"""
        api_key = self.api_key or os.getenv('OPENAI_API_KEY')
        return bool(api_key and api_key.startswith('sk-'))

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available OpenAI models"""
        return [
            'gpt-4',
            'gpt-4-turbo-preview',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k'
        ]
