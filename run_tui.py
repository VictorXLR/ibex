#!/usr/bin/env python3
"""
IBEX TUI Launcher
Launches the IBEX Text User Interface
"""

import sys
import os

# Add the python directory to the path so we can import ibex
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

try:
    from ibex.tui import IBEXTUI
    from rich.console import Console

    console = Console()

    def main():
        console.print("[green]🐙 Starting IBEX TUI...[/green]")
        console.print("Use keyboard shortcuts to navigate:")
        console.print("• 'd' - Dashboard")
        console.print("• 's' - Stake Points")
        console.print("• 'c' - AI Chat")
        console.print("• 'a' - AI Configuration")
        console.print("• 'h' - History")
        console.print("• 'm' - Self-Monitoring")
        console.print("• 't' - Telemetry")
        console.print("• 'q' - Quit")
        console.print()

        app = IBEXTUI()
        app.run()

    if __name__ == "__main__":
        main()

except ImportError as e:
    console = Console()
    console.print(f"[red]Error: Could not import IBEX TUI[/red]")
    console.print(f"[red]Make sure dependencies are installed: pip install -r python/requirements.txt[/red]")
    console.print(f"[red]Import error: {e}[/red]")
    sys.exit(1)
except KeyboardInterrupt:
    console.print("\n[yellow]IBEX TUI stopped[/yellow]")
    sys.exit(0)
except Exception as e:
    console = Console()
    console.print(f"[red]Error running IBEX TUI: {e}[/red]")
    sys.exit(1)
