#!/usr/bin/env python3
"""
IBEX Python Runner
Run IBEX using the Python module directly
"""

import sys
import os
from pathlib import Path

# Add the python directory to the path
python_dir = Path(__file__).parent / "python"
sys.path.insert(0, str(python_dir))

def main():
    """Main entry point for IBEX"""
    try:
        # Import and run IBEX CLI
        from ibex.cli import app
        app()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install typer rich watchdog openai anthropic ollama gitpython flask requests")
        sys.exit(1)
    except Exception as e:
        print(f"Error running IBEX: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
