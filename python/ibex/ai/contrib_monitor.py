"""
IBEX Contribution Monitor
Monitors contributions to the IBEX project and provides intelligent feedback
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from . import AIManager
from .utils import create_commit_message_prompt

class ContributionMonitor:
    """Monitors and analyzes contributions to IBEX"""

    def __init__(self, project_path: str = None, ai_manager: AIManager = None):
        self.project_path = Path(project_path or Path(__file__).parent.parent.parent.parent)
        self.ai_manager = ai_manager
        self.contribution_log = self.project_path / '.ibex' / 'contributions.json'

        # Initialize AI manager if not provided
        if self.ai_manager is None:
            try:
                # Try to get configured provider from environment
                provider = os.getenv('IBEX_AI_PROVIDER', 'ollama')
                model = None
                if provider == 'ollama':
                    model = os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')
                elif provider == 'claude':
                    model = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
                else:  # openai
                    model = os.getenv('OPENAI_MODEL', 'gpt-4')

                self.ai_manager = AIManager(provider, model)
            except Exception as e:
                print(f"Warning: AI provider not available ({e}), using mock manager")
                # Fallback to mock manager
                self.ai_manager = None

        # Create contribution log if it doesn't exist
        if not self.contribution_log.exists():
            self.contribution_log.parent.mkdir(exist_ok=True)
            self._save_contributions([])

    def _load_contributions(self) -> List[Dict]:
        """Load contribution history"""
        try:
            with open(self.contribution_log, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_contributions(self, contributions: List[Dict]):
        """Save contribution history"""
        with open(self.contribution_log, 'w') as f:
            json.dump(contributions, f, indent=2, default=str)

    def _get_file_category(self, file_path: str) -> str:
        """Categorize file type for analysis"""
        path = Path(file_path)

        # Core functionality
        if any(part in str(path) for part in ['core.py', 'cli.py', 'main.py']):
            return 'core'

        # AI functionality
        if 'ai' in str(path):
            return 'ai'

        # Documentation
        if path.suffix in ['.md', '.txt', '.rst']:
            return 'documentation'

        # Configuration
        if any(part in str(path) for part in ['requirements', 'setup', 'config', '.yml', '.yaml']):
            return 'configuration'

        # Tests
        if 'test' in str(path).lower() or path.suffix == '.py' and 'test' in path.name:
            return 'testing'

        # Go code
        if path.suffix == '.go':
            return 'golang'

        # Python code
        if path.suffix == '.py':
            return 'python'

        return 'other'

    async def analyze_contribution(self, files_changed: List[str], commit_message: str = "") -> Dict[str, Any]:
        """Analyze a contribution and provide feedback"""

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'files_changed': files_changed,
            'categories': {},
            'quality_score': 0,
            'feedback': [],
            'suggestions': [],
            'ai_analysis': {}
        }

        # Categorize files
        for file_path in files_changed:
            category = self._get_file_category(file_path)
            if category not in analysis['categories']:
                analysis['categories'][category] = []
            analysis['categories'][category].append(file_path)

        # Analyze each category
        analysis_results = await self._analyze_categories(analysis['categories'])
        analysis.update(analysis_results)

        # Generate AI-powered analysis (if available)
        if files_changed:
            ai_feedback = await self._generate_ai_feedback(files_changed, commit_message)
            if ai_feedback:
                analysis['ai_analysis'] = ai_feedback

        # Calculate quality score
        analysis['quality_score'] = self._calculate_quality_score(analysis)

        # Save contribution
        contributions = self._load_contributions()
        contributions.append(analysis)
        self._save_contributions(contributions)

        return analysis

    async def _analyze_categories(self, categories: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyze different categories of files"""

        feedback = []
        suggestions = []

        # Core functionality analysis
        if 'core' in categories:
            feedback.append("✅ Core functionality modified - ensure backward compatibility")
            suggestions.append("Consider adding unit tests for core changes")

        # AI functionality analysis
        if 'ai' in categories:
            feedback.append("🤖 AI functionality updated - verify all providers work")
            suggestions.append("Test AI providers with different models")

        # Documentation analysis
        if 'documentation' in categories:
            feedback.append("📚 Documentation updated - good practice!")
            if len(categories.get('documentation', [])) > len(categories.get('code', [])):
                suggestions.append("Documentation changes seem extensive - ensure code changes are also covered")

        # Testing analysis
        if 'testing' in categories:
            feedback.append("🧪 Tests added/modified - excellent!")
        elif any(cat in ['python', 'golang', 'core'] for cat in categories.keys()):
            suggestions.append("Consider adding tests for the code changes")

        # Configuration analysis
        if 'configuration' in categories:
            feedback.append("⚙️ Configuration files changed - check for breaking changes")
            suggestions.append("Update documentation if configuration format changed")

        return {
            'feedback': feedback,
            'suggestions': suggestions
        }

    async def _generate_ai_feedback(self, files_changed: List[str], commit_message: str) -> Optional[Dict[str, Any]]:
        """Generate AI-powered feedback on the contribution"""

        # Check if AI is available
        if not hasattr(self, 'ai_manager') or not self.ai_manager.is_available():
            return None

        try:
            # Create a comprehensive analysis prompt
            analysis_prompt = f"""
Analyze this contribution to the IBEX project:

Files Changed:
{chr(10).join(f"- {file}" for file in files_changed)}

Commit Message: {commit_message or "Not provided"}

Please provide:
1. Code quality assessment
2. Potential issues or improvements
3. Documentation needs
4. Testing recommendations
5. Overall contribution quality (1-10 scale)

Focus on:
- Code organization and readability
- Error handling
- Documentation completeness
- Testing adequacy
- Alignment with project goals
"""

            messages = [
                {"role": "system", "content": "You are a senior software engineer reviewing contributions to the IBEX project. Provide constructive, helpful feedback."},
                {"role": "user", "content": analysis_prompt}
            ]

            ai_response = await self.ai_manager.chat(messages)

            return {
                'analysis': ai_response,
                'generated_at': datetime.now().isoformat(),
                'provider': self.ai_manager.provider,
                'model': self.ai_manager.model
            }

        except Exception as e:
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate a quality score for the contribution"""

        score = 5  # Base score

        # Positive factors
        if 'testing' in analysis.get('categories', {}):
            score += 2

        if 'documentation' in analysis.get('categories', {}):
            score += 1

        # Check for AI analysis quality
        ai_analysis = analysis.get('ai_analysis', {})
        if 'analysis' in ai_analysis and len(ai_analysis['analysis']) > 100:
            score += 2

        # Negative factors
        if not analysis.get('categories', {}):
            score -= 2

        # Ensure score is between 1-10
        return max(1, min(10, score))

    def get_contribution_history(self, limit: int = 10) -> List[Dict]:
        """Get recent contribution history"""
        contributions = self._load_contributions()
        return contributions[-limit:][::-1]  # Return most recent first

    def generate_contribution_report(self) -> str:
        """Generate a comprehensive contribution report"""

        contributions = self._load_contributions()

        if not contributions:
            return "No contributions recorded yet."

        report = "# IBEX Contribution Report\n\n"
        report += f"Total Contributions: {len(contributions)}\n\n"

        # Category breakdown
        category_counts = {}
        quality_scores = []

        for contrib in contributions:
            quality_scores.append(contrib.get('quality_score', 0))
            for category, files in contrib.get('categories', {}).items():
                category_counts[category] = category_counts.get(category, 0) + len(files)

        report += "## Category Breakdown\n"
        for category, count in sorted(category_counts.items()):
            report += f"- {category.title()}: {count} files\n"

        # Quality statistics
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            report += f"\n## Quality Statistics\n"
            report += f"- Average Quality Score: {avg_quality:.1f}/10\n"
            report += f"- Highest Score: {max(quality_scores)}/10\n"
            report += f"- Lowest Score: {min(quality_scores)}/10\n"

        # Recent contributions
        report += "\n## Recent Contributions\n"
        recent = contributions[-5:][::-1]  # Last 5, most recent first

        for i, contrib in enumerate(recent, 1):
            timestamp = contrib.get('timestamp', 'Unknown')[:19]
            score = contrib.get('quality_score', 0)
            categories = list(contrib.get('categories', {}).keys())

            report += f"\n### Contribution {i}\n"
            report += f"- Date: {timestamp}\n"
            report += f"- Quality Score: {score}/10\n"
            report += f"- Categories: {', '.join(categories) if categories else 'None'}\n"

            ai_analysis = contrib.get('ai_analysis', {})
            if 'analysis' in ai_analysis:
                analysis_preview = ai_analysis['analysis'][:200] + "..." if len(ai_analysis['analysis']) > 200 else ai_analysis['analysis']
                report += f"- AI Analysis: {analysis_preview}\n"

        return report
