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
        """Analyze different categories of files with comprehensive logic"""

        feedback = []
        suggestions = []
        complexity_score = 0
        risk_level = "low"

        # Core functionality analysis
        if 'core' in categories:
            core_files = categories['core']
            feedback.append("✅ Core functionality modified - ensure backward compatibility")
            suggestions.append("Consider adding unit tests for core changes")
            suggestions.append("Review API changes for breaking compatibility")
            complexity_score += len(core_files) * 3  # High impact
            
            # Analyze specific core files
            for file_path in core_files:
                if 'cli.py' in file_path:
                    feedback.append("🔧 CLI interface modified - test command-line functionality")
                elif 'core.py' in file_path:
                    feedback.append("⚙️ Core logic modified - thorough testing recommended")
                    risk_level = "high"

        # AI functionality analysis
        if 'ai' in categories:
            ai_files = categories['ai']
            feedback.append("🤖 AI functionality updated - verify all providers work")
            suggestions.append("Test AI providers with different models")
            suggestions.append("Validate API key handling and error cases")
            complexity_score += len(ai_files) * 2
            
            # Specific AI component analysis
            for file_path in ai_files:
                if 'provider' in file_path:
                    feedback.append(f"🔌 AI provider modified: {Path(file_path).name}")
                    suggestions.append(f"Test connectivity and error handling for {Path(file_path).stem}")
                elif 'config' in file_path:
                    feedback.append("⚙️ AI configuration updated - validate all settings")
                    risk_level = "medium"

        # Documentation analysis
        if 'documentation' in categories:
            doc_files = categories['documentation']
            feedback.append("📚 Documentation updated - good practice!")
            
            # Check documentation coverage
            code_categories = ['python', 'golang', 'core', 'ai']
            code_files = sum(len(categories.get(cat, [])) for cat in code_categories)
            doc_ratio = len(doc_files) / max(code_files, 1)
            
            if doc_ratio > 0.5:
                feedback.append("📖 Good documentation coverage relative to code changes")
            elif code_files > 0:
                suggestions.append("Consider adding more documentation for the code changes")
                
            # Specific documentation checks
            for file_path in doc_files:
                if 'README' in file_path:
                    feedback.append("📋 Main README updated - verify accuracy of new content")
                elif 'API' in file_path or 'api' in file_path:
                    feedback.append("📡 API documentation updated - ensure examples work")

        # Testing analysis
        if 'testing' in categories:
            test_files = categories['testing']
            feedback.append("🧪 Tests added/modified - excellent!")
            
            # Analyze test coverage
            if len(test_files) >= 2:
                feedback.append("🎯 Comprehensive test coverage detected")
            
            # Check test types
            for file_path in test_files:
                if 'unit' in file_path or 'test_' in Path(file_path).name:
                    feedback.append("🔬 Unit tests updated")
                elif 'integration' in file_path:
                    feedback.append("🔗 Integration tests updated")
                elif 'e2e' in file_path or 'end2end' in file_path:
                    feedback.append("🎭 End-to-end tests updated")
        else:
            # Check if tests are needed
            code_categories = ['python', 'golang', 'core', 'ai']
            if any(cat in categories for cat in code_categories):
                suggestions.append("Consider adding tests for the code changes")
                if 'core' in categories or 'ai' in categories:
                    suggestions.append("High-impact changes detected - tests strongly recommended")

        # Configuration analysis
        if 'configuration' in categories:
            config_files = categories['configuration']
            feedback.append("⚙️ Configuration files changed - check for breaking changes")
            suggestions.append("Update documentation if configuration format changed")
            complexity_score += len(config_files)
            
            # Specific configuration checks
            for file_path in config_files:
                if 'requirements' in file_path:
                    feedback.append("📦 Dependencies updated - check for compatibility issues")
                elif 'setup' in file_path:
                    feedback.append("🔧 Setup configuration changed - test installation process")
                elif any(ext in file_path for ext in ['.yml', '.yaml', '.json']):
                    feedback.append("📝 Configuration format files updated")

        # Python code analysis
        if 'python' in categories:
            py_files = categories['python']
            complexity_score += len(py_files)
            
            # Check file count for complexity
            if len(py_files) > 5:
                feedback.append("📊 Large number of Python files modified - consider staged rollout")
                risk_level = "medium" if risk_level == "low" else risk_level

        # Go code analysis
        if 'golang' in categories:
            go_files = categories['golang']
            feedback.append("🐹 Go code modified - verify build and performance")
            suggestions.append("Run Go-specific tests and benchmarks")
            complexity_score += len(go_files) * 2

        # Calculate overall risk and complexity
        if complexity_score > 10:
            risk_level = "high"
        elif complexity_score > 5:
            risk_level = "medium" if risk_level == "low" else risk_level

        # Add complexity-based suggestions
        if complexity_score > 8:
            suggestions.append("High complexity changes - consider breaking into smaller commits")
            suggestions.append("Extra code review recommended for complex changes")

        # Check for cross-cutting concerns
        total_categories = len(categories)
        if total_categories >= 4:
            feedback.append("🌐 Cross-cutting changes detected across multiple areas")
            suggestions.append("Consider impact on system integration")

        return {
            'feedback': feedback,
            'suggestions': suggestions,
            'complexity_score': complexity_score,
            'risk_level': risk_level,
            'categories_affected': total_categories,
            'analysis_depth': 'comprehensive'
        }

    async def _generate_ai_feedback(self, files_changed: List[str], commit_message: str) -> Optional[Dict[str, Any]]:
        """Generate AI-powered feedback on the contribution"""

        # Check if AI is available
        if not hasattr(self, 'ai_manager') or not self.ai_manager.is_available():
            return None

        try:
            # Use enhanced analysis with full context
            custom_prompt = f"""
Commit Message: {commit_message or "Not provided"}

Please provide a detailed analysis including:
1. Code quality assessment with specific examples
2. Potential bugs or security issues
3. Documentation and commenting quality
4. Testing requirements and coverage
5. Performance implications
6. Code organization and maintainability
7. Overall contribution quality (1-10 scale)

Be specific and actionable - reference actual code patterns, suggest concrete improvements, and prioritize the most important issues.
"""

            ai_response = await self.ai_manager.analyze_with_context(
                files_changed,
                analysis_type="contribution",
                custom_prompt=custom_prompt,
                max_tokens=8192  # Allow for deeper analysis
            )

            return {
                'analysis': ai_response,
                'generated_at': datetime.now().isoformat(),
                'provider': self.ai_manager.provider,
                'model': self.ai_manager.model,
                'analysis_type': 'enhanced',
                'context_used': True
            }

        except Exception as e:
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat(),
                'analysis_type': 'error'
            }

    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate a quality score for the contribution based on comprehensive analysis"""

        score = 5  # Base score

        # Positive factors
        if 'testing' in analysis.get('categories', {}):
            score += 3  # Testing is very important
            
        if 'documentation' in analysis.get('categories', {}):
            score += 2  # Documentation is important

        # Check for AI analysis quality
        ai_analysis = analysis.get('ai_analysis', {})
        if 'analysis' in ai_analysis and len(ai_analysis['analysis']) > 100:
            score += 1  # AI provided substantial feedback

        # Risk and complexity factors
        risk_level = analysis.get('risk_level', 'low')
        complexity_score = analysis.get('complexity_score', 0)
        
        if risk_level == 'low':
            score += 1
        elif risk_level == 'high':
            score -= 1
            
        if complexity_score > 10:
            score -= 2  # Very complex changes
        elif complexity_score > 5:
            score -= 1  # Moderately complex changes

        # Categories and coverage factors
        categories = analysis.get('categories', {})
        
        # Good practices bonus
        code_categories = sum(1 for cat in ['python', 'golang', 'core', 'ai'] if cat in categories)
        non_code_categories = sum(1 for cat in ['testing', 'documentation'] if cat in categories)
        
        if code_categories > 0 and non_code_categories > 0:
            score += 2  # Good balance of code and support changes
            
        # Comprehensive coverage bonus
        if analysis.get('categories_affected', 0) >= 3:
            if 'testing' in categories and 'documentation' in categories:
                score += 1  # Comprehensive change with proper support
            else:
                score -= 1  # Broad changes without proper support

        # Specific category bonuses
        if 'core' in categories and 'testing' in categories:
            score += 1  # Core changes with tests
            
        if 'ai' in categories:
            if 'testing' in categories:
                score += 1  # AI changes with tests
            else:
                score -= 1  # AI changes without tests are risky

        # Negative factors
        if not categories:
            score -= 3  # No categorized changes

        # AI feedback quality
        if ai_analysis.get('analysis_type') == 'error':
            score -= 1  # AI analysis failed

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
