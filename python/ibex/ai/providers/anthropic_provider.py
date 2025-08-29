"""
Anthropic Claude provider implementation
"""

import os
from typing import List, Dict, Any, Optional
from .base_provider import BaseProvider

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    anthropic = None

class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider"""

    def __init__(self, model: str, api_key: Optional[str] = None):
        super().__init__(model, api_key)
        self.setup_client()

    def setup_client(self):
        """Setup Anthropic client"""
        if not HAS_ANTHROPIC:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")

        api_key = self.api_key or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")

        self.client = anthropic.Anthropic(api_key=api_key)

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion using Claude"""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        # Extract system message if present
        system_message = None
        user_messages = []

        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                user_messages.append(msg)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 1024),
                temperature=kwargs.get('temperature', 0.7),
                system=system_message,
                messages=user_messages
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")

    def is_available(self) -> bool:
        """Check if Anthropic is available"""
        return HAS_ANTHROPIC and self.client is not None

    def validate_api_key(self) -> bool:
        """Validate Anthropic API key"""
        api_key = self.api_key or os.getenv('ANTHROPIC_API_KEY')
        return bool(api_key and api_key.startswith('sk-ant-'))

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available Claude models"""
        return [
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-2.1',
            'claude-2.0'
        ]
