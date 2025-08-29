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
        """Analyze recent changes to IBEX with enhanced context"""

        try:
            # Get uncommitted changes
            uncommitted = self.watcher.git.get_uncommitted_changes()

            if not uncommitted:
                return {"status": "no_changes", "message": "No uncommitted changes found"}

            # Get current project state for better context
            state = self.watcher.load_state()
            current_intent = state.get('intent', 'General development')

            # Analyze the contribution with enhanced context
            analysis = await self.monitor.analyze_contribution(uncommitted, f"Intent: {current_intent}")

            # Generate improvement suggestions with enhanced AI analysis
            improvements = await self._generate_improvements(analysis)

            # Add additional context to the response
            enhanced_response = {
                "status": "analyzed",
                "analysis": analysis,
                "improvements": improvements,
                "files_analyzed": len(uncommitted),
                "project_intent": current_intent,
                "analysis_depth": "enhanced",
                "context_provided": True,
                "ai_capabilities": {
                    "file_content_access": True,
                    "diff_analysis": True,
                    "code_quality_assessment": True,
                    "actionable_feedback": True
                }
            }

            return enhanced_response

        except Exception as e:
            return {"status": "error", "message": str(e), "error_details": str(e)}

    async def _generate_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate specific improvement suggestions for IBEX with comprehensive analysis"""

        improvements = []
        categories = analysis.get('categories', {})
        risk_level = analysis.get('risk_level', 'low')
        complexity_score = analysis.get('complexity_score', 0)
        quality_score = analysis.get('quality_score', 0)

        # Risk-based improvements
        if risk_level == 'high':
            improvements.append("🚨 HIGH RISK changes detected - implement staged rollout")
            improvements.append("🔍 Extra code review and testing required for high-risk changes")
            
        # Quality-based improvements
        if quality_score < 5:
            improvements.append("📉 Quality score below average - address key improvement areas")
            if 'testing' not in categories:
                improvements.append("🧪 PRIORITY: Add comprehensive test coverage")
            if 'documentation' not in categories:
                improvements.append("📚 PRIORITY: Add or update documentation")

        # Check for missing tests with specific recommendations
        if 'testing' not in categories:
            code_files = []
            for category, files in categories.items():
                if category in ['python', 'golang', 'core', 'ai']:
                    code_files.extend(files)

            if code_files:
                improvements.append("🧪 Consider adding unit tests for the modified code files")
                
                # Specific test recommendations based on file types
                if 'core' in categories:
                    improvements.append("🔧 Add integration tests for core functionality changes")
                if 'ai' in categories:
                    improvements.append("🤖 Add provider-specific tests for AI functionality")
                    
                # High complexity needs more testing
                if complexity_score > 8:
                    improvements.append("🎯 High complexity detected - comprehensive test suite recommended")

        # Documentation improvements
        if 'documentation' not in categories:
            improvements.append("📚 Update README.md or add docstrings for new functionality")
            
            # Specific documentation needs
            if 'ai' in categories:
                improvements.append("📖 Update AI provider documentation with configuration examples")
            if 'core' in categories:
                improvements.append("📋 Update core functionality documentation and usage examples")
            if 'configuration' in categories:
                improvements.append("⚙️ Document configuration changes and migration steps")

        # AI-specific improvements
        if 'ai' in categories:
            improvements.append("🤖 Test AI functionality with different providers and models")
            improvements.append("🔌 Validate error handling and fallback mechanisms")
            improvements.append("🛡️ Test API key validation and security measures")
            
            # Provider-specific recommendations
            ai_files = categories['ai']
            for file_path in ai_files:
                if 'ollama' in file_path:
                    improvements.append("🦙 Test Ollama connectivity and model availability")
                elif 'openai' in file_path:
                    improvements.append("🔓 Test OpenAI API integration and rate limiting")
                elif 'claude' in file_path:
                    improvements.append("🧠 Test Claude API integration and context handling")

        # Performance and scalability improvements
        if any('core' in cat or 'performance' in str(analysis).lower() for cat in categories):
            improvements.append("⚡ Consider performance benchmarking for core changes")
            
        if complexity_score > 10:
            improvements.append("🚀 High complexity changes - consider performance impact assessment")

        # Configuration and deployment improvements
        if 'configuration' in categories:
            improvements.append("🔧 Test configuration migration and backward compatibility")
            improvements.append("📋 Update deployment documentation for configuration changes")
            
        # Code quality improvements
        if len(categories.get('python', [])) > 5:
            improvements.append("🐍 Large Python changeset - consider code quality checks (linting, formatting)")
            
        # Security improvements
        if 'ai' in categories or 'core' in categories:
            improvements.append("🛡️ Review security implications of changes (API keys, data handling)")

        # Integration improvements
        categories_count = len(categories)
        if categories_count >= 4:
            improvements.append("🌐 Cross-cutting changes - test system integration thoroughly")
            improvements.append("🔄 Consider compatibility testing across different environments")

        # Generate AI-powered improvements
        try:
            # Enhanced prompt with more context
            improvement_prompt = f"""
Based on this comprehensive IBEX contribution analysis, suggest specific, actionable improvements:

ANALYSIS CONTEXT:
- Categories affected: {list(categories.keys())}
- Risk Level: {risk_level}
- Complexity Score: {complexity_score}/20
- Quality Score: {quality_score}/10
- Files changed: {sum(len(files) for files in categories.values())}

DETAILED FEEDBACK:
{analysis.get('feedback', [])}

CURRENT SUGGESTIONS:
{analysis.get('suggestions', [])}

AI ANALYSIS:
{analysis.get('ai_analysis', {}).get('analysis', 'Not available')[:800]}

Please provide 3-5 ADDITIONAL specific, actionable improvement suggestions that complement the existing analysis. Focus on:
1. Technical implementation improvements
2. Testing strategies specific to the changes
3. Documentation gaps not already covered
4. Potential integration issues
5. Performance or security considerations

Be specific and prioritize based on the risk level and complexity.
"""

            messages = [
                {"role": "system", "content": "You are an expert software architect helping improve the IBEX project. Analyze the comprehensive contribution data and provide specific, actionable suggestions that add value beyond the automated analysis."},
                {"role": "user", "content": improvement_prompt}
            ]

            ai_suggestions = await self._get_ai_manager().chat(messages, max_tokens=2048)
            
            # Format AI suggestions nicely
            if ai_suggestions and len(ai_suggestions.strip()) > 20:
                improvements.append("🤖 AI Expert Analysis:")
                # Split suggestions into lines for better readability
                for line in ai_suggestions.split('\n'):
                    if line.strip() and not line.strip().startswith('#'):
                        improvements.append(f"   {line.strip()}")

        except Exception as e:
            improvements.append(f"⚠️ Could not generate AI suggestions: {e}")

        # Add final summary based on quality
        if quality_score >= 8:
            improvements.append("✅ High-quality contribution - minimal additional work needed")
        elif quality_score >= 6:
            improvements.append("👍 Good contribution - address suggestions to improve quality")
        else:
            improvements.append("⚠️ Contribution needs improvement - prioritize testing and documentation")

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
