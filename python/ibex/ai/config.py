"""
IBEX AI Configuration Management
Handles configuration for AI providers, models, and API endpoints
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

class ProviderType(Enum):
    """Supported AI provider types"""
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"

@dataclass
class ProviderConfig:
    """Configuration for an AI provider"""
    provider_type: ProviderType
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 300
    max_retries: int = 3
    retry_delay: int = 1
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['provider_type'] = self.provider_type.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProviderConfig':
        """Create from dictionary"""
        data = data.copy()
        if 'provider_type' in data:
            data['provider_type'] = ProviderType(data['provider_type'])
        return cls(**data)

@dataclass
class AIConfig:
    """Complete AI configuration"""
    default_provider: ProviderType = ProviderType.OLLAMA
    providers: Dict[ProviderType, ProviderConfig] = None
    fallback_order: List[ProviderType] = None
    analysis_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.providers is None:
            self.providers = {}
        if self.fallback_order is None:
            self.fallback_order = [ProviderType.OLLAMA, ProviderType.OPENAI, ProviderType.CLAUDE]
        if self.analysis_settings is None:
            self.analysis_settings = {
                'max_file_size': 100000,  # 100KB
                'max_files_per_analysis': 10,
                'include_git_diff': True,
                'include_file_content': True,
                'context_window_lines': 50
            }

class ConfigManager:
    """Manages AI configuration for IBEX"""
    
    def __init__(self, config_path: Optional[str] = None, project_root: Optional[str] = None):
        self.project_root = Path(project_root or Path.cwd())
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self._config: Optional[AIConfig] = None
        self._config_loaded = False
        
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path"""
        # Try project-specific config first
        project_config = self.project_root / '.ibex' / 'ai_config.yaml'
        if project_config.exists():
            return project_config
            
        # Fall back to global config
        home_config = Path.home() / '.ibex' / 'ai_config.yaml'
        return home_config
    
    def load_config(self) -> AIConfig:
        """Load configuration from file"""
        if self._config_loaded and self._config:
            return self._config
            
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                
                self._config = self._parse_config_data(data)
            else:
                # Create default configuration
                self._config = self._create_default_config()
                
        except Exception as e:
            print(f"Warning: Error loading config from {self.config_path}: {e}")
            self._config = self._create_default_config()
            
        self._config_loaded = True
        return self._config
    
    def _parse_config_data(self, data: Dict[str, Any]) -> AIConfig:
        """Parse configuration data from file"""
        config = AIConfig()
        
        # Parse default provider
        if 'default_provider' in data:
            config.default_provider = ProviderType(data['default_provider'])
            
        # Parse providers
        if 'providers' in data:
            config.providers = {}
            for provider_name, provider_data in data['providers'].items():
                provider_type = ProviderType(provider_name)
                provider_data['provider_type'] = provider_type
                config.providers[provider_type] = ProviderConfig.from_dict(provider_data)
                
        # Parse fallback order
        if 'fallback_order' in data:
            config.fallback_order = [ProviderType(p) for p in data['fallback_order']]
            
        # Parse analysis settings
        if 'analysis_settings' in data:
            config.analysis_settings.update(data['analysis_settings'])
            
        return config
    
    def _create_default_config(self) -> AIConfig:
        """Create default configuration"""
        config = AIConfig()
        
        # Create default provider configurations
        config.providers = {
            ProviderType.OLLAMA: ProviderConfig(
                provider_type=ProviderType.OLLAMA,
                model=os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b'),
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                max_tokens=8192,
                temperature=0.7
            ),
            ProviderType.OPENAI: ProviderConfig(
                provider_type=ProviderType.OPENAI,
                model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                api_key=os.getenv('OPENAI_API_KEY'),
                max_tokens=4096,
                temperature=0.3,
                enabled=bool(os.getenv('OPENAI_API_KEY'))
            ),
            ProviderType.CLAUDE: ProviderConfig(
                provider_type=ProviderType.CLAUDE,
                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229'),
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                max_tokens=4096,
                temperature=0.3,
                enabled=bool(os.getenv('ANTHROPIC_API_KEY'))
            )
        }
        
        # Set default provider based on what's available
        if config.providers[ProviderType.OPENAI].enabled:
            config.default_provider = ProviderType.OPENAI
        elif config.providers[ProviderType.CLAUDE].enabled:
            config.default_provider = ProviderType.CLAUDE
        else:
            config.default_provider = ProviderType.OLLAMA
            
        return config
    
    def save_config(self, config: Optional[AIConfig] = None) -> bool:
        """Save configuration to file"""
        if config is None:
            config = self._config
            
        if config is None:
            return False
            
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            data = {
                'default_provider': config.default_provider.value,
                'providers': {},
                'fallback_order': [p.value for p in config.fallback_order],
                'analysis_settings': config.analysis_settings
            }
            
            for provider_type, provider_config in config.providers.items():
                data['providers'][provider_type.value] = provider_config.to_dict()
                # Don't save sensitive API keys to file
                if 'api_key' in data['providers'][provider_type.value]:
                    data['providers'][provider_type.value]['api_key'] = None
            
            # Save to file
            with open(self.config_path, 'w') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.safe_dump(data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(data, f, indent=2)
                    
            print(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_provider_config(self, provider_type: ProviderType) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider"""
        config = self.load_config()
        return config.providers.get(provider_type)
    
    def set_provider_config(self, provider_type: ProviderType, provider_config: ProviderConfig):
        """Set configuration for a specific provider"""
        config = self.load_config()
        config.providers[provider_type] = provider_config
        self._config = config
    
    def get_available_providers(self) -> List[ProviderType]:
        """Get list of available/enabled providers"""
        config = self.load_config()
        available = []
        
        for provider_type, provider_config in config.providers.items():
            if provider_config.enabled:
                # Additional checks for provider availability
                if provider_type == ProviderType.OLLAMA:
                    # Ollama is available if enabled (local installation)
                    available.append(provider_type)
                elif provider_config.api_key:
                    # API providers need API keys
                    available.append(provider_type)
                    
        return available
    
    def get_default_provider(self) -> ProviderType:
        """Get the default provider"""
        config = self.load_config()
        return config.default_provider
    
    def set_default_provider(self, provider_type: ProviderType):
        """Set the default provider"""
        config = self.load_config()
        config.default_provider = provider_type
        self._config = config
    
    def validate_config(self) -> tuple[bool, List[str]]:
        """Validate the current configuration"""
        config = self.load_config()
        issues = []
        
        # Check if default provider is available
        default_config = config.providers.get(config.default_provider)
        if not default_config or not default_config.enabled:
            issues.append(f"Default provider {config.default_provider.value} is not enabled")
            
        # Check provider configurations
        for provider_type, provider_config in config.providers.items():
            if not provider_config.enabled:
                continue
                
            if provider_type in [ProviderType.OPENAI, ProviderType.CLAUDE]:
                if not provider_config.api_key:
                    api_key_env = 'OPENAI_API_KEY' if provider_type == ProviderType.OPENAI else 'ANTHROPIC_API_KEY'
                    if not os.getenv(api_key_env):
                        issues.append(f"{provider_type.value} is enabled but no API key found (check {api_key_env})")
                        
            if provider_config.max_tokens <= 0:
                issues.append(f"{provider_type.value} has invalid max_tokens setting")
                
            if not (0 <= provider_config.temperature <= 2):
                issues.append(f"{provider_type.value} has invalid temperature setting (should be 0-2)")
        
        return len(issues) == 0, issues
    
    def update_from_environment(self):
        """Update configuration from environment variables"""
        config = self.load_config()
        
        # Update API keys from environment
        for provider_type, provider_config in config.providers.items():
            if provider_type == ProviderType.OPENAI:
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    provider_config.api_key = api_key
                    provider_config.enabled = True
                    
            elif provider_type == ProviderType.CLAUDE:
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    provider_config.api_key = api_key
                    provider_config.enabled = True
                    
            elif provider_type == ProviderType.OLLAMA:
                base_url = os.getenv('OLLAMA_BASE_URL')
                if base_url:
                    provider_config.base_url = base_url
                    
        # Update models from environment
        openai_model = os.getenv('OPENAI_MODEL')
        if openai_model and ProviderType.OPENAI in config.providers:
            config.providers[ProviderType.OPENAI].model = openai_model
            
        claude_model = os.getenv('ANTHROPIC_MODEL')
        if claude_model and ProviderType.CLAUDE in config.providers:
            config.providers[ProviderType.CLAUDE].model = claude_model
            
        ollama_model = os.getenv('OLLAMA_MODEL')
        if ollama_model and ProviderType.OLLAMA in config.providers:
            config.providers[ProviderType.OLLAMA].model = ollama_model
            
        # Update default provider from environment
        default_provider = os.getenv('IBEX_AI_PROVIDER')
        if default_provider:
            try:
                config.default_provider = ProviderType(default_provider)
            except ValueError:
                pass
                
        self._config = config
    
    def create_sample_config(self) -> str:
        """Create a sample configuration file content"""
        sample_config = {
            'default_provider': 'ollama',
            'providers': {
                'ollama': {
                    'model': 'qwen3-coder:30b',
                    'base_url': 'http://localhost:11434',
                    'max_tokens': 8192,
                    'temperature': 0.3,
                    'timeout': 300,
                    'max_retries': 3,
                    'retry_delay': 1,
                    'enabled': True
                },
                'openai': {
                    'model': 'gpt-4',
                    'max_tokens': 4096,
                    'temperature': 0.3,
                    'timeout': 60,
                    'max_retries': 3,
                    'retry_delay': 1,
                    'enabled': False,
                    'api_key': None  # Set via OPENAI_API_KEY environment variable
                },
                'claude': {
                    'model': 'claude-3-sonnet-20240229',
                    'max_tokens': 4096,
                    'temperature': 0.3,
                    'timeout': 60,
                    'max_retries': 3,
                    'retry_delay': 1,
                    'enabled': False,
                    'api_key': None  # Set via ANTHROPIC_API_KEY environment variable
                }
            },
            'fallback_order': ['ollama', 'openai', 'claude'],
            'analysis_settings': {
                'max_file_size': 100000,
                'max_files_per_analysis': 10,
                'include_git_diff': True,
                'include_file_content': True,
                'context_window_lines': 50
            }
        }
        
        return yaml.safe_dump(sample_config, default_flow_style=False, indent=2)

# Global config manager instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager(project_root: Optional[str] = None) -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(project_root=project_root)
    return _config_manager

def reset_config_manager():
    """Reset global configuration manager (for testing)"""
    global _config_manager
    _config_manager = None
