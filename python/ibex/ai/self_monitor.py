"""
IBEX Self-Monitoring System
IBEX watches and analyzes its own contributions
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import subprocess

from .contrib_monitor import ContributionMonitor
from . import AIManager
from ..core import IbexWatcher

class MockAIManager:
    """Mock AI manager for when no AI providers are available"""

    def __init__(self):
        self.provider = "none"
        self.model = "none"

    async def chat(self, messages):
        return "AI analysis not available - please configure an AI provider (OpenAI, Claude, or Ollama)"

    def is_available(self):
        return False

    async def generate_self_improvement_plan(self):
        return "# Basic Improvement Plan\n\nConfigure an AI provider to get intelligent suggestions."

class IBEXSelfMonitor:
    """IBEX self-monitoring system"""

    def __init__(self, provider: str = None, model: str = None):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.provider = provider or os.getenv('IBEX_AI_PROVIDER', 'ollama')
        self.model = model or os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')
        self.ai_manager = None
        self.watcher = IbexWatcher(str(self.project_root), "IBEX self-monitoring and improvement")

        # Initialize AI manager first
        try:
            ai_mgr = self._get_ai_manager()
            self.monitor = ContributionMonitor(str(self.project_root), ai_mgr)
        except Exception as e:
            print(f"Warning: Failed to initialize AI components: {e}")
            print("Continuing with basic monitoring capabilities...")
            ai_mgr = MockAIManager()
            self.monitor = ContributionMonitor(str(self.project_root), ai_mgr)

    def _get_ai_manager(self):
        """Lazy initialization of AI manager"""
        if self.ai_manager is None:
            try:
                self.ai_manager = AIManager(self.provider, self.model)
            except Exception as e:
                print(f"Warning: AI provider not available ({e}), using mock manager")
                # AI not available, create a mock manager
                self.ai_manager = MockAIManager()
        return self.ai_manager

        # IBEX-specific file patterns to monitor
        self.important_files = [
            'python/ibex/**/*.py',      # Python code
            'python/requirements.txt',  # Dependencies
            '*.md',                     # Documentation
            'setup.py',                 # Package setup
            '*.yml', '*.yaml',          # Configuration
        ]

    async def start_self_monitoring(self):
        """Start self-monitoring IBEX"""
        print("🐙 IBEX Self-Monitoring Started")
        print("Watching for contributions to improve IBEX itself...")

        try:
            # Start the file watcher
            self.watcher.start()

            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Stopping IBEX self-monitoring...")
            self.watcher.stop()

    async def analyze_recent_changes(self) -> Dict[str, Any]:
        """Analyze recent changes to IBEX"""

        try:
            # Get uncommitted changes
            uncommitted = self.watcher.git.get_uncommitted_changes()

            if not uncommitted:
                return {"status": "no_changes", "message": "No uncommitted changes found"}

            # Analyze the contribution
            analysis = await self.monitor.analyze_contribution(uncommitted)

            # Generate improvement suggestions
            improvements = await self._generate_improvements(analysis)

            return {
                "status": "analyzed",
                "analysis": analysis,
                "improvements": improvements,
                "files_analyzed": len(uncommitted)
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _generate_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate specific improvement suggestions for IBEX"""

        improvements = []

        # Check for missing tests
        if 'testing' not in analysis.get('categories', {}):
            code_files = []
            for category, files in analysis.get('categories', {}).items():
                if category in ['python', 'golang', 'core', 'ai']:
                    code_files.extend(files)

            if code_files:
                improvements.append("Consider adding unit tests for the modified code files")

        # Check for documentation updates
        if 'documentation' not in analysis.get('categories', {}):
            improvements.append("Update README.md or add docstrings for new functionality")

        # AI-specific improvements
        if 'ai' in analysis.get('categories', {}):
            improvements.append("Test AI functionality with different providers and models")
            improvements.append("Update AI documentation with new features")

        # Performance considerations
        if any('core' in cat or 'performance' in str(analysis).lower() for cat in analysis.get('categories', {})):
            improvements.append("Consider performance benchmarking for core changes")

        # Generate AI-powered improvements
        try:
            improvement_prompt = f"""
Based on this IBEX contribution analysis, suggest specific improvements:

Categories: {list(analysis.get('categories', {}).keys())}
Quality Score: {analysis.get('quality_score', 0)}/10
AI Analysis: {analysis.get('ai_analysis', {}).get('analysis', 'Not available')[:500]}

Provide 3-5 specific, actionable improvement suggestions for this IBEX contribution.
"""

            messages = [
                {"role": "system", "content": "You are an expert software engineer helping improve the IBEX project. Provide specific, actionable suggestions."},
                {"role": "user", "content": improvement_prompt}
            ]

            ai_suggestions = await self._get_ai_manager().chat(messages)
            improvements.append(f"🤖 AI Suggestions: {ai_suggestions}")

        except Exception as e:
            improvements.append(f"Could not generate AI suggestions: {e}")

        return improvements

    def run_quality_checks(self) -> Dict[str, Any]:
        """Run quality checks on IBEX codebase"""

        results = {
            "python_linting": self._check_python_quality(),
            "dependencies": self._check_dependencies(),
            "documentation": self._check_documentation()
        }

        return results

    def _check_python_quality(self) -> Dict[str, Any]:
        """Check Python code quality"""

        try:
            # Try to import and run basic checks
            import ast
            import os

            python_files = []
            for root, dirs, files in os.walk(self.project_root / 'python'):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))

            issues = []
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Basic syntax check
                    ast.parse(content)

                    # Check for common issues
                    if 'import *' in content:
                        issues.append(f"{file_path}: Uses 'import *'")

                    if len(content.split('\n')) > 1000:
                        issues.append(f"{file_path}: Very long file ({len(content.split())} lines)")

                except SyntaxError as e:
                    issues.append(f"{file_path}: Syntax error - {e}")
                except Exception as e:
                    issues.append(f"{file_path}: Error reading file - {e}")

            return {
                "status": "checked",
                "files_checked": len(python_files),
                "issues": issues,
                "issues_count": len(issues)
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}



    def _check_dependencies(self) -> Dict[str, Any]:
        """Check if dependencies are properly specified"""

        try:
            req_file = self.project_root / 'python' / 'requirements.txt'
            if not req_file.exists():
                return {"status": "missing", "message": "requirements.txt not found"}

            with open(req_file, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            return {
                "status": "found",
                "dependencies": len(requirements),
                "packages": requirements[:10],  # Show first 10
                "message": f"Found {len(requirements)} dependencies"
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_documentation(self) -> Dict[str, Any]:
        """Check documentation completeness"""

        try:
            docs = []
            for file in ['README.md', 'python/ibex/ai/README.md']:
                doc_file = self.project_root / file
                if doc_file.exists():
                    with open(doc_file, 'r') as f:
                        content = f.read()
                        docs.append({
                            "file": file,
                            "lines": len(content.split('\n')),
                            "chars": len(content)
                        })

            return {
                "status": "checked",
                "documents": docs,
                "message": f"Found {len(docs)} documentation files"
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def generate_self_improvement_plan(self) -> str:
        """Generate a plan for improving IBEX based on analysis"""

        # Run quality checks
        quality_results = self.run_quality_checks()

        # Analyze recent contributions
        analysis_result = await self.analyze_recent_changes()

        # Generate improvement plan
        if self._get_ai_manager().is_available():
            plan_prompt = f"""
Based on this IBEX analysis, create a self-improvement plan:

Quality Checks:
{json.dumps(quality_results, indent=2)}

Recent Analysis:
{json.dumps(analysis_result, indent=2)}

Create a structured improvement plan with:
1. Immediate fixes needed
2. Medium-term improvements
3. Long-term goals
4. Specific action items
"""

            messages = [
                {"role": "system", "content": "You are an expert software architect helping improve the IBEX project. Create a comprehensive, actionable improvement plan."},
                {"role": "user", "content": plan_prompt}
            ]

            try:
                plan = await self._get_ai_manager().chat(messages)
                return plan
            except Exception as e:
                return f"Could not generate improvement plan: {e}"
        else:
            # Provide basic improvement suggestions without AI
            return self._generate_basic_improvement_plan(quality_results, analysis_result)

    def _generate_basic_improvement_plan(self, quality_results: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
        """Generate basic improvement plan without AI"""

        plan = "# IBEX Self-Improvement Plan (Basic Analysis)\n\n"

        # Check quality results
        issues = []
        for check_name, result in quality_results.items():
            if result.get('status') not in ['success', 'checked', 'found']:
                issues.append(f"• Fix {check_name.replace('_', ' ')}: {result.get('message', 'Unknown issue')}")

        if issues:
            plan += "## Immediate Fixes Needed\n"
            plan += "\n".join(issues)
            plan += "\n\n"

        # Basic improvements
        plan += "## Recommended Improvements\n"
        plan += "• Set up AI provider (OpenAI, Claude, or Ollama) for enhanced analysis\n"
        plan += "• Add unit tests for core functionality\n"
        plan += "• Improve documentation completeness\n"
        plan += "• Set up automated testing pipeline\n"
        plan += "• Add performance monitoring\n"
        plan += "• Implement code coverage reporting\n"

        # Check for recent changes
        if analysis_result.get('status') == 'analyzed':
            files_analyzed = analysis_result.get('files_analyzed', 0)
            plan += f"\n## Recent Activity\n"
            plan += f"• Analyzed {files_analyzed} files in recent contributions\n"

        plan += "\n## Getting Started\n"
        plan += "1. Configure an AI provider by setting API keys\n"
        plan += "2. Run 'python run_ibex.py ai quality-check' regularly\n"
        plan += "3. Use 'python start_self_monitoring.py' for continuous monitoring\n"

        return plan
