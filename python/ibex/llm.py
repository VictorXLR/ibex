from typing import List, Dict, Optional
import sqlite3
import json
from pathlib import Path
import os
from datetime import datetime
import difflib
from uuid import uuid4
from git import Repo
from .ai import AIManager

# Provider availability flags
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

class LLMManager:
    def __init__(self, path: str, provider: str = None, model: str = None):
        self.path = Path(path)
        self.db_path = self.path / '.ibex' / 'semantic.db'
        self._init_db()

        # Initialize repo
        try:
            self.repo = Repo(path)
        except:
            self.repo = None

        # Configure LLM provider using AIManager
        self.ai_manager = AIManager(provider, model)
        self.provider = self.ai_manager.provider
        self.model = self.ai_manager.model
        
    def _init_db(self):
        """Initialize SQLite database for semantic history"""
        # Ensure .ibex directory exists
        self.db_path.parent.mkdir(exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS semantic_changes
                    (id TEXT PRIMARY KEY, timestamp TEXT,
                     description TEXT, changes TEXT,
                     commit_hash TEXT, intent TEXT, provider TEXT, model TEXT)''')
        conn.commit()
        conn.close()



    def generate_diff(self, file_path: str) -> str:
        """Generate git-style diff for a file"""
        if not self.repo:
            return ""
        try:
            diff = self.repo.git.diff('HEAD', file_path, unified=3)
            return diff
        except:
            return ""

    async def analyze_changes(self, changes: List[Dict], intent: str) -> str:
        """Analyze changes using LLM to generate meaningful commit message"""
        if not changes:
            return "No changes to analyze"

        if not self.ai_manager.is_available():
            return f"LLM provider '{self.provider}' not available. Please install the required dependencies and set the appropriate API keys."

        diffs = []
        for change in changes:
            file_path = change['file']
            diff = self.generate_diff(file_path)
            if diff:
                diffs.append(f"File: {file_path}\n{diff}")

        if not diffs:
            return "No git diffs available for analysis"

        combined_diff = "\n\n".join(diffs)

        # Prepare prompt for LLM
        prompt = f"""Given these changes and the development intent: "{intent}",
        provide a detailed commit message following this format:

        Title: Short summary (max 50 chars)
        Description: Detailed explanation
        Impact: What changed and why

        Changes:
        {combined_diff}
        """

        try:
            messages = [
                {"role": "system", "content": "You are a code analysis assistant that creates meaningful git commit messages."},
                {"role": "user", "content": prompt}
            ]
            return await self.ai_manager.chat(messages)
        except Exception as e:
            print(f"LLM error: {e}")
            return f"Error analyzing changes: {str(e)}"

    def store_semantic_change(self, commit_hash: str, description: str, changes: List[Dict], intent: str):
        """Store semantic change information in SQLite"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO semantic_changes
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                 (str(uuid4()),
                  datetime.now().isoformat(),
                  description,
                  json.dumps(changes),
                  commit_hash,
                  intent,
                  self.provider,
                  self.model))
        conn.commit()
        conn.close()

    def get_semantic_history(self) -> List[Dict]:
        """Retrieve semantic history of changes"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM semantic_changes ORDER BY timestamp DESC")
        rows = c.fetchall()
        conn.close()

        return [{
            'id': row[0],
            'timestamp': row[1],
            'description': row[2],
            'changes': json.loads(row[3]),
            'commit_hash': row[4],
            'intent': row[5],
            'provider': row[6] if len(row) > 6 else 'unknown',
            'model': row[7] if len(row) > 7 else 'unknown'
        } for row in rows]

    def list_available_providers(self) -> List[str]:
        """List available LLM providers"""
        providers = []
        if HAS_OPENAI:
            providers.append('openai')
        if HAS_ANTHROPIC:
            providers.append('anthropic')
        if HAS_OLLAMA:
            providers.append('ollama')
        return providers

    def validate_configuration(self) -> tuple[bool, str]:
        """Validate LLM configuration"""
        if self.provider == 'openai':
            if not HAS_OPENAI:
                return False, "OpenAI library not installed"
            if not os.getenv('OPENAI_API_KEY'):
                return False, "OPENAI_API_KEY environment variable not set"
        elif self.provider == 'anthropic':
            if not HAS_ANTHROPIC:
                return False, "Anthropic library not installed"
            if not os.getenv('ANTHROPIC_API_KEY'):
                return False, "ANTHROPIC_API_KEY environment variable not set"
        elif self.provider == 'ollama':
            if not HAS_OLLAMA:
                return False, "Ollama library not installed"
        else:
            return False, f"Unsupported provider: {self.provider}"

        return True, "Configuration is valid"
