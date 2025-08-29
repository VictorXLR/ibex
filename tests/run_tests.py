#!/usr/bin/env python3
"""
Comprehensive test runner for IBEX AI fixes
"""

import sys
import subprocess
import os
from pathlib import Path

# Add the python directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

def run_test_file(test_file):
    """Run a specific test file and return results"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print('='*60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False

def run_all_tests():
    """Run all test files"""
    test_files = [
        "test_ai_config.py",
        "test_ai_manager.py", 
        "test_contrib_monitor.py",
        "test_self_monitor.py",
        "test_error_handling.py",
        "test_cli_commands.py",
        "test_chat.py",
        "test_chat_context.py",
        "test_chat_functionality.py",
        "test_enhanced_analysis.py",
        "simple_test.py",
        "test_ollama.py",
        "simple_ollama_test.py"
    ]
    
    print("🚀 Running IBEX AI Tests")
    print(f"Testing fixes for issues identified in terminal selection:")
    print("1. ✅ Incomplete Implementation → Comprehensive analysis logic")
    print("2. ✅ Missing Configuration → Full configuration management")  
    print("3. ✅ Limited Error Handling → Robust error handling with retry")
    print()
    
    results = {}
    total_tests = len(test_files)
    passed_tests = 0
    
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            success = run_test_file(str(test_path))
            results[test_file] = success
            if success:
                passed_tests += 1
        else:
            print(f"⚠️ Test file not found: {test_file}")
            results[test_file] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    for test_file, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_file}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} test files passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! IBEX AI fixes are working correctly.")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test file(s) failed.")
        return False

def run_specific_test(test_name):
    """Run a specific test by name"""
    test_files = {
        "config": "test_ai_config.py",
        "manager": "test_ai_manager.py",
        "contrib": "test_contrib_monitor.py", 
        "self": "test_self_monitor.py",
        "error": "test_error_handling.py",
        "cli": "test_cli_commands.py",
        "chat": "test_chat.py",
        "context": "test_chat_context.py",
        "functionality": "test_chat_functionality.py",
        "analysis": "test_enhanced_analysis.py",
        "simple": "simple_test.py",
        "ollama": "test_ollama.py",
        "ollama-simple": "simple_ollama_test.py"
    }
    
    if test_name in test_files:
        test_file = test_files[test_name]
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            return run_test_file(str(test_path))
        else:
            print(f"Test file not found: {test_file}")
            return False
    else:
        print(f"Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_files.keys())}")
        return False

def check_dependencies():
    """Check if test dependencies are available"""
    try:
        import pytest
        print("✅ pytest available")
    except ImportError:
        print("❌ pytest not available. Install with: pip install pytest")
        return False
        
    try:
        import yaml
        print("✅ PyYAML available")
    except ImportError:
        print("❌ PyYAML not available. Install with: pip install PyYAML")
        return False
        
    return True

if __name__ == "__main__":
    print("🔧 Checking test dependencies...")
    if not check_dependencies():
        print("\n⚠️ Missing dependencies. Please install required packages.")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
