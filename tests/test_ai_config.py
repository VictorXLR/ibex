"""
Tests for AI configuration management system
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from ibex.ai.config import ConfigManager, ProviderType, ProviderConfig, AIConfig


class TestProviderConfig:
    """Test ProviderConfig class"""
    
    def test_provider_config_creation(self):
        """Test creating a provider config"""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            model="test-model",
            max_tokens=1000
        )
        
        assert config.provider_type == ProviderType.OLLAMA
        assert config.model == "test-model"
        assert config.max_tokens == 1000
        assert config.enabled == True
    
    def test_provider_config_to_dict(self):
        """Test converting provider config to dictionary"""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        result = config.to_dict()
        assert result['provider_type'] == 'openai'
        assert result['model'] == 'gpt-4'
        assert result['api_key'] == 'test-key'
    
    def test_provider_config_from_dict(self):
        """Test creating provider config from dictionary"""
        data = {
            'provider_type': 'claude',
            'model': 'claude-3-sonnet',
            'max_tokens': 2000,
            'temperature': 0.5
        }
        
        config = ProviderConfig.from_dict(data)
        assert config.provider_type == ProviderType.CLAUDE
        assert config.model == 'claude-3-sonnet'
        assert config.max_tokens == 2000
        assert config.temperature == 0.5


class TestAIConfig:
    """Test AIConfig class"""
    
    def test_ai_config_defaults(self):
        """Test AI config default values"""
        config = AIConfig()
        
        assert config.default_provider == ProviderType.OLLAMA
        assert config.providers == {}
        assert config.fallback_order == [ProviderType.OLLAMA, ProviderType.OPENAI, ProviderType.CLAUDE]
        assert 'max_file_size' in config.analysis_settings
    
    def test_ai_config_with_providers(self):
        """Test AI config with providers"""
        ollama_config = ProviderConfig(ProviderType.OLLAMA, "test-model")
        config = AIConfig(
            default_provider=ProviderType.OLLAMA,
            providers={ProviderType.OLLAMA: ollama_config}
        )
        
        assert config.default_provider == ProviderType.OLLAMA
        assert ProviderType.OLLAMA in config.providers
        assert config.providers[ProviderType.OLLAMA].model == "test-model"


class TestConfigManager:
    """Test ConfigManager class"""
    
    def test_config_manager_init(self):
        """Test config manager initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            assert manager.project_root == Path(temp_dir)
            assert '.ibex' in str(manager.config_path)
    
    def test_create_default_config(self):
        """Test creating default configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            config = manager._create_default_config()
            
            assert isinstance(config, AIConfig)
            assert len(config.providers) == 3
            assert ProviderType.OLLAMA in config.providers
            assert ProviderType.OPENAI in config.providers
            assert ProviderType.CLAUDE in config.providers
    
    def test_load_config_creates_default(self):
        """Test that load_config creates default when no file exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            config = manager.load_config()
            
            assert isinstance(config, AIConfig)
            assert config.default_provider in [ProviderType.OLLAMA, ProviderType.OPENAI, ProviderType.CLAUDE]
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_update_from_environment(self):
        """Test updating config from environment variables"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            manager.load_config()
            manager.update_from_environment()
            
            config = manager._config
            openai_config = config.providers[ProviderType.OPENAI]
            assert openai_config.api_key == 'test-key'
            assert openai_config.enabled == True
    
    def test_validate_config_no_issues(self):
        """Test config validation with no issues"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            config = manager.load_config()
            
            # Ensure at least one provider is enabled
            config.providers[ProviderType.OLLAMA].enabled = True
            config.default_provider = ProviderType.OLLAMA
            manager._config = config
            
            is_valid, issues = manager.validate_config()
            assert is_valid or len(issues) == 0  # No critical issues
    
    def test_validate_config_with_issues(self):
        """Test config validation with issues"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            config = manager.load_config()
            
            # Create invalid config
            for provider_config in config.providers.values():
                provider_config.enabled = False
            
            manager._config = config
            is_valid, issues = manager.validate_config()
            assert not is_valid
            assert len(issues) > 0
    
    def test_get_available_providers(self):
        """Test getting available providers"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            config = manager.load_config()
            
            # Enable Ollama only
            config.providers[ProviderType.OLLAMA].enabled = True
            config.providers[ProviderType.OPENAI].enabled = False
            config.providers[ProviderType.CLAUDE].enabled = False
            manager._config = config
            
            available = manager.get_available_providers()
            assert ProviderType.OLLAMA in available
            assert ProviderType.OPENAI not in available
            assert ProviderType.CLAUDE not in available
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create and save config
            manager1 = ConfigManager(project_root=temp_dir)
            config = manager1.load_config()
            config.providers[ProviderType.OLLAMA].model = "custom-model"
            success = manager1.save_config(config)
            assert success
            
            # Load config with new manager
            manager2 = ConfigManager(project_root=temp_dir)
            loaded_config = manager2.load_config()
            assert loaded_config.providers[ProviderType.OLLAMA].model == "custom-model"
    
    def test_set_and_get_provider_config(self):
        """Test setting and getting provider configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            
            new_config = ProviderConfig(
                provider_type=ProviderType.OLLAMA,
                model="new-model",
                max_tokens=5000
            )
            
            manager.set_provider_config(ProviderType.OLLAMA, new_config)
            retrieved_config = manager.get_provider_config(ProviderType.OLLAMA)
            
            assert retrieved_config.model == "new-model"
            assert retrieved_config.max_tokens == 5000
    
    def test_set_default_provider(self):
        """Test setting default provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(project_root=temp_dir)
            manager.load_config()
            
            manager.set_default_provider(ProviderType.CLAUDE)
            assert manager.get_default_provider() == ProviderType.CLAUDE
    
    def test_create_sample_config(self):
        """Test creating sample configuration"""
        manager = ConfigManager()
        sample = manager.create_sample_config()
        
        assert isinstance(sample, str)
        assert 'default_provider' in sample
        assert 'ollama' in sample
        assert 'openai' in sample
        assert 'claude' in sample


if __name__ == "__main__":
    pytest.main([__file__])
