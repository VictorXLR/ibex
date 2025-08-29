"""
IBEX AI Module - Multi-provider LLM support

This module provides unified interfaces for OpenAI, Anthropic Claude, and Ollama models.
"""

from typing import Optional, Dict, Any, List
import os
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.client = None

    @abstractmethod
    def setup_client(self):
        """Setup the provider client"""
        pass

    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass

class AIManager:
    """Unified AI manager for multiple LLM providers"""

    def __init__(self, provider: str = None, model: str = None, api_key: Optional[str] = None):
        self.provider = provider or os.getenv('IBEX_AI_PROVIDER', 'ollama')
        self.model = model or self._get_default_model()
        self.api_key = api_key
        self._provider_instance = None
        self._setup_provider()

    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            'openai': 'gpt-4',
            'claude': 'claude-3-sonnet-20240229',
            'ollama': 'qwen3-coder:30b'
        }
        return os.getenv(f'{self.provider.upper()}_MODEL', defaults.get(self.provider, 'gpt-4'))

    def _setup_provider(self):
        """Setup the appropriate provider"""
        try:
            if self.provider == 'openai':
                from .providers.openai_provider import OpenAIProvider
                self._provider_instance = OpenAIProvider(self.model, self.api_key)
            elif self.provider == 'claude':
                from .providers.anthropic_provider import ClaudeProvider
                self._provider_instance = ClaudeProvider(self.model, self.api_key)
            elif self.provider == 'ollama':
                from .providers.ollama_provider import OllamaProvider
                self._provider_instance = OllamaProvider(self.model)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except ImportError as e:
            raise ImportError(f"Provider {self.provider} dependencies not installed: {e}")

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion"""
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")
        return await self._provider_instance.chat_completion(messages, **kwargs)

    def is_available(self) -> bool:
        """Check if current provider is available"""
        if not self._provider_instance:
            return False
        return self._provider_instance.is_available()

    def list_providers(self) -> List[str]:
        """List available providers"""
        providers = []
        try:
            from .providers.openai_provider import OpenAIProvider
            providers.append('openai')
        except ImportError:
            pass

        try:
            from .providers.anthropic_provider import ClaudeProvider
            providers.append('claude')
        except ImportError:
            pass

        try:
            from .providers.ollama_provider import OllamaProvider
            providers.append('ollama')
        except ImportError:
            pass

        return providers

    def validate_config(self) -> tuple[bool, str]:
        """Validate current configuration"""
        if not self._provider_instance:
            return False, "Provider not initialized"

        if not self._provider_instance.is_available():
            return False, f"{self.provider} client not available"

        return True, "Configuration is valid"
