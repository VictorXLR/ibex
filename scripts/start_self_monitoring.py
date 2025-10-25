#!/usr/bin/env python3
"""
IBEX Self-Monitoring Startup Script
Automatically starts IBEX in self-monitoring mode
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the python directory to the path
project_root = Path(__file__).parent
python_dir = project_root / "python"
sys.path.insert(0, str(python_dir))

async def start_ibex_self_monitoring():
    """Start IBEX in self-monitoring mode"""

    print("🐙 IBEX Self-Monitoring System")
    print("=" * 50)

    try:
        # Import IBEX components
        from ibex.ai.self_monitor import IBEXSelfMonitor
        from ibex.ai.contrib_monitor import ContributionMonitor

        # Initialize monitors
        self_monitor = IBEXSelfMonitor()
        contrib_monitor = ContributionMonitor()

        # Check AI availability
        try:
            ai_available = self_monitor.ai_manager.is_available()
        except Exception as e:
            print(f"⚠️  AI check failed: {e}")
            ai_available = False
        if ai_available:
            print("✅ IBEX Self-Monitoring initialized with AI")
            print("📊 Monitoring capabilities:")
            print("   • Real-time contribution analysis")
            print("   • AI-powered code review")
            print("   • Quality assurance checks")
            print("   • Automatic improvement suggestions")
            print("   • Contribution tracking and reporting")
        else:
            print("⚠️  IBEX Self-Monitoring initialized (AI features limited)")
            print("📊 Monitoring capabilities:")
            print("   • Real-time contribution analysis")
            print("   • Quality assurance checks")
            print("   • Contribution tracking and reporting")
            print("   • Basic improvement suggestions")
            print()
            print("💡 To enable AI features:")
            print("   • Set OPENAI_API_KEY for OpenAI GPT models")
            print("   • Set ANTHROPIC_API_KEY for Claude models")
            print("   • Install Ollama for local models")
        print()

        # Show current status
        print("📈 Current Status:")
        contributions = contrib_monitor.get_contribution_history(limit=1)
        if contributions:
            latest = contributions[0]
            print(f"   • Latest contribution: {latest.get('timestamp', 'Unknown')[:19]}")
            print(f"   • Quality score: {latest.get('quality_score', 0)}/10")
            print(f"   • Categories: {', '.join(latest.get('categories', {}).keys())}")
        else:
            print("   • No previous contributions analyzed")
        print()

        # Run initial quality check
        print("🔍 Running initial quality check...")
        quality_results = self_monitor.run_quality_checks()

        checks_passed = 0
        total_checks = len(quality_results)

        for check_name, result in quality_results.items():
            if result.get('status') in ['success', 'checked', 'found']:
                checks_passed += 1
                print(f"   ✅ {check_name.replace('_', ' ').title()}: {result.get('message', 'OK')}")
            else:
                print(f"   ❌ {check_name.replace('_', ' ').title()}: {result.get('message', 'Failed')}")

        print(f"\nQuality Score: {checks_passed}/{total_checks} checks passed")
        print()

        # Start monitoring loop
        print("🚀 Starting continuous monitoring...")
        print("Press Ctrl+C to stop")
        print("-" * 50)

        while True:
            # Check for new contributions every 30 seconds
            await asyncio.sleep(30)

            try:
                # Analyze any new changes
                analysis_result = await self_monitor.analyze_recent_changes()

                if analysis_result['status'] == 'analyzed':
                    analysis = analysis_result['analysis']
                    files_analyzed = analysis_result.get('files_analyzed', 0)

                    if files_analyzed > 0:
                        print(f"\n🔔 New contribution detected! ({files_analyzed} files)")
                        print(f"Quality Score: {analysis.get('quality_score', 0)}/10")

                        # Show brief feedback
                        feedback = analysis.get('feedback', [])[:2]  # Show first 2 feedback items
                        for item in feedback:
                            print(f"   {item}")

                        suggestions = analysis.get('suggestions', [])[:1]  # Show first suggestion
                        if suggestions:
                            print(f"   💡 {suggestions[0]}")

                        print("   (Run 'python run_ibex.py ai analyze-contribution' for full analysis)")

                elif analysis_result['status'] == 'no_changes':
                    # Only show this occasionally to avoid spam
                    pass  # Silent when no changes

            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                import traceback
                print(f"   Error details: {traceback.format_exc()}")

    except KeyboardInterrupt:
        print("\n\n🛑 IBEX Self-Monitoring stopped by user")
        print("Thanks for using IBEX! 🎉")

    except Exception as e:
        print(f"❌ Error starting IBEX Self-Monitoring: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r python/requirements.txt")
        sys.exit(1)

def show_help():
    """Show help information"""
    print("IBEX Self-Monitoring System")
    print("=" * 30)
    print()
    print("This script starts IBEX in self-monitoring mode, where it will:")
    print("• Watch for changes to its own codebase")
    print("• Analyze contributions using AI")
    print("• Provide quality feedback and suggestions")
    print("• Track contribution history")
    print("• Run automated quality checks")
    print()
    print("Commands:")
    print("  python start_self_monitoring.py    # Start monitoring")
    print("  python run_ibex.py ai analyze-contribution  # Analyze recent changes")
    print("  python run_ibex.py ai quality-check        # Run quality checks")
    print("  python run_ibex.py ai improvement-plan     # Get improvement suggestions")
    print("  python run_ibex.py ai contribution-report  # View contribution history")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
    else:
        asyncio.run(start_ibex_self_monitoring())
