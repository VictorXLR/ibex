"""
Tests for Self Monitor functionality
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from ibex.ai.self_monitor import IBEXSelfMonitor, MockAIManager
from ibex.ai.contrib_monitor import ContributionMonitor


class TestMockAIManager:
    """Test MockAIManager class"""
    
    def test_mock_ai_manager_init(self):
        """Test MockAIManager initialization"""
        mock_manager = MockAIManager()
        
        assert mock_manager.provider == "none"
        assert mock_manager.model == "none"
        assert not mock_manager.is_available()
    
    @pytest.mark.asyncio
    async def test_mock_ai_manager_chat(self):
        """Test MockAIManager chat functionality"""
        mock_manager = MockAIManager()
        
        response = await mock_manager.chat([])
        assert "AI analysis not available" in response
    
    @pytest.mark.asyncio
    async def test_mock_ai_manager_improvement_plan(self):
        """Test MockAIManager improvement plan"""
        mock_manager = MockAIManager()
        
        plan = await mock_manager.generate_self_improvement_plan()
        assert "Basic Improvement Plan" in plan


class TestIBEXSelfMonitor:
    """Test IBEXSelfMonitor class"""
    
    def test_self_monitor_init_default(self):
        """Test self monitor initialization with defaults"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary project structure
            (Path(temp_dir) / "python" / "ibex").mkdir(parents=True)
            
            monitor = IBEXSelfMonitor()
            
            assert monitor.provider in ["ollama", "openai", "claude"]
            assert monitor.model is not None
            assert monitor.ai_manager is not None
            assert monitor.monitor is not None
    
    def test_self_monitor_init_with_params(self):
        """Test self monitor initialization with specific parameters"""
        monitor = IBEXSelfMonitor(provider="ollama", model="test-model")
        
        assert monitor.provider == "ollama"
        assert monitor.model == "test-model"
    
    @patch('ibex.ai.self_monitor.AIManager')
    def test_get_ai_manager_success(self, mock_ai_manager_class):
        """Test successful AI manager initialization"""
        mock_ai_manager = Mock()
        mock_ai_manager_class.return_value = mock_ai_manager
        
        monitor = IBEXSelfMonitor()
        ai_manager = monitor._get_ai_manager()
        
        assert ai_manager == mock_ai_manager
        assert monitor.ai_manager == mock_ai_manager
    
    @patch('ibex.ai.self_monitor.AIManager')
    def test_get_ai_manager_failure(self, mock_ai_manager_class):
        """Test AI manager initialization failure"""
        mock_ai_manager_class.side_effect = Exception("AI not available")
        
        monitor = IBEXSelfMonitor()
        ai_manager = monitor._get_ai_manager()
        
        assert isinstance(ai_manager, MockAIManager)
    
    @patch('ibex.ai.self_monitor.IbexWatcher')
    @pytest.mark.asyncio
    async def test_start_self_monitoring(self, mock_watcher_class):
        """Test starting self-monitoring (with early exit)"""
        mock_watcher = Mock()
        mock_watcher_class.return_value = mock_watcher
        
        monitor = IBEXSelfMonitor()
        
        # We can't actually test the infinite loop, but we can test initialization
        assert monitor.watcher == mock_watcher
    
    @patch('ibex.ai.self_monitor.IbexWatcher')
    @pytest.mark.asyncio
    async def test_analyze_recent_changes_no_changes(self, mock_watcher_class):
        """Test analyzing when no changes are present"""
        mock_watcher = Mock()
        mock_git = Mock()
        mock_git.get_uncommitted_changes.return_value = []
        mock_watcher.git = mock_git
        mock_watcher_class.return_value = mock_watcher
        
        monitor = IBEXSelfMonitor()
        result = await monitor.analyze_recent_changes()
        
        assert result["status"] == "no_changes"
        assert "No uncommitted changes" in result["message"]
    
    @patch('ibex.ai.self_monitor.IbexWatcher')
    @patch('ibex.ai.contrib_monitor.ContributionMonitor.analyze_contribution')
    @pytest.mark.asyncio
    async def test_analyze_recent_changes_with_changes(self, mock_analyze, mock_watcher_class):
        """Test analyzing when changes are present"""
        # Setup mocks
        mock_watcher = Mock()
        mock_git = Mock()
        mock_git.get_uncommitted_changes.return_value = ["test.py", "README.md"]
        mock_watcher.git = mock_git
        mock_watcher.load_state.return_value = {"intent": "Test improvements"}
        mock_watcher_class.return_value = mock_watcher
        
        mock_analysis = {
            "categories": {"python": ["test.py"], "documentation": ["README.md"]},
            "quality_score": 8,
            "risk_level": "low",
            "complexity_score": 3
        }
        mock_analyze.return_value = mock_analysis
        
        monitor = IBEXSelfMonitor()
        result = await monitor.analyze_recent_changes()
        
        assert result["status"] == "analyzed"
        assert result["files_analyzed"] == 2
        assert result["project_intent"] == "Test improvements"
        assert result["analysis_depth"] == "enhanced"
        assert "ai_capabilities" in result
    
    @patch('ibex.ai.self_monitor.IbexWatcher')
    @pytest.mark.asyncio
    async def test_analyze_recent_changes_error(self, mock_watcher_class):
        """Test analyzing when an error occurs"""
        mock_watcher = Mock()
        mock_watcher.git.get_uncommitted_changes.side_effect = Exception("Git error")
        mock_watcher_class.return_value = mock_watcher
        
        monitor = IBEXSelfMonitor()
        result = await monitor.analyze_recent_changes()
        
        assert result["status"] == "error"
        assert "Git error" in result["message"]
    
    @pytest.mark.asyncio
    async def test_generate_improvements_basic(self):
        """Test improvement generation with basic analysis"""
        monitor = IBEXSelfMonitor()
        
        analysis = {
            "categories": {"python": ["utils.py"]},
            "risk_level": "low",
            "complexity_score": 2,
            "quality_score": 6,
            "feedback": ["Good code structure"],
            "suggestions": ["Add tests"]
        }
        
        improvements = await monitor._generate_improvements(analysis)
        
        assert isinstance(improvements, list)
        assert len(improvements) > 0
        
        # Should suggest tests since none are present
        improvements_text = " ".join(improvements)
        assert "test" in improvements_text.lower()
    
    @pytest.mark.asyncio
    async def test_generate_improvements_high_risk(self):
        """Test improvement generation for high-risk changes"""
        monitor = IBEXSelfMonitor()
        
        analysis = {
            "categories": {"core": ["core.py"]},
            "risk_level": "high",
            "complexity_score": 15,
            "quality_score": 3,
            "feedback": ["High risk changes detected"],
            "suggestions": ["Thorough testing required"]
        }
        
        improvements = await monitor._generate_improvements(analysis)
        
        improvements_text = " ".join(improvements)
        assert "high risk" in improvements_text.lower()
        assert "priority" in improvements_text.lower()
    
    @pytest.mark.asyncio
    async def test_generate_improvements_ai_files(self):
        """Test improvement generation for AI-related files"""
        monitor = IBEXSelfMonitor()
        
        analysis = {
            "categories": {"ai": ["ai/providers/ollama.py", "ai/config.py"]},
            "risk_level": "medium",
            "complexity_score": 6,
            "quality_score": 7,
            "feedback": ["AI functionality updated"],
            "suggestions": ["Test providers"]
        }
        
        improvements = await monitor._generate_improvements(analysis)
        
        improvements_text = " ".join(improvements)
        assert "ai" in improvements_text.lower()
        assert "provider" in improvements_text.lower()
    
    @pytest.mark.asyncio
    async def test_generate_improvements_with_tests(self):
        """Test improvement generation when tests are present"""
        monitor = IBEXSelfMonitor()
        
        analysis = {
            "categories": {
                "python": ["utils.py"],
                "testing": ["test_utils.py"]
            },
            "risk_level": "low",
            "complexity_score": 3,
            "quality_score": 8,
            "feedback": ["Good test coverage"],
            "suggestions": ["Continue good practices"]
        }
        
        improvements = await monitor._generate_improvements(analysis)
        
        improvements_text = " ".join(improvements)
        # Should have positive feedback about tests
        assert "high-quality" in improvements_text.lower() or "good" in improvements_text.lower()
    
    @patch('ibex.ai.self_monitor.IBEXSelfMonitor._get_ai_manager')
    @pytest.mark.asyncio
    async def test_generate_improvements_with_ai(self, mock_get_ai):
        """Test improvement generation with AI suggestions"""
        mock_ai_manager = AsyncMock()
        mock_ai_manager.is_available.return_value = True
        mock_ai_manager.chat.return_value = "1. Add unit tests\n2. Improve documentation\n3. Consider performance"
        mock_get_ai.return_value = mock_ai_manager
        
        monitor = IBEXSelfMonitor()
        
        analysis = {
            "categories": {"python": ["utils.py"]},
            "risk_level": "low",
            "complexity_score": 3,
            "quality_score": 6,
            "feedback": ["Code looks good"],
            "suggestions": ["Add tests"],
            "ai_analysis": {"analysis": "The code is well-structured"}
        }
        
        improvements = await monitor._generate_improvements(analysis)
        
        improvements_text = " ".join(improvements)
        assert "ai expert analysis" in improvements_text.lower()
    
    def test_run_quality_checks(self):
        """Test running quality checks"""
        monitor = IBEXSelfMonitor()
        
        results = monitor.run_quality_checks()
        
        assert "python_linting" in results
        assert "dependencies" in results
        assert "documentation" in results
        
        # Each check should have a status
        for check_name, check_result in results.items():
            assert "status" in check_result
    
    def test_check_python_quality(self):
        """Test Python quality checking"""
        monitor = IBEXSelfMonitor()
        
        result = monitor._check_python_quality()
        
        assert "status" in result
        if result["status"] == "checked":
            assert "files_checked" in result
            assert "issues" in result
            assert "issues_count" in result
    
    def test_check_dependencies(self):
        """Test dependency checking"""
        monitor = IBEXSelfMonitor()
        
        result = monitor._check_dependencies()
        
        assert "status" in result
        if result["status"] == "found":
            assert "dependencies" in result
            assert "packages" in result
        elif result["status"] == "missing":
            assert "requirements.txt not found" in result["message"]
    
    def test_check_documentation(self):
        """Test documentation checking"""
        monitor = IBEXSelfMonitor()
        
        result = monitor._check_documentation()
        
        assert "status" in result
        if result["status"] == "checked":
            assert "documents" in result
    
    @patch('ibex.ai.self_monitor.IBEXSelfMonitor.run_quality_checks')
    @patch('ibex.ai.self_monitor.IBEXSelfMonitor.analyze_recent_changes')
    @patch('ibex.ai.self_monitor.IBEXSelfMonitor._get_ai_manager')
    @pytest.mark.asyncio
    async def test_generate_self_improvement_plan_with_ai(self, mock_get_ai, mock_analyze, mock_quality):
        """Test generating improvement plan with AI available"""
        mock_ai_manager = AsyncMock()
        mock_ai_manager.is_available.return_value = True
        mock_ai_manager.chat.return_value = "## Improvement Plan\n1. Fix immediate issues\n2. Long-term goals"
        mock_get_ai.return_value = mock_ai_manager
        
        mock_quality.return_value = {
            "python_linting": {"status": "checked", "issues": []},
            "dependencies": {"status": "found", "dependencies": 5},
            "documentation": {"status": "checked", "documents": []}
        }
        
        mock_analyze.return_value = {
            "status": "analyzed",
            "files_analyzed": 3,
            "quality_score": 7
        }
        
        monitor = IBEXSelfMonitor()
        plan = await monitor.generate_self_improvement_plan()
        
        assert isinstance(plan, str)
        assert "improvement plan" in plan.lower()
    
    @patch('ibex.ai.self_monitor.IBEXSelfMonitor.run_quality_checks')
    @patch('ibex.ai.self_monitor.IBEXSelfMonitor.analyze_recent_changes')
    @patch('ibex.ai.self_monitor.IBEXSelfMonitor._get_ai_manager')
    @pytest.mark.asyncio
    async def test_generate_self_improvement_plan_no_ai(self, mock_get_ai, mock_analyze, mock_quality):
        """Test generating improvement plan without AI"""
        mock_ai_manager = Mock()
        mock_ai_manager.is_available.return_value = False
        mock_get_ai.return_value = mock_ai_manager
        
        mock_quality.return_value = {
            "python_linting": {"status": "error", "message": "Linting failed"},
            "dependencies": {"status": "found", "dependencies": 5},
            "documentation": {"status": "checked", "documents": []}
        }
        
        mock_analyze.return_value = {
            "status": "analyzed",
            "files_analyzed": 2
        }
        
        monitor = IBEXSelfMonitor()
        plan = await monitor.generate_self_improvement_plan()
        
        assert isinstance(plan, str)
        assert "basic analysis" in plan.lower()
        assert "immediate fixes" in plan.lower()
    
    def test_generate_basic_improvement_plan(self):
        """Test generating basic improvement plan"""
        monitor = IBEXSelfMonitor()
        
        quality_results = {
            "python_linting": {"status": "error", "message": "Syntax errors found"},
            "dependencies": {"status": "found", "dependencies": 5},
            "documentation": {"status": "missing", "message": "No docs found"}
        }
        
        analysis_result = {
            "status": "analyzed",
            "files_analyzed": 3
        }
        
        plan = monitor._generate_basic_improvement_plan(quality_results, analysis_result)
        
        assert isinstance(plan, str)
        assert "IBEX Self-Improvement Plan" in plan
        assert "Immediate Fixes Needed" in plan
        assert "Getting Started" in plan


if __name__ == "__main__":
    pytest.main([__file__])
