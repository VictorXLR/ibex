"""
Tests for CLI commands functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from ibex.ai.cli_commands import (
    cmd_config_init, cmd_config_show, cmd_config_validate, 
    cmd_config_sample, cmd_config_switch
)
from ibex.ai.config import ProviderType


class TestCLICommands:
    """Test CLI command functions"""
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_init_success(self, mock_print, mock_get_config_manager):
        """Test config init command success"""
        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.default_provider.value = "ollama"
        
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager.validate_config.return_value = (True, [])
        mock_config_manager.save_config.return_value = True
        mock_config_manager.config_path = "/test/path/config.yaml"
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_init(temp_dir)
        
        # Verify expected print statements
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Initializing IBEX AI Configuration" in call for call in print_calls)
        assert any("Configuration is valid" in call for call in print_calls)
        assert any("Configuration saved" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_init_with_issues(self, mock_print, mock_get_config_manager):
        """Test config init command with validation issues"""
        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.default_provider.value = "ollama"
        
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager.validate_config.return_value = (False, ["API key missing"])
        mock_config_manager.save_config.return_value = True
        mock_config_manager.config_path = "/test/path/config.yaml"
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_init(temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Configuration issues found" in call for call in print_calls)
        assert any("API key missing" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_show(self, mock_print, mock_get_config_manager):
        """Test config show command"""
        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.default_provider.value = "ollama"
        mock_config.config_path = "/test/path/config.yaml"
        
        # Mock provider configs
        mock_ollama_config = Mock()
        mock_ollama_config.enabled = True
        mock_ollama_config.model = "test-model"
        mock_ollama_config.api_key = None
        mock_ollama_config.base_url = "http://localhost:11434"
        mock_ollama_config.max_tokens = 8192
        mock_ollama_config.temperature = 0.3
        
        mock_openai_config = Mock()
        mock_openai_config.enabled = False
        mock_openai_config.model = "gpt-4"
        mock_openai_config.api_key = "test-key"
        mock_openai_config.max_tokens = 4096
        mock_openai_config.temperature = 0.3
        
        mock_config.providers = {
            ProviderType.OLLAMA: mock_ollama_config,
            ProviderType.OPENAI: mock_openai_config
        }
        
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager.config_path = "/test/path/config.yaml"
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_show(temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Current IBEX AI Configuration" in call for call in print_calls)
        assert any("Provider Status" in call for call in print_calls)
        assert any("ollama" in call for call in print_calls)
        assert any("Enabled" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_validate_success(self, mock_print, mock_get_config_manager):
        """Test config validate command success"""
        mock_config_manager = Mock()
        mock_config = Mock()
        
        mock_config_manager.validate_config.return_value = (True, [])
        mock_config_manager.get_available_providers.return_value = [ProviderType.OLLAMA]
        mock_config_manager.load_config.return_value = mock_config
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_validate(temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Configuration is valid" in call for call in print_calls)
        assert any("Available providers: ollama" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_validate_failure(self, mock_print, mock_get_config_manager):
        """Test config validate command failure"""
        mock_config_manager = Mock()
        
        mock_config_manager.validate_config.return_value = (False, ["API key missing", "Invalid model"])
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_validate(temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Configuration validation failed" in call for call in print_calls)
        assert any("API key missing" in call for call in print_calls)
        assert any("Invalid model" in call for call in print_calls)
        assert any("Suggestions" in call for call in print_calls)
    
    @patch('builtins.print')
    def test_cmd_config_sample(self, mock_print):
        """Test config sample command"""
        cmd_config_sample()
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        sample_output = "\n".join(print_calls)
        
        assert "Sample IBEX AI Configuration" in sample_output
        assert "default_provider: ollama" in sample_output
        assert "OPENAI_API_KEY" in sample_output
        assert "ANTHROPIC_API_KEY" in sample_output
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_switch_success(self, mock_print, mock_get_config_manager):
        """Test config switch command success"""
        mock_config_manager = Mock()
        mock_config = Mock()
        
        # Mock provider config
        mock_provider_config = Mock()
        mock_provider_config.enabled = True
        mock_config.providers = {ProviderType.CLAUDE: mock_provider_config}
        
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager.save_config.return_value = True
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_switch("claude", temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Default provider switched to: claude" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_switch_unknown_provider(self, mock_print, mock_get_config_manager):
        """Test config switch command with unknown provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_switch("unknown", temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Unknown provider: unknown" in call for call in print_calls)
        assert any("Available providers:" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_switch_not_configured(self, mock_print, mock_get_config_manager):
        """Test config switch command with provider not configured"""
        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.providers = {}  # No providers configured
        
        mock_config_manager.load_config.return_value = mock_config
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_switch("openai", temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Provider openai not configured" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_switch_disabled(self, mock_print, mock_get_config_manager):
        """Test config switch command with disabled provider"""
        mock_config_manager = Mock()
        mock_config = Mock()
        
        # Mock disabled provider config
        mock_provider_config = Mock()
        mock_provider_config.enabled = False
        mock_config.providers = {ProviderType.OPENAI: mock_provider_config}
        
        mock_config_manager.load_config.return_value = mock_config
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_switch("openai", temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Provider openai is disabled" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.get_config_manager')
    @patch('builtins.print')
    def test_cmd_config_switch_save_failure(self, mock_print, mock_get_config_manager):
        """Test config switch command with save failure"""
        mock_config_manager = Mock()
        mock_config = Mock()
        
        # Mock enabled provider config
        mock_provider_config = Mock()
        mock_provider_config.enabled = True
        mock_config.providers = {ProviderType.CLAUDE: mock_provider_config}
        
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager.save_config.return_value = False  # Save fails
        mock_get_config_manager.return_value = mock_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd_config_switch("claude", temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Failed to save configuration" in call for call in print_calls)


class TestCLICommandsIntegration:
    """Integration tests for CLI commands"""
    
    @patch('ibex.ai.cli_commands.AIManager')
    @patch('builtins.print')
    @pytest.mark.asyncio
    async def test_cmd_config_test_available_provider(self, mock_print, mock_ai_manager_class):
        """Test config test command with available provider"""
        mock_ai_manager = Mock()
        mock_ai_manager.provider = "ollama"
        mock_ai_manager.is_available.return_value = True
        mock_ai_manager.chat = AsyncMock(return_value="AI test successful")
        mock_ai_manager.list_available_providers.return_value = [
            {
                'provider': 'ollama',
                'model': 'test-model',
                'available': True,
                'enabled': True
            }
        ]
        mock_ai_manager_class.return_value = mock_ai_manager
        
        # Import and call the async command
        from ibex.ai.cli_commands import cmd_config_test
        
        with tempfile.TemporaryDirectory() as temp_dir:
            await cmd_config_test(temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Testing AI Provider Configurations" in call for call in print_calls)
        assert any("Provider is available" in call for call in print_calls)
        assert any("Basic chat functionality working" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.AIManager')
    @patch('builtins.print')
    @pytest.mark.asyncio
    async def test_cmd_config_test_unavailable_provider(self, mock_print, mock_ai_manager_class):
        """Test config test command with unavailable provider"""
        mock_ai_manager = Mock()
        mock_ai_manager.provider = "ollama"
        mock_ai_manager.is_available.return_value = False
        mock_ai_manager_class.return_value = mock_ai_manager
        
        from ibex.ai.cli_commands import cmd_config_test
        
        with tempfile.TemporaryDirectory() as temp_dir:
            await cmd_config_test(temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Provider is not available" in call for call in print_calls)
    
    @patch('ibex.ai.cli_commands.AIManager')
    @patch('builtins.print')
    @pytest.mark.asyncio
    async def test_cmd_config_test_chat_failure(self, mock_print, mock_ai_manager_class):
        """Test config test command with chat failure"""
        mock_ai_manager = Mock()
        mock_ai_manager.provider = "ollama"
        mock_ai_manager.is_available.return_value = True
        mock_ai_manager.chat = AsyncMock(side_effect=Exception("Chat failed"))
        mock_ai_manager_class.return_value = mock_ai_manager
        
        from ibex.ai.cli_commands import cmd_config_test
        
        with tempfile.TemporaryDirectory() as temp_dir:
            await cmd_config_test(temp_dir)
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Chat test failed" in call for call in print_calls)


class TestCLICommandMapping:
    """Test the command mapping for CLI integration"""
    
    def test_ai_commands_mapping(self):
        """Test that AI_COMMANDS mapping is properly defined"""
        from ibex.ai.cli_commands import AI_COMMANDS
        
        expected_commands = [
            'config-init',
            'config-show', 
            'config-test',
            'config-sample',
            'config-validate',
            'config-switch'
        ]
        
        for cmd in expected_commands:
            assert cmd in AI_COMMANDS
            assert callable(AI_COMMANDS[cmd])


if __name__ == "__main__":
    pytest.main([__file__])
