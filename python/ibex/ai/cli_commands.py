"""
CLI commands for IBEX AI configuration management
"""

import asyncio
import json
from typing import Optional
from .config import ConfigManager, ProviderType, get_config_manager
from . import AIManager

def cmd_config_init(project_root: Optional[str] = None):
    """Initialize AI configuration"""
    config_manager = get_config_manager(project_root)
    
    print("🔧 Initializing IBEX AI Configuration...")
    
    # Load/create default config
    config = config_manager.load_config()
    
    # Update from environment
    config_manager.update_from_environment()
    
    # Validate configuration
    is_valid, issues = config_manager.validate_config()
    
    print(f"Configuration loaded from: {config_manager.config_path}")
    print(f"Default provider: {config.default_provider.value}")
    
    if is_valid:
        print("✅ Configuration is valid")
    else:
        print("⚠️ Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
            
    # Save configuration
    if config_manager.save_config():
        print(f"✅ Configuration saved to {config_manager.config_path}")
    else:
        print("❌ Failed to save configuration")

def cmd_config_show(project_root: Optional[str] = None):
    """Show current AI configuration"""
    config_manager = get_config_manager(project_root)
    config = config_manager.load_config()
    
    print("🔍 Current IBEX AI Configuration:")
    print(f"Default Provider: {config.default_provider.value}")
    print(f"Configuration File: {config_manager.config_path}")
    
    print("\n📊 Provider Status:")
    for provider_type, provider_config in config.providers.items():
        status = "✅ Enabled" if provider_config.enabled else "❌ Disabled"
        api_key_status = "🔑 Has API Key" if provider_config.api_key else "🔓 No API Key"
        
        print(f"  {provider_type.value}:")
        print(f"    Status: {status}")
        print(f"    Model: {provider_config.model}")
        if provider_type in [ProviderType.OPENAI, ProviderType.CLAUDE]:
            print(f"    API Key: {api_key_status}")
        if hasattr(provider_config, 'base_url') and provider_config.base_url:
            print(f"    URL: {provider_config.base_url}")
        print(f"    Max Tokens: {provider_config.max_tokens}")
        print(f"    Temperature: {provider_config.temperature}")
        print()

async def cmd_config_test(project_root: Optional[str] = None):
    """Test AI provider configurations"""
    print("🧪 Testing AI Provider Configurations...")
    
    try:
        ai_manager = AIManager(project_root=project_root)
        
        # Test current provider
        print(f"\n🔄 Testing current provider: {ai_manager.provider}")
        
        if ai_manager.is_available():
            print("✅ Provider is available")
            
            # Test basic functionality
            try:
                test_messages = [
                    {"role": "user", "content": "Hello! Please respond with 'AI test successful' to confirm functionality."}
                ]
                
                response = await ai_manager.chat(test_messages, max_tokens=50)
                if response and len(response.strip()) > 0:
                    print("✅ Basic chat functionality working")
                    print(f"Response: {response[:100]}...")
                else:
                    print("⚠️ Empty response from provider")
                    
            except Exception as e:
                print(f"❌ Chat test failed: {e}")
        else:
            print("❌ Provider is not available")
            
        # Test all configured providers
        print("\n🔍 Testing all configured providers:")
        available_providers = ai_manager.list_available_providers()
        
        for provider_info in available_providers:
            provider_name = provider_info['provider']
            is_available = provider_info['available']
            is_enabled = provider_info['enabled']
            
            status_icon = "✅" if is_available and is_enabled else "❌"
            print(f"  {status_icon} {provider_name}: {provider_info['model']}")
            
            if not is_enabled:
                print(f"    Status: Disabled")
            elif not is_available:
                print(f"    Status: Enabled but not available")
            else:
                print(f"    Status: Ready")
                
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")

def cmd_config_sample():
    """Generate sample configuration file"""
    config_manager = ConfigManager()
    sample = config_manager.create_sample_config()
    
    print("📝 Sample IBEX AI Configuration:")
    print("=" * 50)
    print(sample)
    print("=" * 50)
    print(f"\nSave this to: {config_manager.config_path}")
    print("Then set your API keys via environment variables:")
    print("  export OPENAI_API_KEY='your-openai-key'")
    print("  export ANTHROPIC_API_KEY='your-claude-key'")

def cmd_config_validate(project_root: Optional[str] = None):
    """Validate AI configuration"""
    config_manager = get_config_manager(project_root)
    
    print("🔍 Validating IBEX AI Configuration...")
    
    # Update from environment first
    config_manager.update_from_environment()
    
    is_valid, issues = config_manager.validate_config()
    
    if is_valid:
        print("✅ Configuration is valid!")
        
        # Show summary
        config = config_manager.load_config()
        available_providers = [
            provider_type.value for provider_type in config_manager.get_available_providers()
        ]
        
        if available_providers:
            print(f"Available providers: {', '.join(available_providers)}")
        else:
            print("⚠️ No providers are currently available")
            
    else:
        print("❌ Configuration validation failed:")
        for issue in issues:
            print(f"  - {issue}")
            
        print("\n💡 Suggestions:")
        print("  1. Run 'ibex ai config init' to create default configuration")
        print("  2. Set required environment variables (API keys)")
        print("  3. Check provider availability (e.g., Ollama running)")

def cmd_config_switch(provider: str, project_root: Optional[str] = None):
    """Switch default AI provider"""
    try:
        provider_type = ProviderType(provider)
    except ValueError:
        print(f"❌ Unknown provider: {provider}")
        print(f"Available providers: {[p.value for p in ProviderType]}")
        return
        
    config_manager = get_config_manager(project_root)
    config = config_manager.load_config()
    
    if provider_type not in config.providers:
        print(f"❌ Provider {provider} not configured")
        return
        
    if not config.providers[provider_type].enabled:
        print(f"❌ Provider {provider} is disabled")
        return
    
    # Update default provider
    config.default_provider = provider_type
    
    if config_manager.save_config(config):
        print(f"✅ Default provider switched to: {provider}")
    else:
        print(f"❌ Failed to save configuration")

# Command mapping for CLI integration
AI_COMMANDS = {
    'config-init': cmd_config_init,
    'config-show': cmd_config_show,
    'config-test': lambda *args, **kwargs: asyncio.run(cmd_config_test(*args, **kwargs)),
    'config-sample': cmd_config_sample,
    'config-validate': cmd_config_validate,
    'config-switch': cmd_config_switch,
}
