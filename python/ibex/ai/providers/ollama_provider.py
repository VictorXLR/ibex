"""
Ollama provider implementation using direct HTTP API
"""

import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from .base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    """Ollama local LLM provider using direct HTTP API"""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: str = "http://localhost:11434"):
        super().__init__(model, api_key)
        self.base_url = base_url
        self.setup_client()

    def setup_client(self):
        """Setup base URL for Ollama API"""
        # aiohttp session will be created per request
        pass

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion using Ollama HTTP API with retry logic"""
        max_retries = kwargs.get('max_retries', 3)
        retry_delay = kwargs.get('retry_delay', 1)
        
        for attempt in range(max_retries):
            try:
                # Convert messages to Ollama format
                ollama_messages = []
                system_message = None

                for msg in messages:
                    if msg['role'] == 'system':
                        system_message = msg['content']
                    elif msg['role'] == 'user':
                        ollama_messages.append({"role": "user", "content": msg['content']})
                    elif msg['role'] == 'assistant':
                        ollama_messages.append({"role": "assistant", "content": msg['content']})

                # Prepare request payload
                payload = {
                    "model": self.model,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get('temperature', 0.7),
                        "num_predict": kwargs.get('max_tokens', 1024)
                    }
                }

                # Add system message if present
                if system_message:
                    payload["messages"].insert(0, {"role": "system", "content": system_message})

                # Make async API request
                timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            error_msg = f"Ollama API error {response.status}: {error_text}"
                            
                            # Check if it's a retryable error
                            if response.status in [500, 502, 503, 504] and attempt < max_retries - 1:
                                print(f"Retryable error on attempt {attempt + 1}: {error_msg}")
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                            else:
                                raise RuntimeError(error_msg)

                        result = await response.json()

                        if 'message' in result and 'content' in result['message']:
                            return result['message']['content']
                        else:
                            raise RuntimeError(f"Unexpected response format: {result}")

            except aiohttp.ClientConnectorError as e:
                error_msg = f"Connection failed to Ollama at {self.base_url}: {str(e)}"
                if attempt < max_retries - 1:
                    print(f"Connection error on attempt {attempt + 1}: {error_msg}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise RuntimeError(f"{error_msg} - Check if Ollama is running")
                    
            except asyncio.TimeoutError as e:
                error_msg = f"Request timeout to Ollama API: {str(e)}"
                if attempt < max_retries - 1:
                    print(f"Timeout on attempt {attempt + 1}: {error_msg}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise RuntimeError(f"{error_msg} - Model: {self.model}")
                    
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON response from Ollama API: {str(e)}"
                if attempt < max_retries - 1:
                    print(f"JSON decode error on attempt {attempt + 1}: {error_msg}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise RuntimeError(error_msg)
                    
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                if attempt < max_retries - 1:
                    print(f"Unexpected error on attempt {attempt + 1}: {error_msg}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise RuntimeError(f"{error_msg} - Model: {self.model}, URL: {self.base_url}")
        
        # This should never be reached, but just in case
        raise RuntimeError(f"All {max_retries} attempts failed for Ollama API request")

    async def is_available_async(self) -> bool:
        """Check if Ollama API is available (async version)"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except:
            return False

    def is_available(self) -> bool:
        """Check if Ollama API is available (sync version)"""
        import asyncio
        try:
            # Try to get the current event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we need to use a different approach
                    import concurrent.futures
                    import aiohttp

                    def check_sync():
                        timeout = aiohttp.ClientTimeout(total=5)
                        try:
                            import requests
                            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                            return response.status_code == 200
                        except:
                            return False

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(check_sync)
                        return future.result()
                else:
                    return loop.run_until_complete(self.is_available_async())
            except RuntimeError:
                # No event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.is_available_async())
                    return result
                finally:
                    loop.close()
        except Exception as e:
            print(f"Ollama availability check failed: {e}")
            return False

    def validate_api_key(self) -> bool:
        """Ollama doesn't require API key"""
        return True

    @classmethod
    async def get_available_models_async(cls, base_url: str = "http://localhost:11434") -> List[str]:
        """Get list of available Ollama models via API (async)"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model['name'] for model in data.get('models', [])]
        except:
            pass

        # Fallback to common models if API is not available
        return [
            'codellama',
            'llama2',
            'mistral',
            'codellama:7b',
            'codellama:13b',
            'codellama:34b',
            'qwen3:30b',
            'qwen3-coder:30b',
            'deepseek-r1:32b'
        ]

    @classmethod
    def get_available_models(cls, base_url: str = "http://localhost:11434") -> List[str]:
        """Get list of available Ollama models via API (sync)"""
        try:
            import asyncio
            return asyncio.run(cls.get_available_models_async(base_url))
        except:
            # Fallback to common models if async fails
            return [
                'codellama',
                'llama2',
                'mistral',
                'codellama:7b',
                'codellama:13b',
                'codellama:34b',
                'qwen3:30b',
                'qwen3-coder:30b',
                'deepseek-r1:32b'
            ]

    async def pull_model_async(self, model_name: str) -> bool:
        """Pull a model from Ollama registry via API (async)"""
        try:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for model download
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Failed to pull model {model_name}: {e}")
            return False

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry via API (sync)"""
        try:
            import asyncio
            return asyncio.run(self.pull_model_async(model_name))
        except Exception as e:
            print(f"Failed to pull model {model_name}: {e}")
            return False

    async def list_running_models_async(self) -> List[Dict[str, Any]]:
        """List currently running models (async)"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/api/ps") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('models', [])
        except:
            pass
        return []

    def list_running_models(self) -> List[Dict[str, Any]]:
        """List currently running models (sync)"""
        try:
            import asyncio
            return asyncio.run(self.list_running_models_async())
        except:
            return []
