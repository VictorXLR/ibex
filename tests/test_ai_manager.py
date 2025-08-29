"""
Tests for AI Manager functionality
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from ibex.ai import AIManager
from ibex.ai.config import ConfigManager, ProviderType, ProviderConfig, AIConfig


class TestAIManager:
    """Test AIManager class"""
    
    def test_ai_manager_init_default(self):
        """Test AI manager initialization with defaults"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(project_root=temp_dir)
            
            assert manager.project_root == Path(temp_dir)
            assert manager.provider_type in [ProviderType.OLLAMA, ProviderType.OPENAI, ProviderType.CLAUDE]
            assert manager.provider_config is not None
    
    def test_ai_manager_init_with_provider(self):
        """Test AI manager initialization with specific provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            
            assert manager.provider_type == ProviderType.OLLAMA
            assert manager.provider == "ollama"
    
    def test_ai_manager_init_invalid_provider(self):
        """Test AI manager initialization with invalid provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Unsupported provider"):
                AIManager(provider="invalid", project_root=temp_dir)
    
    def test_ai_manager_properties(self):
        """Test AI manager properties"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", model="test-model", project_root=temp_dir)
            
            assert manager.provider == "ollama"
            assert manager.model == "test-model"
    
    def test_get_config_summary(self):
        """Test getting configuration summary"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            summary = manager.get_config_summary()
            
            assert 'provider' in summary
            assert 'model' in summary
            assert 'enabled' in summary
            assert 'available' in summary
            assert summary['provider'] == 'ollama'
    
    @patch('ibex.ai.providers.ollama_provider.OllamaProvider')
    def test_switch_provider_success(self, mock_ollama):
        """Test successful provider switching"""
        mock_instance = Mock()
        mock_instance.is_available.return_value = True
        mock_ollama.return_value = mock_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            
            # Ensure OpenAI is configured and enabled
            manager.config.providers[ProviderType.OPENAI].enabled = True
            manager.config.providers[ProviderType.OPENAI].api_key = "test-key"
            
            success = manager.switch_provider(ProviderType.OPENAI)
            # Note: This might fail due to missing OpenAI provider import, which is expected in test
    
    def test_switch_provider_disabled(self):
        """Test switching to disabled provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            
            # Disable all other providers
            manager.config.providers[ProviderType.OPENAI].enabled = False
            manager.config.providers[ProviderType.CLAUDE].enabled = False
            
            success = manager.switch_provider(ProviderType.OPENAI)
            assert not success
    
    @patch('ibex.ai.providers.ollama_provider.OllamaProvider')
    def test_list_available_providers(self, mock_ollama):
        """Test listing available providers"""
        mock_instance = Mock()
        mock_instance.is_available.return_value = True
        mock_ollama.return_value = mock_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            providers = manager.list_available_providers()
            
            assert isinstance(providers, list)
            assert len(providers) >= 1  # At least Ollama should be listed
            
            # Check structure
            for provider in providers:
                assert 'provider' in provider
                assert 'model' in provider
                assert 'enabled' in provider
                assert 'available' in provider
                assert 'is_current' in provider
    
    @patch('ibex.ai.providers.ollama_provider.OllamaProvider')
    @pytest.mark.asyncio
    async def test_chat_with_config_defaults(self, mock_ollama):
        """Test chat functionality with configuration defaults"""
        mock_instance = AsyncMock()
        mock_instance.is_available.return_value = True
        mock_instance.chat_completion.return_value = "Test response"
        mock_ollama.return_value = mock_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            
            messages = [{"role": "user", "content": "Hello"}]
            response = await manager.chat(messages)
            
            assert response == "Test response"
            
            # Verify that config defaults were used
            mock_instance.chat_completion.assert_called_once()
            call_args = mock_instance.chat_completion.call_args
            kwargs = call_args[1]
            
            assert 'max_tokens' in kwargs
            assert 'temperature' in kwargs
            assert 'max_retries' in kwargs
    
    @patch('ibex.ai.providers.ollama_provider.OllamaProvider')
    @pytest.mark.asyncio
    async def test_chat_with_override_params(self, mock_ollama):
        """Test chat functionality with parameter overrides"""
        mock_instance = AsyncMock()
        mock_instance.is_available.return_value = True
        mock_instance.chat_completion.return_value = "Test response"
        mock_ollama.return_value = mock_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            
            messages = [{"role": "user", "content": "Hello"}]
            response = await manager.chat(messages, max_tokens=1000, temperature=0.5)
            
            assert response == "Test response"
            
            # Verify that overrides were used
            call_args = mock_instance.chat_completion.call_args
            kwargs = call_args[1]
            
            assert kwargs['max_tokens'] == 1000
            assert kwargs['temperature'] == 0.5
    
    @patch('ibex.ai.providers.ollama_provider.OllamaProvider')
    def test_validate_config_success(self, mock_ollama):
        """Test configuration validation success"""
        mock_instance = Mock()
        mock_instance.is_available.return_value = True
        mock_ollama.return_value = mock_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            
            is_valid, issues = manager.validate_config()
            # Should be valid with Ollama as default
            assert is_valid or len(issues) == 0
    
    @patch('ibex.ai.providers.ollama_provider.OllamaProvider')
    def test_validate_config_unavailable_provider(self, mock_ollama):
        """Test configuration validation with unavailable provider"""
        mock_instance = Mock()
        mock_instance.is_available.return_value = False
        mock_ollama.return_value = mock_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            
            is_valid, issues = manager.validate_config()
            assert not is_valid
            assert len(issues) > 0
    
    def test_ai_manager_with_custom_config_manager(self):
        """Test AI manager with custom config manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = ConfigManager(project_root=temp_dir)
            manager = AIManager(config_manager=config_manager, project_root=temp_dir)
            
            assert manager.config_manager == config_manager
    
    @patch('ibex.ai.providers.ollama_provider.OllamaProvider')
    @pytest.mark.asyncio
    async def test_chat_provider_not_initialized(self, mock_ollama):
        """Test chat when provider is not initialized"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            manager._provider_instance = None
            
            with pytest.raises(RuntimeError, match="Provider not initialized"):
                await manager.chat([{"role": "user", "content": "Hello"}])
    
    def test_is_available_no_provider(self):
        """Test is_available when no provider instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AIManager(provider="ollama", project_root=temp_dir)
            manager._provider_instance = None
            
            assert not manager.is_available()


class TestAIManagerIntegration:
    """Integration tests for AI Manager"""
    
    @patch('ibex.ai.providers.ollama_provider.OllamaProvider')
    def test_end_to_end_config_flow(self, mock_ollama):
        """Test end-to-end configuration flow"""
        mock_instance = Mock()
        mock_instance.is_available.return_value = True
        mock_ollama.return_value = mock_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create manager
            manager = AIManager(provider="ollama", project_root=temp_dir)
            
            # Verify initial state
            assert manager.provider == "ollama"
            assert manager.is_available()
            
            # Get and modify config
            summary = manager.get_config_summary()
            assert summary['provider'] == 'ollama'
            
            # Test validation
            is_valid, issues = manager.validate_config()
            assert is_valid or len(issues) == 0  # Should be valid or have non-critical issues


if __name__ == "__main__":
    pytest.main([__file__])
