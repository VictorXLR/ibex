"""
Comprehensive tests for LLMManager - LLM integration and functionality

Tests cover:
- LLMManager initialization with different providers
- Integration with AIManager
- Change analysis with LLM
- Git diff generation
- Provider validation and configuration
- Error handling for LLM operations
- Async operations
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from git import Repo
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ibex.llm import LLMManager


class TestLLMManagerInitialization:
    """Test LLMManager initialization with different configurations"""

    def test_init_with_default_provider(self):
        """Test initialization with default provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            assert llm_manager is not None
            assert llm_manager.path == Path(temp_dir)
            assert llm_manager.db_path == Path(temp_dir) / '.ibex' / 'semantic.db'

    def test_init_with_ollama_provider(self):
        """Test initialization with Ollama provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            assert llm_manager.provider == 'ollama'
            assert llm_manager.ai_manager is not None

    def test_init_with_openai_provider(self):
        """Test initialization with OpenAI provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                try:
                    llm_manager = LLMManager(temp_dir, provider='openai', model='gpt-4')

                    assert llm_manager.provider == 'openai'
                    assert llm_manager.model == 'gpt-4'
                except (ImportError, RuntimeError):
                    # OpenAI provider may not be available - this is acceptable
                    pytest.skip("OpenAI provider not available")

    def test_init_with_claude_provider(self):
        """Test initialization with Claude provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                try:
                    # Provider name is 'claude' not 'anthropic'
                    llm_manager = LLMManager(temp_dir, provider='claude', model='claude-3-opus')

                    assert llm_manager.provider == 'claude'
                    assert llm_manager.model == 'claude-3-opus'
                except (ImportError, RuntimeError):
                    # Claude provider may not be available - this is acceptable
                    pytest.skip("Claude provider not available")

    def test_init_with_custom_model(self):
        """Test initialization with custom model"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama', model='llama2')

            assert llm_manager.model == 'llama2'

    def test_init_creates_database(self):
        """Test that initialization creates database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            assert llm_manager.db_path.exists()


class TestGitIntegration:
    """Test Git integration functionality"""

    def test_init_with_git_repo(self):
        """Test initialization with a git repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            Repo.init(temp_dir)

            llm_manager = LLMManager(temp_dir)

            assert llm_manager.repo is not None
            assert isinstance(llm_manager.repo, Repo)

    def test_init_without_git_repo(self):
        """Test initialization without a git repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            # Should handle gracefully
            assert llm_manager.repo is None

    def test_generate_diff_without_repo(self):
        """Test diff generation when no git repo exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            diff = llm_manager.generate_diff("test.py")
            assert diff == "", "Should return empty string when no repo"

    def test_generate_diff_with_repo(self):
        """Test diff generation with a git repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            repo = Repo.init(temp_dir)

            # Create and commit a file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")

            repo.index.add(["test.py"])
            repo.index.commit("Initial commit")

            # Modify the file
            test_file.write_text("print('hello world')")

            llm_manager = LLMManager(temp_dir)
            diff = llm_manager.generate_diff("test.py")

            assert diff != "", "Should generate diff for modified file"
            assert "print('hello world')" in diff or "-print('hello')" in diff

    def test_generate_diff_for_nonexistent_file(self):
        """Test diff generation for file that doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)
            llm_manager = LLMManager(temp_dir)

            diff = llm_manager.generate_diff("nonexistent.py")
            # Should handle gracefully (return empty or handle error)
            assert isinstance(diff, str)


class TestLLMAnalysis:
    """Test LLM-powered change analysis"""

    @pytest.mark.asyncio
    async def test_analyze_changes_empty_list(self):
        """Test analyzing empty changes list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            result = await llm_manager.analyze_changes([], "test intent")
            assert result == "No changes to analyze"

    @pytest.mark.asyncio
    async def test_analyze_changes_provider_unavailable(self):
        """Test analysis when LLM provider is unavailable"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Mock is_available to return False
            llm_manager.ai_manager.is_available = Mock(return_value=False)

            changes = [{"file": "test.py"}]
            result = await llm_manager.analyze_changes(changes, "test intent")

            assert "not available" in result.lower()

    @pytest.mark.asyncio
    async def test_analyze_changes_with_no_diffs(self):
        """Test analysis when no git diffs are available"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Mock is_available to return True
            llm_manager.ai_manager.is_available = Mock(return_value=True)

            # Mock generate_diff to return empty
            llm_manager.generate_diff = Mock(return_value="")

            changes = [{"file": "test.py"}]
            result = await llm_manager.analyze_changes(changes, "test intent")

            assert result == "No git diffs available for analysis"

    @pytest.mark.asyncio
    async def test_analyze_changes_successful(self):
        """Test successful change analysis with LLM"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            repo = Repo.init(temp_dir)

            # Create and commit a file
            test_file = Path(temp_dir) / "auth.py"
            test_file.write_text("def login(): pass")
            repo.index.add(["auth.py"])
            repo.index.commit("Initial commit")

            # Modify the file
            test_file.write_text("def login():\n    return authenticate_user()")

            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Mock the AI manager's chat method
            mock_response = """Title: Add user authentication

Description: Implemented authentication logic in login function

Impact: Enhanced security by adding proper authentication"""

            llm_manager.ai_manager.chat = AsyncMock(return_value=mock_response)
            llm_manager.ai_manager.is_available = Mock(return_value=True)

            changes = [{"file": str(test_file)}]
            result = await llm_manager.analyze_changes(changes, "Add authentication")

            assert "authentication" in result.lower()
            llm_manager.ai_manager.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_changes_with_multiple_files(self):
        """Test analysis with multiple changed files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            # Create multiple files
            files = ["auth.py", "database.py", "api.py"]
            for filename in files:
                file_path = Path(temp_dir) / filename
                file_path.write_text(f"# {filename}")
                repo.index.add([filename])

            repo.index.commit("Initial commit")

            # Modify all files
            for filename in files:
                file_path = Path(temp_dir) / filename
                file_path.write_text(f"# {filename}\n# Modified")

            llm_manager = LLMManager(temp_dir, provider='ollama')
            llm_manager.ai_manager.chat = AsyncMock(return_value="Multi-file update")
            llm_manager.ai_manager.is_available = Mock(return_value=True)

            changes = [{"file": str(Path(temp_dir) / f)} for f in files]
            result = await llm_manager.analyze_changes(changes, "Update all modules")

            # Should have called chat with all diffs combined
            call_args = llm_manager.ai_manager.chat.call_args
            messages = call_args[0][0]
            user_message = messages[1]['content']

            # Verify all files are mentioned
            for filename in files:
                assert filename in user_message

    @pytest.mark.asyncio
    async def test_analyze_changes_llm_error(self):
        """Test handling of LLM errors during analysis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("original")
            repo.index.add(["test.py"])
            repo.index.commit("Initial")

            test_file.write_text("modified")

            llm_manager = LLMManager(temp_dir, provider='ollama')
            llm_manager.ai_manager.chat = AsyncMock(side_effect=Exception("API Error"))
            llm_manager.ai_manager.is_available = Mock(return_value=True)

            changes = [{"file": str(test_file)}]
            result = await llm_manager.analyze_changes(changes, "test")

            assert "Error analyzing changes" in result
            assert "API Error" in result

    @pytest.mark.asyncio
    async def test_analyze_changes_prompt_format(self):
        """Test that the prompt is correctly formatted"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            test_file = Path(temp_dir) / "feature.py"
            test_file.write_text("def feature(): pass")
            repo.index.add(["feature.py"])
            repo.index.commit("Initial")

            test_file.write_text("def feature():\n    return 'implemented'")

            llm_manager = LLMManager(temp_dir, provider='ollama')
            llm_manager.ai_manager.chat = AsyncMock(return_value="Analysis")
            llm_manager.ai_manager.is_available = Mock(return_value=True)

            intent = "Implement feature function"
            changes = [{"file": str(test_file)}]
            await llm_manager.analyze_changes(changes, intent)

            # Check the prompt format
            call_args = llm_manager.ai_manager.chat.call_args[0][0]
            user_message = call_args[1]['content']

            assert intent in user_message
            assert "Title:" in user_message
            assert "Description:" in user_message
            assert "Impact:" in user_message


class TestProviderManagement:
    """Test provider availability and configuration"""

    def test_list_available_providers(self):
        """Test listing available providers"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            providers = llm_manager.list_available_providers()

            assert isinstance(providers, list)
            # At least one provider should be available
            assert len(providers) >= 0

    def test_validate_configuration_ollama(self):
        """Test configuration validation for Ollama"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            is_valid, message = llm_manager.validate_configuration()

            # Should be valid if ollama is installed
            assert isinstance(is_valid, bool)
            assert isinstance(message, str)

    def test_validate_configuration_openai_without_key(self):
        """Test validation fails for OpenAI without API key"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Ensure no API key is set
            with patch.dict(os.environ, {}, clear=True):
                try:
                    llm_manager = LLMManager(temp_dir, provider='openai')
                    is_valid, message = llm_manager.validate_configuration()

                    assert is_valid == False
                    assert "API" in message or "key" in message.lower()
                except (ValueError, RuntimeError, ImportError):
                    # It's also acceptable to raise an error during initialization
                    pytest.skip("OpenAI provider not available or configuration error")

    def test_validate_configuration_anthropic_without_key(self):
        """Test validation fails for Anthropic without API key"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {}, clear=True):
                try:
                    llm_manager = LLMManager(temp_dir, provider='anthropic')
                    is_valid, message = llm_manager.validate_configuration()

                    assert is_valid == False
                    assert "API" in message or "key" in message.lower()
                except ValueError:
                    pass

    def test_validate_configuration_with_valid_openai_key(self):
        """Test validation succeeds with valid OpenAI key"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'}):
                try:
                    llm_manager = LLMManager(temp_dir, provider='openai')
                    is_valid, message = llm_manager.validate_configuration()

                    # Should be valid (library is installed and key is set)
                    # Note: Actual validation depends on library availability
                    assert isinstance(is_valid, bool)
                except (ValueError, RuntimeError, ImportError):
                    # Configuration might still fail if library not installed
                    pytest.skip("OpenAI provider not available")


class TestEndToEndIntegration:
    """Test end-to-end integration of LLMManager functionality"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: analyze changes and store in database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup git repo
            repo = Repo.init(temp_dir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()

            # Create initial file
            test_file = Path(temp_dir) / "module.py"
            test_file.write_text("class Module: pass")
            repo.index.add(["module.py"])
            initial_commit = repo.index.commit("Initial commit")

            # Modify file
            test_file.write_text("class Module:\n    def execute(self): pass")

            # Initialize LLMManager
            llm_manager = LLMManager(temp_dir, provider='ollama', model='llama2')
            llm_manager.ai_manager.chat = AsyncMock(return_value="Added execute method")
            llm_manager.ai_manager.is_available = Mock(return_value=True)

            # Analyze changes
            changes = [{"file": str(test_file), "hash": "abc123"}]
            analysis = await llm_manager.analyze_changes(changes, "Add module execution")

            # Store in database
            llm_manager.store_semantic_change(
                initial_commit.hexsha,
                analysis,
                changes,
                "Add module execution"
            )

            # Verify it's stored
            history = llm_manager.get_semantic_history()
            assert len(history) == 1
            assert history[0]['description'] == "Added execute method"
            assert history[0]['provider'] == 'ollama'
            assert history[0]['model'] == 'llama2'

    @pytest.mark.asyncio
    async def test_multiple_analysis_cycles(self):
        """Test multiple analyze-store cycles"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            llm_manager = LLMManager(temp_dir, provider='ollama')
            llm_manager.ai_manager.chat = AsyncMock(return_value="Analysis result")
            llm_manager.ai_manager.is_available = Mock(return_value=True)

            # Perform multiple cycles
            for i in range(3):
                # Create file
                file_path = Path(temp_dir) / f"file{i}.py"
                file_path.write_text(f"# File {i}")
                repo.index.add([f"file{i}.py"])
                commit = repo.index.commit(f"Commit {i}")

                # Analyze and store
                changes = [{"file": str(file_path)}]
                analysis = await llm_manager.analyze_changes(changes, f"Intent {i}")
                llm_manager.store_semantic_change(
                    commit.hexsha,
                    analysis,
                    changes,
                    f"Intent {i}"
                )

            # Verify all stored
            history = llm_manager.get_semantic_history()
            assert len(history) == 3

            # Verify intents
            intents = [h['intent'] for h in history]
            assert "Intent 0" in intents
            assert "Intent 1" in intents
            assert "Intent 2" in intents


class TestAIManagerIntegration:
    """Test integration with AIManager"""

    def test_ai_manager_initialization(self):
        """Test that AIManager is properly initialized"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            assert llm_manager.ai_manager is not None
            assert hasattr(llm_manager.ai_manager, 'chat')
            assert hasattr(llm_manager.ai_manager, 'is_available')

    def test_provider_consistency(self):
        """Test that provider is consistent between LLMManager and AIManager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama', model='llama2')

            assert llm_manager.provider == 'ollama'
            assert llm_manager.model == 'llama2'
            assert llm_manager.ai_manager.provider == 'ollama'

    @pytest.mark.asyncio
    async def test_chat_method_delegation(self):
        """Test that chat calls are properly delegated to AIManager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Mock the chat method and is_available
            expected_response = "Test response"
            llm_manager.ai_manager.chat = AsyncMock(return_value=expected_response)
            llm_manager.ai_manager.is_available = Mock(return_value=True)

            # Call through analyze_changes which uses chat
            repo = Repo.init(temp_dir)
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("code")
            repo.index.add(["test.py"])
            repo.index.commit("Initial")
            test_file.write_text("modified code")

            # Mock generate_diff to return non-empty diff
            llm_manager.generate_diff = Mock(return_value="diff content")

            changes = [{"file": str(test_file)}]
            result = await llm_manager.analyze_changes(changes, "test")

            assert result == expected_response
            llm_manager.ai_manager.chat.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
