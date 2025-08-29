"""
Base provider class for LLM providers
"""

from typing import List, Dict, Any, Optional
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

    def validate_api_key(self) -> bool:
        """Validate API key if required"""
        return True
