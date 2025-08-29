"""
Tests for Contribution Monitor functionality
"""

import pytest
import tempfile
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from ibex.ai.contrib_monitor import ContributionMonitor
from ibex.ai import AIManager


class TestContributionMonitor:
    """Test ContributionMonitor class"""
    
    def test_contribution_monitor_init(self):
        """Test contribution monitor initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = ContributionMonitor(project_path=temp_dir)
            
            assert monitor.project_path == Path(temp_dir)
            assert monitor.contribution_log.parent.name == '.ibex'
    
    def test_contribution_monitor_with_ai_manager(self):
        """Test contribution monitor with custom AI manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            ai_manager = Mock()
            monitor = ContributionMonitor(project_path=temp_dir, ai_manager=ai_manager)
            
            assert monitor.ai_manager == ai_manager
    
    def test_get_file_category_core(self):
        """Test file categorization for core files"""
        monitor = ContributionMonitor()
        
        assert monitor._get_file_category("core.py") == "core"
        assert monitor._get_file_category("cli.py") == "core"
        assert monitor._get_file_category("main.py") == "core"
    
    def test_get_file_category_ai(self):
        """Test file categorization for AI files"""
        monitor = ContributionMonitor()
        
        assert monitor._get_file_category("python/ibex/ai/providers/ollama.py") == "ai"
        assert monitor._get_file_category("ai/config.py") == "ai"
    
    def test_get_file_category_documentation(self):
        """Test file categorization for documentation"""
        monitor = ContributionMonitor()
        
        assert monitor._get_file_category("README.md") == "documentation"
        assert monitor._get_file_category("docs/api.txt") == "documentation"
        assert monitor._get_file_category("guide.rst") == "documentation"
    
    def test_get_file_category_configuration(self):
        """Test file categorization for configuration files"""
        monitor = ContributionMonitor()
        
        assert monitor._get_file_category("requirements.txt") == "configuration"
        assert monitor._get_file_category("setup.py") == "configuration"
        assert monitor._get_file_category("config.yml") == "configuration"
    
    def test_get_file_category_testing(self):
        """Test file categorization for test files"""
        monitor = ContributionMonitor()
        
        assert monitor._get_file_category("test_ai.py") == "testing"
        assert monitor._get_file_category("tests/test_config.py") == "testing"
        assert monitor._get_file_category("unit_test.py") == "testing"
    
    def test_get_file_category_python(self):
        """Test file categorization for Python files"""
        monitor = ContributionMonitor()
        
        assert monitor._get_file_category("utils.py") == "python"
        assert monitor._get_file_category("module/helper.py") == "python"
    
    def test_get_file_category_golang(self):
        """Test file categorization for Go files"""
        monitor = ContributionMonitor()
        
        assert monitor._get_file_category("main.go") == "golang"
        assert monitor._get_file_category("pkg/utils.go") == "golang"
    
    def test_get_file_category_other(self):
        """Test file categorization for other files"""
        monitor = ContributionMonitor()
        
        assert monitor._get_file_category("data.json") == "other"
        assert monitor._get_file_category("image.png") == "other"
    
    @pytest.mark.asyncio
    async def test_analyze_categories_core_files(self):
        """Test category analysis for core files"""
        monitor = ContributionMonitor()
        categories = {"core": ["core.py", "cli.py"]}
        
        result = await monitor._analyze_categories(categories)
        
        assert "feedback" in result
        assert "suggestions" in result
        assert "complexity_score" in result
        assert "risk_level" in result
        
        # Check for core-specific feedback
        feedback_text = " ".join(result["feedback"])
        assert "core functionality" in feedback_text.lower()
        assert result["risk_level"] in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_analyze_categories_ai_files(self):
        """Test category analysis for AI files"""
        monitor = ContributionMonitor()
        categories = {"ai": ["ai/providers/ollama.py", "ai/config.py"]}
        
        result = await monitor._analyze_categories(categories)
        
        feedback_text = " ".join(result["feedback"])
        assert "ai functionality" in feedback_text.lower()
        assert "providers" in feedback_text.lower()
        
        suggestions_text = " ".join(result["suggestions"])
        assert "test" in suggestions_text.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_categories_with_tests(self):
        """Test category analysis when tests are included"""
        monitor = ContributionMonitor()
        categories = {
            "python": ["utils.py"],
            "testing": ["test_utils.py"]
        }
        
        result = await monitor._analyze_categories(categories)
        
        feedback_text = " ".join(result["feedback"])
        assert "tests" in feedback_text.lower()
        
        # Should have higher score with tests
        assert result["complexity_score"] >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_categories_no_tests(self):
        """Test category analysis when no tests are included"""
        monitor = ContributionMonitor()
        categories = {"python": ["utils.py"], "core": ["core.py"]}
        
        result = await monitor._analyze_categories(categories)
        
        suggestions_text = " ".join(result["suggestions"])
        assert "test" in suggestions_text.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_categories_documentation(self):
        """Test category analysis with documentation"""
        monitor = ContributionMonitor()
        categories = {
            "documentation": ["README.md"],
            "python": ["utils.py"]
        }
        
        result = await monitor._analyze_categories(categories)
        
        feedback_text = " ".join(result["feedback"])
        assert "documentation" in feedback_text.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_categories_high_complexity(self):
        """Test category analysis for high complexity changes"""
        monitor = ContributionMonitor()
        categories = {
            "core": ["core.py", "main.py"],
            "ai": ["ai/provider1.py", "ai/provider2.py", "ai/config.py"],
            "python": ["utils1.py", "utils2.py", "utils3.py"]
        }
        
        result = await monitor._analyze_categories(categories)
        
        assert result["complexity_score"] > 8
        assert result["risk_level"] in ["medium", "high"]
        
        suggestions_text = " ".join(result["suggestions"])
        assert "complexity" in suggestions_text.lower() or "review" in suggestions_text.lower()
    
    def test_calculate_quality_score_high_quality(self):
        """Test quality score calculation for high quality contribution"""
        monitor = ContributionMonitor()
        analysis = {
            "categories": {
                "python": ["utils.py"],
                "testing": ["test_utils.py"],
                "documentation": ["README.md"]
            },
            "risk_level": "low",
            "complexity_score": 3,
            "ai_analysis": {"analysis": "Good contribution with comprehensive coverage"}
        }
        
        score = monitor._calculate_quality_score(analysis)
        assert score >= 7  # Should be high with tests + docs + low risk
    
    def test_calculate_quality_score_low_quality(self):
        """Test quality score calculation for low quality contribution"""
        monitor = ContributionMonitor()
        analysis = {
            "categories": {"core": ["core.py"]},
            "risk_level": "high",
            "complexity_score": 15,
            "ai_analysis": {"analysis_type": "error"}
        }
        
        score = monitor._calculate_quality_score(analysis)
        assert score <= 5  # Should be low with high risk, no tests/docs
    
    def test_calculate_quality_score_bounds(self):
        """Test quality score bounds"""
        monitor = ContributionMonitor()
        
        # Test minimum bound
        very_bad_analysis = {
            "categories": {},
            "risk_level": "high",
            "complexity_score": 20,
            "ai_analysis": {"analysis_type": "error"}
        }
        score = monitor._calculate_quality_score(very_bad_analysis)
        assert 1 <= score <= 10
        
        # Test maximum bound
        perfect_analysis = {
            "categories": {
                "core": ["core.py"],
                "testing": ["test_core.py", "integration_test.py"],
                "documentation": ["README.md", "API.md"]
            },
            "risk_level": "low",
            "complexity_score": 2,
            "ai_analysis": {"analysis": "Excellent contribution"}
        }
        score = monitor._calculate_quality_score(perfect_analysis)
        assert 1 <= score <= 10
    
    @patch('ibex.ai.contrib_monitor.ContributionMonitor._generate_ai_feedback')
    @pytest.mark.asyncio
    async def test_analyze_contribution_full_flow(self, mock_ai_feedback):
        """Test full contribution analysis flow"""
        mock_ai_feedback.return_value = {
            "analysis": "Good contribution",
            "generated_at": "2023-01-01T00:00:00",
            "provider": "ollama",
            "model": "test-model"
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = ContributionMonitor(project_path=temp_dir)
            
            files_changed = ["python/utils.py", "tests/test_utils.py", "README.md"]
            result = await monitor.analyze_contribution(files_changed, "Add utility functions")
            
            assert "timestamp" in result
            assert "files_changed" in result
            assert "categories" in result
            assert "quality_score" in result
            assert "feedback" in result
            assert "suggestions" in result
            assert "ai_analysis" in result
            
            assert result["files_changed"] == files_changed
            assert len(result["categories"]) > 0
            assert 1 <= result["quality_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_generate_ai_feedback_no_ai(self):
        """Test AI feedback generation when AI is not available"""
        monitor = ContributionMonitor()
        monitor.ai_manager = None
        
        result = await monitor._generate_ai_feedback(["test.py"], "Test commit")
        assert result is None
    
    @patch('ibex.ai.AIManager')
    @pytest.mark.asyncio
    async def test_generate_ai_feedback_with_ai(self, mock_ai_manager_class):
        """Test AI feedback generation with AI available"""
        mock_ai_manager = AsyncMock()
        mock_ai_manager.is_available.return_value = True
        mock_ai_manager.analyze_with_context.return_value = "AI analysis result"
        mock_ai_manager.provider = "ollama"
        mock_ai_manager.model = "test-model"
        mock_ai_manager_class.return_value = mock_ai_manager
        
        monitor = ContributionMonitor()
        monitor.ai_manager = mock_ai_manager
        
        result = await monitor._generate_ai_feedback(["test.py"], "Test commit")
        
        assert result is not None
        assert "analysis" in result
        assert result["analysis"] == "AI analysis result"
        assert result["provider"] == "ollama"
        assert result["model"] == "test-model"
    
    def test_load_save_contributions(self):
        """Test loading and saving contribution history"""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = ContributionMonitor(project_path=temp_dir)
            
            # Should start empty
            contributions = monitor._load_contributions()
            assert contributions == []
            
            # Save some contributions
            test_contributions = [
                {"timestamp": "2023-01-01", "quality_score": 8},
                {"timestamp": "2023-01-02", "quality_score": 6}
            ]
            monitor._save_contributions(test_contributions)
            
            # Load and verify
            loaded = monitor._load_contributions()
            assert len(loaded) == 2
            assert loaded[0]["quality_score"] == 8
    
    def test_get_contribution_history(self):
        """Test getting contribution history"""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = ContributionMonitor(project_path=temp_dir)
            
            # Add some test data
            test_contributions = [
                {"timestamp": f"2023-01-0{i}", "quality_score": i}
                for i in range(1, 16)  # 15 contributions
            ]
            monitor._save_contributions(test_contributions)
            
            # Get last 5
            recent = monitor.get_contribution_history(5)
            assert len(recent) == 5
            assert recent[0]["quality_score"] == 15  # Most recent first
            assert recent[4]["quality_score"] == 11
    
    def test_generate_contribution_report(self):
        """Test generating contribution report"""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = ContributionMonitor(project_path=temp_dir)
            
            # Test with no contributions
            report = monitor.generate_contribution_report()
            assert "No contributions recorded" in report
            
            # Add test data
            test_contributions = [
                {
                    "timestamp": "2023-01-01T00:00:00",
                    "quality_score": 8,
                    "categories": {"python": ["utils.py"], "testing": ["test.py"]},
                    "ai_analysis": {"analysis": "Good work on utility functions"}
                },
                {
                    "timestamp": "2023-01-02T00:00:00",
                    "quality_score": 6,
                    "categories": {"documentation": ["README.md"]},
                    "ai_analysis": {"analysis": "Documentation update"}
                }
            ]
            monitor._save_contributions(test_contributions)
            
            report = monitor.generate_contribution_report()
            assert "Total Contributions: 2" in report
            assert "Category Breakdown" in report
            assert "Quality Statistics" in report
            assert "Average Quality Score" in report
            assert "Recent Contributions" in report


if __name__ == "__main__":
    pytest.main([__file__])
