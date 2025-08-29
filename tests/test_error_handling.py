"""
Tests for error handling and retry logic improvements
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from ibex.ai.providers.ollama_provider import OllamaProvider


class TestOllamaProviderErrorHandling:
    """Test OllamaProvider error handling and retry logic"""
    
    def test_ollama_provider_init(self):
        """Test OllamaProvider initialization"""
        provider = OllamaProvider("test-model")
        
        assert provider.model == "test-model"
        assert provider.base_url == "http://localhost:11434"
        assert provider.api_key is None
    
    def test_ollama_provider_init_with_base_url(self):
        """Test OllamaProvider initialization with custom base URL"""
        provider = OllamaProvider("test-model", base_url="http://custom:8080")
        
        assert provider.base_url == "http://custom:8080"
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_success(self, mock_post):
        """Test successful chat completion"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "message": {"content": "Hello, world!"}
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        response = await provider.chat_completion(messages)
        assert response == "Hello, world!"
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_with_system_message(self, mock_post):
        """Test chat completion with system message"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "message": {"content": "System understood"}
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]
        
        response = await provider.chat_completion(messages)
        assert response == "System understood"
        
        # Verify system message was included in payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert len(payload['messages']) == 2
        assert payload['messages'][0]['role'] == 'system'
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_custom_parameters(self, mock_post):
        """Test chat completion with custom parameters"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "message": {"content": "Custom response"}
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        await provider.chat_completion(
            messages, 
            temperature=0.8, 
            max_tokens=2000,
            max_retries=5,
            retry_delay=2
        )
        
        # Verify custom parameters were used
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['options']['temperature'] == 0.8
        assert payload['options']['num_predict'] == 2000
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_http_error_no_retry(self, mock_post):
        """Test chat completion with non-retryable HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(RuntimeError, match="Ollama API error 400"):
            await provider.chat_completion(messages)
    
    @patch('aiohttp.ClientSession.post')
    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_chat_completion_http_error_with_retry(self, mock_sleep, mock_post):
        """Test chat completion with retryable HTTP error"""
        # First call fails with 500, second succeeds
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        mock_response_fail.text.return_value = "Internal Server Error"
        
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json.return_value = {
            "message": {"content": "Success after retry"}
        }
        
        mock_post.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_success
        ]
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        response = await provider.chat_completion(messages, max_retries=2)
        assert response == "Success after retry"
        
        # Verify retry delay was called
        mock_sleep.assert_called_once()
    
    @patch('aiohttp.ClientSession.post')
    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_chat_completion_max_retries_exceeded(self, mock_sleep, mock_post):
        """Test chat completion when max retries are exceeded"""
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_response.text.return_value = "Service Unavailable"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(RuntimeError, match="Ollama API error 503"):
            await provider.chat_completion(messages, max_retries=2)
        
        # Should have called post 2 times (initial + 1 retry)
        assert mock_post.call_count == 2
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_connection_error(self, mock_post):
        """Test chat completion with connection error"""
        mock_post.side_effect = aiohttp.ClientConnectorError(
            connection_key=Mock(),
            os_error=Exception("Connection refused")
        )
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(RuntimeError, match="Connection failed to Ollama"):
            await provider.chat_completion(messages, max_retries=1)
    
    @patch('aiohttp.ClientSession.post')
    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_chat_completion_connection_error_with_retry(self, mock_sleep, mock_post):
        """Test chat completion with connection error and retry"""
        # First call fails with connection error, second succeeds
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json.return_value = {
            "message": {"content": "Connected after retry"}
        }
        
        mock_post.side_effect = [
            aiohttp.ClientConnectorError(
                connection_key=Mock(),
                os_error=Exception("Connection refused")
            ),
            AsyncMock(return_value=mock_response_success).__aenter__.return_value
        ]
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        response = await provider.chat_completion(messages, max_retries=2)
        assert response == "Connected after retry"
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_timeout_error(self, mock_post):
        """Test chat completion with timeout error"""
        mock_post.side_effect = aiohttp.ClientTimeout()
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(RuntimeError, match="Request timeout to Ollama API"):
            await provider.chat_completion(messages, max_retries=1)
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_json_decode_error(self, mock_post):
        """Test chat completion with JSON decode error"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(RuntimeError, match="Invalid JSON response"):
            await provider.chat_completion(messages, max_retries=1)
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_unexpected_response_format(self, mock_post):
        """Test chat completion with unexpected response format"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"unexpected": "format"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(RuntimeError, match="Unexpected response format"):
            await provider.chat_completion(messages)
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_generic_exception(self, mock_post):
        """Test chat completion with generic exception"""
        mock_post.side_effect = Exception("Unexpected error")
        
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(RuntimeError, match="Unexpected error"):
            await provider.chat_completion(messages, max_retries=1)
    
    @patch('aiohttp.ClientSession.get')
    @pytest.mark.asyncio
    async def test_is_available_async_success(self, mock_get):
        """Test async availability check success"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        is_available = await provider.is_available_async()
        
        assert is_available is True
    
    @patch('aiohttp.ClientSession.get')
    @pytest.mark.asyncio
    async def test_is_available_async_failure(self, mock_get):
        """Test async availability check failure"""
        mock_get.side_effect = Exception("Connection failed")
        
        provider = OllamaProvider("test-model")
        is_available = await provider.is_available_async()
        
        assert is_available is False
    
    @patch('requests.get')
    @patch('asyncio.get_event_loop')
    def test_is_available_sync_with_requests(self, mock_get_loop, mock_requests_get):
        """Test sync availability check using requests fallback"""
        # Mock running event loop
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_get_loop.return_value = mock_loop
        
        # Mock successful requests call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        is_available = provider.is_available()
        
        assert is_available is True
    
    @patch('aiohttp.ClientSession.get')
    @pytest.mark.asyncio
    async def test_get_available_models_async(self, mock_get):
        """Test getting available models async"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "codellama"},
                {"name": "qwen3-coder:30b"}
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        models = await OllamaProvider.get_available_models_async()
        
        assert "llama2" in models
        assert "codellama" in models
        assert "qwen3-coder:30b" in models
    
    @patch('aiohttp.ClientSession.get')
    @pytest.mark.asyncio
    async def test_get_available_models_async_fallback(self, mock_get):
        """Test getting available models with fallback to defaults"""
        mock_get.side_effect = Exception("API not available")
        
        models = await OllamaProvider.get_available_models_async()
        
        # Should return fallback list
        assert "codellama" in models
        assert "llama2" in models
        assert "mistral" in models
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_pull_model_async_success(self, mock_post):
        """Test pulling model async success"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        success = await provider.pull_model_async("new-model")
        
        assert success is True
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_pull_model_async_failure(self, mock_post):
        """Test pulling model async failure"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_post.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        success = await provider.pull_model_async("nonexistent-model")
        
        assert success is False
    
    @patch('aiohttp.ClientSession.get')
    @pytest.mark.asyncio
    async def test_list_running_models_async(self, mock_get):
        """Test listing running models async"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2", "size": "7B"},
                {"name": "codellama", "size": "13B"}
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        provider = OllamaProvider("test-model")
        models = await provider.list_running_models_async()
        
        assert len(models) == 2
        assert models[0]["name"] == "llama2"


class TestRetryLogic:
    """Test retry logic behavior"""
    
    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, mock_sleep):
        """Test that retry delay increases exponentially"""
        provider = OllamaProvider("test-model")
        
        # Mock connection errors that trigger retries
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientConnectorError(
                connection_key=Mock(),
                os_error=Exception("Connection refused")
            )
            
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(RuntimeError):
                await provider.chat_completion(messages, max_retries=3, retry_delay=1)
            
            # Verify exponential backoff: sleep(1), sleep(2), sleep(3)
            expected_calls = [Mock(call_args[0][0]) for call_args in mock_sleep.call_args_list]
            assert len(expected_calls) == 3
            
            # Check that delays increase
            delays = [call.call_args[0][0] for call in mock_sleep.call_args_list]
            assert delays[0] == 1  # 1 * 1
            assert delays[1] == 2  # 1 * 2
            assert delays[2] == 3  # 1 * 3
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_retry_only_retryable_errors(self, mock_post):
        """Test that only retryable errors trigger retries"""
        provider = OllamaProvider("test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        # 400 errors should not retry
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="Ollama API error 400"):
            await provider.chat_completion(messages, max_retries=3)
        
        # Should only be called once (no retries)
        assert mock_post.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__])
