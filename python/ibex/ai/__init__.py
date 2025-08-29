"""
IBEX AI Module - Multi-provider LLM support

This module provides unified interfaces for OpenAI, Anthropic Claude, and Ollama models.
Enhanced with file content access and deep analysis capabilities.
"""

from typing import Optional, Dict, Any, List
import os
from pathlib import Path
from abc import ABC, abstractmethod
import json
from .config import ConfigManager, ProviderType, ProviderConfig

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
    """Unified AI manager for multiple LLM providers with configuration management"""

    def __init__(self, provider: str = None, model: str = None, api_key: Optional[str] = None, project_root: Optional[str] = None, config_manager: Optional[ConfigManager] = None):
        self.project_root = Path(project_root or Path.cwd())
        self.config_manager = config_manager or ConfigManager(project_root=str(self.project_root))
        
        # Update config from environment
        self.config_manager.update_from_environment()
        
        # Load configuration
        self.config = self.config_manager.load_config()
        
        # Determine provider and model
        if provider:
            try:
                self.provider_type = ProviderType(provider)
            except ValueError:
                raise ValueError(f"Unsupported provider: {provider}")
        else:
            self.provider_type = self.config.default_provider
            
        self.provider_config = self.config.providers.get(self.provider_type)
        if not self.provider_config:
            raise ValueError(f"No configuration found for provider: {self.provider_type.value}")
            
        # Override with provided parameters
        if model:
            self.provider_config.model = model
        if api_key:
            self.provider_config.api_key = api_key
            
        self._provider_instance = None
        self._file_cache = {}  # Cache for file contents
        self._setup_provider()

    @property
    def provider(self) -> str:
        """Get provider name for backward compatibility"""
        return self.provider_type.value
    
    @property
    def model(self) -> str:
        """Get model name"""
        return self.provider_config.model

    def _setup_provider(self):
        """Setup the appropriate provider using configuration"""
        try:
            if not self.provider_config.enabled:
                raise RuntimeError(f"Provider {self.provider} is disabled in configuration")
                
            if self.provider_type == ProviderType.OPENAI:
                from .providers.openai_provider import OpenAIProvider
                self._provider_instance = OpenAIProvider(
                    self.provider_config.model, 
                    self.provider_config.api_key
                )
            elif self.provider_type == ProviderType.CLAUDE:
                from .providers.anthropic_provider import ClaudeProvider
                self._provider_instance = ClaudeProvider(
                    self.provider_config.model, 
                    self.provider_config.api_key
                )
            elif self.provider_type == ProviderType.OLLAMA:
                from .providers.ollama_provider import OllamaProvider
                self._provider_instance = OllamaProvider(
                    self.provider_config.model,
                    base_url=self.provider_config.base_url or "http://localhost:11434"
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except ImportError as e:
            raise ImportError(f"Provider {self.provider} dependencies not installed: {e}")

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion with configuration-based parameters"""
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")
            
        # Use configuration defaults, allow override via kwargs
        chat_kwargs = {
            'max_tokens': kwargs.get('max_tokens', self.provider_config.max_tokens),
            'temperature': kwargs.get('temperature', self.provider_config.temperature),
            'max_retries': kwargs.get('max_retries', self.provider_config.max_retries),
            'retry_delay': kwargs.get('retry_delay', self.provider_config.retry_delay)
        }
        
        return await self._provider_instance.chat_completion(messages, **chat_kwargs)

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

    def validate_config(self) -> tuple[bool, List[str]]:
        """Validate current configuration"""
        if not self._provider_instance:
            return False, ["Provider not initialized"]

        if not self._provider_instance.is_available():
            return False, [f"{self.provider} client not available"]

        # Use configuration manager validation
        is_valid, issues = self.config_manager.validate_config()
        return is_valid, issues
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration"""
        return {
            'provider': self.provider,
            'model': self.model,
            'enabled': self.provider_config.enabled,
            'available': self.is_available(),
            'max_tokens': self.provider_config.max_tokens,
            'temperature': self.provider_config.temperature,
            'timeout': self.provider_config.timeout,
            'max_retries': self.provider_config.max_retries,
            'base_url': getattr(self.provider_config, 'base_url', None),
            'has_api_key': bool(self.provider_config.api_key)
        }
    
    def switch_provider(self, provider_type: ProviderType, save_config: bool = False) -> bool:
        """Switch to a different provider"""
        try:
            new_config = self.config.providers.get(provider_type)
            if not new_config:
                return False
                
            if not new_config.enabled:
                return False
                
            # Update current configuration
            self.provider_type = provider_type
            self.provider_config = new_config
            
            # Setup new provider
            self._setup_provider()
            
            # Update default in config
            if save_config:
                self.config.default_provider = provider_type
                self.config_manager.save_config(self.config)
                
            return True
            
        except Exception as e:
            print(f"Failed to switch provider: {e}")
            return False
    
    def list_available_providers(self) -> List[Dict[str, Any]]:
        """List all available providers with their status"""
        available = []
        for provider_type in ProviderType:
            config = self.config.providers.get(provider_type)
            if config:
                # Try to create a test instance to check availability
                test_available = False
                try:
                    if provider_type == ProviderType.OLLAMA:
                        from .providers.ollama_provider import OllamaProvider
                        test_instance = OllamaProvider(config.model, base_url=config.base_url)
                        test_available = test_instance.is_available()
                    elif provider_type == ProviderType.OPENAI and config.api_key:
                        from .providers.openai_provider import OpenAIProvider
                        test_instance = OpenAIProvider(config.model, config.api_key)
                        test_available = test_instance.is_available()
                    elif provider_type == ProviderType.CLAUDE and config.api_key:
                        from .providers.anthropic_provider import ClaudeProvider
                        test_instance = ClaudeProvider(config.model, config.api_key)
                        test_available = test_instance.is_available()
                except Exception:
                    test_available = False
                    
                available.append({
                    'provider': provider_type.value,
                    'model': config.model,
                    'enabled': config.enabled,
                    'available': test_available,
                    'is_current': provider_type == self.provider_type,
                    'has_api_key': bool(config.api_key)
                })
                
        return available

    def read_file_content(self, file_path: str, max_lines: int = 100) -> str:
        """Read file content with line limiting for context"""
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return f"File not found: {file_path}"

            if str(full_path) in self._file_cache:
                return self._file_cache[str(full_path)]

            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) > max_lines:
                content = f"File: {file_path} ({len(lines)} lines total, showing first {max_lines})\n"
                content += "".join(lines[:max_lines])
                content += f"\n... ({len(lines) - max_lines} more lines)"
            else:
                content = f"File: {file_path} ({len(lines)} lines)\n"
                content += "".join(lines)

            # Cache the content
            self._file_cache[str(full_path)] = content
            return content

        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"

    def get_file_diff(self, file_path: str) -> str:
        """Get git diff for a file"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'diff', 'HEAD', '--', file_path],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return f"Git diff for {file_path}:\n{result.stdout}"
            else:
                return f"No changes in git diff for {file_path}"
        except Exception as e:
            return f"Error getting git diff for {file_path}: {str(e)}"

    def create_enhanced_context(self, files_changed: List[str], analysis_type: str = "general") -> str:
        """Create enhanced context with file contents and metadata"""
        context = f"Project: {self.project_root.name}\n"
        context += f"Files Changed: {len(files_changed)}\n"
        context += f"Analysis Type: {analysis_type}\n\n"

        # Add file metadata
        for file_path in files_changed[:5]:  # Limit to 5 files for context
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    context += f"File: {file_path}\n"
                    context += f"  - Lines: {len(lines)}\n"
                    context += f"  - Size: {full_path.stat().st_size} bytes\n"
                    if len(lines) <= 50:  # Include small files entirely
                        context += f"  - Content:\n{''.join(lines)}\n"
                    else:
                        context += f"  - Preview (first 10 lines):\n{''.join(lines[:10])}\n"
                except Exception as e:
                    context += f"  - Error reading: {e}\n"
            context += "\n"

        return context

    def create_system_prompt(self, analysis_type: str = "general", include_file_access: bool = True) -> str:
        """Create comprehensive system prompt with capabilities"""
        base_prompt = f"""You are an expert software engineer and code reviewer analyzing the IBEX project.

IBEX is an intelligent development companion that:
- Tracks file changes and creates meaningful commits
- Provides AI-powered code analysis and feedback
- Supports multiple AI providers (OpenAI, Claude, Ollama)
- Monitors its own development and improvements

Current Analysis Type: {analysis_type}
"""

        if include_file_access:
            base_prompt += """
You have access to read file contents and analyze code changes. When you need more context, you can:
1. Request specific files to be read using the available context
2. Ask for git diffs to understand what changed
3. Examine code structure and patterns

Available capabilities:
- File content reading (with line limits for large files)
- Git diff analysis
- Code quality assessment
- Documentation review
- Testing recommendations
- Performance analysis

Always provide specific, actionable feedback based on the actual code and changes.
"""

        return base_prompt

    async def analyze_with_context(self, files_changed: List[str], analysis_type: str = "contribution",
                                  custom_prompt: str = "", max_tokens: int = 4096) -> str:
        """Enhanced analysis with full context and file access"""
        try:
            # Create enhanced context
            context = self.create_enhanced_context(files_changed, analysis_type)

            # Create system prompt
            system_prompt = self.create_system_prompt(analysis_type)

            # Build analysis prompt
            analysis_prompt = f"""
{context}

Please provide a comprehensive analysis of these changes:

{custom_prompt}

Focus on:
- Code quality and best practices
- Potential bugs or issues
- Documentation and comments
- Testing requirements
- Performance implications
- Security considerations
- Overall contribution quality

Provide specific, actionable feedback that helps improve the codebase.
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ]

            # Use enhanced token limits for deeper analysis
            response = await self.chat(messages, max_tokens=max_tokens, temperature=0.3)
            return response

        except Exception as e:
            return f"Error in enhanced analysis: {str(e)}"

    async def chat_with_context(self, user_message: str, conversation_history: List[Dict] = None,
                               include_project_context: bool = True) -> str:
        """Enhanced chat with project context awareness and automatic file access"""
        try:
            # Pre-load relevant context based on user message
            context_content = await self._get_relevant_context(user_message)
            
            system_prompt = self.create_system_prompt("chat", include_file_access=True)

            if include_project_context:
                context_info = f"""
Current project: {self.project_root.name}
Working directory: {self.project_root}
AI Provider: {self.provider}
AI Model: {self.model}

PROJECT CONTEXT:
{context_content}

You can help with:
- Code analysis and review (with actual file access)
- Development workflow optimization  
- AI provider configuration
- Git workflow and commits
- Project documentation
- Testing strategies
- Performance optimization
"""

                system_prompt += context_info

            messages = [{"role": "system", "content": system_prompt}]

            if conversation_history:
                messages.extend(conversation_history[-10:])  # Keep last 10 messages for context

            messages.append({"role": "user", "content": user_message})

            response = await self.chat(messages, temperature=0.7)
            return response

        except Exception as e:
            return f"Error in contextual chat: {str(e)}"

    async def _get_relevant_context(self, user_message: str) -> str:
        """Get comprehensive project context based on user message"""
        context_parts = []
        lower_msg = user_message.lower()

        try:
            # Always include comprehensive project structure
            context_parts.append("=== PROJECT OVERVIEW ===")
            context_parts.append(f"Project: {self.project_root.name}")
            context_parts.append(f"Root Directory: {self.project_root}")
            context_parts.append("")

            # Get full directory tree structure
            context_parts.append("=== FULL PROJECT STRUCTURE ===")
            tree_structure = self._get_directory_tree()
            context_parts.append(tree_structure)

            # Categorize files by type
            context_parts.append("\n=== FILE CATEGORIES ===")
            file_categories = self._categorize_files()
            for category, files in file_categories.items():
                if files:
                    context_parts.append(f"{category.upper()}:")
                    for file in sorted(files)[:5]:  # Show up to 5 per category
                        context_parts.append(f"  • {file}")
                    if len(files) > 5:
                        context_parts.append(f"  • ... and {len(files) - 5} more {category.lower()} files")
                    context_parts.append("")

            # Always include git status and recent activity
            context_parts.append("=== GIT STATUS & RECENT ACTIVITY ===")
            try:
                import subprocess

                # Get git status
                result = subprocess.run(['git', 'status', '--porcelain'],
                                      cwd=self.project_root, capture_output=True, text=True)
                context_parts.append("Current Status:")
                if result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        context_parts.append(f"  {line}")
                else:
                    context_parts.append("  Working directory clean")

                # Get recent commits
                result = subprocess.run(['git', 'log', '--oneline', '-5'],
                                      cwd=self.project_root, capture_output=True, text=True)
                if result.stdout.strip():
                    context_parts.append("\nRecent Commits:")
                    for line in result.stdout.strip().split('\n'):
                        context_parts.append(f"  {line}")

                # Get current branch
                result = subprocess.run(['git', 'branch', '--show-current'],
                                      cwd=self.project_root, capture_output=True, text=True)
                if result.stdout.strip():
                    context_parts.append(f"\nCurrent Branch: {result.stdout.strip()}")

            except Exception as e:
                context_parts.append(f"Git info unavailable: {e}")

            # Intelligent content inclusion based on query type
            content_included = await self._get_relevant_file_content(user_message)
            if content_included:
                context_parts.append("\n=== RELEVANT FILE CONTENT ===")
                context_parts.extend(content_included)

            # Add project metadata
            context_parts.append("\n=== PROJECT METADATA ===")
            metadata = self._get_project_metadata()
            context_parts.extend(metadata)

        except Exception as e:
            context_parts.append(f"Error gathering context: {e}")
            import traceback
            context_parts.append(traceback.format_exc())

        return "\n".join(context_parts)

    def _get_directory_tree(self, max_depth: int = 4) -> str:
        """Generate a comprehensive directory tree"""
        tree_lines = []

        def add_directory(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return

            try:
                items = sorted(path.iterdir())
            except PermissionError:
                return

            for i, item in enumerate(items):
                if item.name.startswith('.') and item.name != '.ibex':
                    continue  # Skip hidden files except .ibex

                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{connector}{item.name}")

                if item.is_dir() and depth < max_depth:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    add_directory(item, new_prefix, depth + 1)

        add_directory(self.project_root)
        return "\n".join(tree_lines)

    def _categorize_files(self) -> dict:
        """Categorize all files in the project"""
        categories = {
            "Python Code": [],
            "Configuration": [],
            "Documentation": [],
            "Tests": [],
            "Scripts": [],
            "Other": []
        }

        try:
            for file_path in self.project_root.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    rel_path = str(file_path.relative_to(self.project_root))

                    if file_path.suffix == '.py':
                        if 'test' in rel_path.lower() or rel_path.startswith('tests/'):
                            categories["Tests"].append(rel_path)
                        else:
                            categories["Python Code"].append(rel_path)
                    elif file_path.suffix in ['.yml', '.yaml', '.json', '.toml', '.cfg', '.ini']:
                        categories["Configuration"].append(rel_path)
                    elif file_path.suffix in ['.md', '.txt', '.rst']:
                        categories["Documentation"].append(rel_path)
                    elif file_path.suffix in ['.sh', '.bat', '.ps1'] or file_path.name in ['Makefile']:
                        categories["Scripts"].append(rel_path)
                    else:
                        categories["Other"].append(rel_path)
        except Exception as e:
            categories["Other"].append(f"Error categorizing files: {e}")

        return categories

    async def _get_relevant_file_content(self, user_message: str) -> list:
        """Get relevant file content based on user query"""
        content_parts = []
        lower_msg = user_message.lower()

        # Define query patterns and corresponding files
        query_patterns = {
            'readme|docs|documentation|what does|what is|about': ['README.md'],
            'config|setup|install|requirements|dependencies': [
                'python/requirements.txt', 'setup.py', 'pyproject.toml'
            ],
            'core|main|architecture': [
                'python/ibex/core.py', 'python/ibex/__init__.py'
            ],
            'ai|llm|model|chat': [
                'python/ibex/ai/__init__.py', 'python/ibex/llm.py'
            ],
            'git|version|commit': [
                'python/ibex/git_integration.py'
            ],
            'cli|command|interface': [
                'python/ibex/cli.py', 'run_ibex.py'
            ],
            'test|testing': [
                'tests/__init__.py', 'python/ibex/ai/example.py'
            ]
        }

        relevant_files = []
        for pattern, files in query_patterns.items():
            if any(word in lower_msg for word in pattern.split('|')):
                relevant_files.extend(files)

        # Remove duplicates and limit to prevent context overflow
        relevant_files = list(dict.fromkeys(relevant_files))[:3]

        for file_path in relevant_files:
            try:
                content = self.read_file_content(file_path, max_lines=50)
                if content and not content.startswith("File not found"):
                    content_parts.append(f"📄 {file_path}:")
                    content_parts.append(content)
                    content_parts.append("")  # Add spacing
            except Exception as e:
                content_parts.append(f"Error reading {file_path}: {e}")

        return content_parts

    def _get_project_metadata(self) -> list:
        """Get project metadata"""
        metadata = []

        try:
            # File counts
            total_files = sum(1 for _ in self.project_root.rglob("*") if _.is_file())
            python_files = sum(1 for _ in self.project_root.rglob("*.py"))
            metadata.append(f"Total Files: {total_files}")
            metadata.append(f"Python Files: {python_files}")

            # Get project size
            total_size = sum(f.stat().st_size for f in self.project_root.rglob("*") if f.is_file())
            metadata.append(f"Project Size: {total_size:,} bytes")

            # AI provider status
            metadata.append(f"AI Provider: {self.provider}")
            metadata.append(f"AI Model: {self.model}")
            metadata.append(f"Provider Available: {'Yes' if self.is_available() else 'No'}")

        except Exception as e:
            metadata.append(f"Error getting metadata: {e}")

        return metadata
