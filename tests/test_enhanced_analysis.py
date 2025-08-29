#!/usr/bin/env python3
"""
Test script to demonstrate enhanced IBEX analysis functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the python directory to the path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from ibex.ai.self_monitor import IBEXSelfMonitor
from ibex.ai import AIManager

async def test_enhanced_analysis():
    """Test the enhanced analysis functionality"""
    print("🧪 Testing Enhanced IBEX Analysis Functionality")
    print("=" * 60)

    try:
        # Initialize the self-monitor
        print("🔧 Initializing IBEX Self-Monitor...")
        monitor = IBEXSelfMonitor()

        # Test the enhanced analysis
        print("🔍 Running enhanced analysis...")
        result = await monitor.analyze_recent_changes()

        print(f"📊 Analysis Status: {result.get('status', 'Unknown')}")
        print(f"📁 Files Analyzed: {result.get('files_analyzed', 0)}")
        print(f"🎯 Project Intent: {result.get('project_intent', 'Not specified')}")
        print(f"🔬 Analysis Depth: {result.get('analysis_depth', 'Basic')}")

        if result['status'] == 'analyzed':
            analysis = result['analysis']

            print(f"\n⭐ Quality Score: {analysis.get('quality_score', 0)}/10")

            print("\n📝 Categories:")
            for category, files in analysis.get('categories', {}).items():
                print(f"  • {category.title()}: {len(files)} files")

            print("\n🔍 Basic Feedback:")
            for feedback in analysis.get('feedback', []):
                print(f"  • {feedback}")

            print("\n💡 Suggestions:")
            for suggestion in analysis.get('suggestions', []):
                print(f"  • {suggestion}")

            # Enhanced AI analysis
            ai_analysis = analysis.get('ai_analysis', {})
            if 'analysis' in ai_analysis:
                print(f"\n🤖 AI Analysis ({ai_analysis.get('provider', 'unknown')}):")
                analysis_text = ai_analysis['analysis']
                if len(analysis_text) > 500:
                    print(f"  {analysis_text[:500]}...")
                else:
                    print(f"  {analysis_text}")

            # Improvements
            improvements = result.get('improvements', [])
            if improvements:
                print("\n🚀 Improvement Suggestions:")
                for improvement in improvements:
                    print(f"  • {improvement}")

            # Capabilities
            capabilities = result.get('ai_capabilities', {})
            if capabilities:
                print("\n⚡ Analysis Capabilities Used:")
                for capability, enabled in capabilities.items():
                    status = "✅" if enabled else "❌"
                    print(f"  {status} {capability.replace('_', ' ').title()}")

        elif result['status'] == 'no_changes':
            print("📝 No uncommitted changes found to analyze")
            print("💡 Try making some changes to files and running this test again")

        elif result['status'] == 'error':
            print(f"❌ Analysis Error: {result.get('message', 'Unknown error')}")

        print("\n" + "=" * 60)
        print("✅ Enhanced analysis test completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def test_ai_manager_capabilities():
    """Test AI manager enhanced capabilities"""
    print("\n🧪 Testing AI Manager Enhanced Capabilities")
    print("=" * 60)

    try:
        # Test AI manager initialization
        print("🔧 Testing AI Manager initialization...")
        ai_manager = AIManager()

        print(f"🤖 Provider: {ai_manager.provider}")
        print(f"🧠 Model: {ai_manager.model}")
        print(f"📁 Project Root: {ai_manager.project_root}")

        # Test file reading capability
        print("\n📖 Testing file reading capability...")
        test_files = [
            "python/ibex/ai/__init__.py",
            "python/ibex/core.py",
            "README.md"
        ]

        for file_path in test_files:
            content = ai_manager.read_file_content(file_path, max_lines=10)
            if content.startswith("File not found"):
                print(f"  ❌ {file_path}: Not found")
            else:
                lines = content.count('\n')
                print(f"  ✅ {file_path}: {lines} lines read")

        # Test enhanced context creation
        print("\n🔬 Testing enhanced context creation...")
        context = ai_manager.create_enhanced_context(test_files[:2], "test")
        print(f"  📝 Context created: {len(context)} characters")
        print(f"  📋 Preview: {context[:200]}...")

        # Test system prompt creation
        print("\n💬 Testing system prompt creation...")
        system_prompt = ai_manager.create_system_prompt("test", True)
        print(f"  📝 System prompt: {len(system_prompt)} characters")
        print(f"  📋 Preview: {system_prompt[:200]}...")

        print("\n✅ AI Manager capabilities test completed!")

    except Exception as e:
        print(f"❌ AI Manager test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("🚀 IBEX Enhanced Analysis Test Suite")
    print("=" * 60)

    await test_enhanced_analysis()
    await test_ai_manager_capabilities()

    print("\n🎉 All tests completed!")
    print("\n💡 To see the enhanced analysis in action:")
    print("  1. Make some changes to IBEX files")
    print("  2. Run: python run_ibex.py ai analyze-contribution")
    print("  3. Or use CLI: python run_ibex.py ai self-monitor")

if __name__ == "__main__":
    asyncio.run(main())
