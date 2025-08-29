"""
AI utility functions
"""

from typing import List, Dict, Any
import os

def create_commit_message_prompt(changes: List[Dict], intent: str) -> List[Dict[str, str]]:
    """Create a prompt for generating commit messages"""

    # Format changes for the prompt
    changes_text = ""
    for change in changes:
        changes_text += f"• {change.get('summary', 'Modified file')}\n"

    system_prompt = """You are a code analysis assistant that creates meaningful git commit messages.
Follow these guidelines:
- Keep the title under 50 characters
- Provide a detailed description of what changed and why
- Focus on the impact and purpose of the changes
- Use present tense for the title
- Be specific about what functionality was added/modified"""

    user_prompt = f"""Given these changes and the development intent: "{intent}"

Changes:
{changes_text}

Please provide a commit message in the following format:

Title: [Brief summary under 50 chars]
Description: [Detailed explanation of what changed and why]
Impact: [What this change accomplishes]

Commit message:"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def create_code_review_prompt(code: str, context: str = "") -> List[Dict[str, str]]:
    """Create a prompt for code review"""

    system_prompt = """You are an expert code reviewer. Analyze the provided code for:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security concerns
- Readability and maintainability"""

    user_prompt = f"""Please review the following code:

Context: {context}

Code:
```python
{code}
```

Provide your analysis focusing on:
1. Strengths of the code
2. Areas for improvement
3. Specific recommendations
4. Overall assessment"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def get_provider_config(provider: str) -> Dict[str, Any]:
    """Get configuration for a specific provider"""

    configs = {
        'openai': {
            'api_key_env': 'OPENAI_API_KEY',
            'default_model': 'gpt-4',
            'models': ['gpt-4', 'gpt-4-turbo-preview', 'gpt-3.5-turbo'],
            'requires_api_key': True
        },
        'claude': {
            'api_key_env': 'ANTHROPIC_API_KEY',
            'default_model': 'claude-3-sonnet-20240229',
            'models': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
            'requires_api_key': True
        },
        'ollama': {
            'api_key_env': None,
            'default_model': 'codellama',
            'models': ['codellama', 'llama2', 'mistral'],
            'requires_api_key': False
        }
    }

    return configs.get(provider, {})

def validate_environment(provider: str) -> tuple[bool, str]:
    """Validate environment for a provider"""

    config = get_provider_config(provider)
    if not config:
        return False, f"Unknown provider: {provider}"

    if config.get('requires_api_key'):
        api_key_env = config['api_key_env']
        if not os.getenv(api_key_env):
            return False, f"Environment variable {api_key_env} not set"

    return True, "Environment is valid"
