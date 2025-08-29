# ibex/cli.py
import typer
from rich.console import Console
from pathlib import Path
from .core import IbexWatcher
import time
from .telemetry import TelemetryClient
import asyncio
import os

app = typer.Typer()
console = Console()
telemetry = TelemetryClient()

def show_mascot(message: str = ""):
    console.print(f"""
    /|      __
   / |   .-'  '-.
  /  |  /  .-.  \\
 |   | |  /   \\  |
 |   | | |     | |
 |   | |  \\   /  |
 |   |   '-.__.'
 |   |    (◕‿◕)    {message}
 |   |     IBEX
 |   |
    """)

@app.command()
def init(
    path: str = typer.Argument(".", help="Project path"),
    intent: str = typer.Option(..., "--intent", "-i", help="What are you building?")
):
    """Start IBEX watching your project"""
    show_mascot("Initializing...")
    telemetry.log_event("init", {"path": path, "intent": intent})
    watcher = IbexWatcher(path, intent)
    try:
        watcher.start()
        console.print(f"[green]IBEX is watching {path}[/green]")
        console.print("[blue]Press Ctrl+C to stop[/blue]")
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        console.print("\n[yellow]IBEX stopped watching[/yellow]")
    except Exception as e:
        telemetry.log_event("error", {"error": str(e)})
        watcher.stop()
        console.print(f"\n[red]Error: {e}[/red]")

@app.command()
async def stake(
    name: str = typer.Argument(..., help="Stake point name"),
    message: str = typer.Argument(..., help="What did you accomplish?")
):
    """Create a stake point to mark your progress"""
    show_mascot("Creating stake point...")
    watcher = IbexWatcher(".")
    await watcher.create_stake(name, message)
    console.print(f"[green]Created stake point: {name}[/green]")

@app.command()
def status(
    path: str = typer.Argument(".", help="Project path")
):
    """Show current IBEX and Git status"""
    watcher = IbexWatcher(path)
    state = watcher.load_state()
    
    console.print("\n[bold]Current Changes:[/bold]")
    for change in state['changes']:
        console.print(f"• {change['summary']}")
    
    console.print("\n[bold]Uncommitted Git Changes:[/bold]")
    for file in watcher.git.get_uncommitted_changes():
        console.print(f"• {file}")

@app.command()
def history(
    path: str = typer.Argument(".", help="Project path")
):
    """Show semantic change history"""
    watcher = IbexWatcher(path)
    history = watcher.llm.get_semantic_history()

    if not history:
        console.print("[yellow]No semantic history found[/yellow]")
        return

    for entry in history:
        console.print(f"\n[bold blue]{entry['timestamp']}[/bold blue]")
        console.print(f"[bold]Intent:[/bold] {entry['intent']}")
        console.print(f"[bold]Description:[/bold]\n{entry['description']}")
        console.print("\n[dim]" + "-"*50 + "[/dim]")

# AI Management Commands
ai_app = typer.Typer()
app.add_typer(ai_app, name="ai", help="AI management commands")

@ai_app.command("providers")
def list_providers():
    """List available AI providers"""
    try:
        from .ai import AIManager
        manager = AIManager()
        providers = manager.list_providers()

        console.print("[bold]Available AI Providers:[/bold]")
        for provider in providers:
            status = "[green]✓[/green]" if manager.provider == provider else "[dim]-[/dim]"
            console.print(f"{status} {provider}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@ai_app.command("config")
def configure_ai(
    provider: str = typer.Option(None, help="AI provider (openai, claude, ollama)"),
    model: str = typer.Option(None, help="Model name"),
    test: bool = typer.Option(False, "--test", help="Test the configuration")
):
    """Configure AI settings"""
    try:
        from .ai import AIManager

        if provider:
            os.environ['IBEX_AI_PROVIDER'] = provider
            if model:
                os.environ[f'{provider.upper()}_MODEL'] = model

        manager = AIManager(provider, model)

        if test:
            console.print("Testing AI configuration...")
            valid, message = manager.validate_config()
            if valid:
                # Test with a simple prompt
                test_messages = [{"role": "user", "content": "Hello, can you respond with just 'OK'?"}]
                try:
                    import asyncio
                    response = asyncio.run(manager.chat(test_messages))
                    console.print(f"[green]✓ Test successful: {response.strip()}[/green]")
                except Exception as e:
                    console.print(f"[red]✗ Test failed: {e}[/red]")
            else:
                console.print(f"[red]✗ Configuration invalid: {message}[/red]")
        else:
            console.print(f"[bold]Current AI Configuration:[/bold]")
            console.print(f"Provider: {manager.provider}")
            console.print(f"Model: {manager.model}")
            valid, message = manager.validate_config()
            status = "[green]✓ Valid[/green]" if valid else f"[red]✗ {message}[/red]"
            console.print(f"Status: {status}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@ai_app.command("chat")
def ai_chat(
    message: str = typer.Argument(..., help="Message to send to AI"),
    provider: str = typer.Option(None, help="AI provider to use"),
    model: str = typer.Option(None, help="Model to use")
):
    """Chat with AI"""
    try:
        from .ai import AIManager
        import asyncio

        manager = AIManager(provider, model)
        messages = [{"role": "user", "content": message}]

        with console.status("[bold green]Thinking...[/bold green]"):
            response = asyncio.run(manager.chat(messages))

        console.print(f"\n[bold blue]AI Response:[/bold blue]")
        console.print(response)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@ai_app.command("models")
def list_models(provider: str = typer.Argument(..., help="Provider to list models for")):
    """List available models for a provider"""
    try:
        if provider == 'openai':
            from .ai.providers.openai_provider import OpenAIProvider
            models = OpenAIProvider.get_available_models()
        elif provider == 'claude':
            from .ai.providers.anthropic_provider import ClaudeProvider
            models = ClaudeProvider.get_available_models()
        elif provider == 'ollama':
            from .ai.providers.ollama_provider import OllamaProvider
            models = OllamaProvider.get_available_models()
        else:
            console.print(f"[red]Unknown provider: {provider}[/red]")
            return

        console.print(f"[bold]Available {provider} models:[/bold]")
        for model in models:
            console.print(f"• {model}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@ai_app.command("self-monitor")
def start_self_monitoring():
    """Start IBEX self-monitoring mode"""
    try:
        import asyncio
        from .ai.self_monitor import IBEXSelfMonitor

        monitor = IBEXSelfMonitor()
        console.print("[green]🐙 Starting IBEX Self-Monitoring[/green]")
        console.print("IBEX will now watch its own codebase for improvements!")

        asyncio.run(monitor.start_self_monitoring())

    except Exception as e:
        console.print(f"[red]Error starting self-monitoring: {e}[/red]")

@ai_app.command("analyze-contribution")
def analyze_contribution():
    """Analyze recent contributions to IBEX"""
    try:
        import asyncio
        from .ai.self_monitor import IBEXSelfMonitor

        monitor = IBEXSelfMonitor()

        with console.status("[bold green]Analyzing recent contributions...[/bold green]"):
            result = asyncio.run(monitor.analyze_recent_changes())

        if result['status'] == 'no_changes':
            console.print("[yellow]No uncommitted changes found to analyze[/yellow]")
            return

        if result['status'] == 'error':
            console.print(f"[red]Analysis error: {result['message']}[/red]")
            return

        # Display analysis results
        analysis = result['analysis']
        console.print(f"\n[bold blue]📊 Contribution Analysis[/bold blue]")
        console.print(f"Quality Score: [bold]{analysis.get('quality_score', 0)}/10[/bold]")
        console.print(f"Files Analyzed: {result.get('files_analyzed', 0)}")
        console.print(f"Categories: {', '.join(analysis.get('categories', {}).keys())}")

        # Show feedback
        if analysis.get('feedback'):
            console.print(f"\n[green]✅ Feedback:[/green]")
            for feedback in analysis['feedback']:
                console.print(f"  {feedback}")

        # Show suggestions
        if analysis.get('suggestions'):
            console.print(f"\n[blue]💡 Suggestions:[/blue]")
            for suggestion in analysis['suggestions']:
                console.print(f"  {suggestion}")

        # Show AI analysis
        ai_analysis = analysis.get('ai_analysis', {})
        if 'analysis' in ai_analysis:
            console.print(f"\n[purple]🤖 AI Analysis ({ai_analysis.get('provider', 'unknown')}):[/purple]")
            # Show first 500 chars of AI analysis
            analysis_text = ai_analysis['analysis'][:500]
            if len(ai_analysis['analysis']) > 500:
                analysis_text += "..."
            console.print(f"  {analysis_text}")

    except Exception as e:
        console.print(f"[red]Error analyzing contributions: {e}[/red]")

@ai_app.command("quality-check")
def run_quality_checks():
    """Run quality checks on IBEX codebase"""
    try:
        from .ai.self_monitor import IBEXSelfMonitor

        # Get configured provider from environment
        provider = os.getenv('IBEX_AI_PROVIDER', 'ollama')
        model = None
        if provider == 'ollama':
            model = os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')
        elif provider == 'claude':
            model = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
        else:  # openai
            model = os.getenv('OPENAI_MODEL', 'gpt-4')

        monitor = IBEXSelfMonitor(provider, model)

        with console.status("[bold green]Running quality checks...[/bold green]"):
            results = monitor.run_quality_checks()

        console.print("[bold blue]🔍 Quality Check Results[/bold blue]")

        # Python quality
        py_check = results.get('python_linting', {})
        if py_check.get('status') == 'checked':
            console.print(f"[green]✅ Python Code:[/green] {py_check['files_checked']} files checked")
            if py_check.get('issues'):
                console.print(f"   Issues found: {py_check['issues_count']}")
                for issue in py_check['issues'][:5]:  # Show first 5 issues
                    console.print(f"   • {issue}")
        else:
            console.print(f"[red]❌ Python Check: {py_check.get('message', 'Failed')}[/red]")

        # Go build
        go_check = results.get('go_build', {})
        if go_check.get('status') == 'success':
            console.print(f"[green]✅ Go Build: Successful[/green]")
        else:
            console.print(f"[red]❌ Go Build: {go_check.get('message', 'Failed')}[/red]")
            if go_check.get('error'):
                console.print(f"   Error: {go_check['error'][:200]}...")

        # Dependencies
        dep_check = results.get('dependencies', {})
        if dep_check.get('status') == 'found':
            console.print(f"[green]✅ Dependencies: {dep_check.get('dependencies', 0)} packages found[/green]")
        else:
            console.print(f"[red]❌ Dependencies: {dep_check.get('message', 'Missing')}[/red]")

        # Documentation
        doc_check = results.get('documentation', {})
        if doc_check.get('status') == 'checked':
            docs = doc_check.get('documents', [])
            console.print(f"[green]✅ Documentation: {len(docs)} files found[/green]")
            for doc in docs:
                console.print(f"   • {doc['file']}: {doc['lines']} lines")
        else:
            console.print(f"[red]❌ Documentation: {doc_check.get('message', 'Missing')}[/red]")

    except Exception as e:
        console.print(f"[red]Error running quality checks: {e}[/red]")

@ai_app.command("improvement-plan")
def generate_improvement_plan():
    """Generate a self-improvement plan for IBEX"""
    try:
        import asyncio
        from .ai.self_monitor import IBEXSelfMonitor

        monitor = IBEXSelfMonitor()

        with console.status("[bold green]Generating improvement plan...[/bold green]"):
            plan = asyncio.run(monitor.generate_self_improvement_plan())

        console.print("[bold blue]🚀 IBEX Self-Improvement Plan[/bold blue]")
        console.print(plan)

    except Exception as e:
        console.print(f"[red]Error generating improvement plan: {e}[/red]")

@ai_app.command("contribution-report")
def generate_contribution_report():
    """Generate a contribution report for IBEX"""
    try:
        from .ai.contrib_monitor import ContributionMonitor

        monitor = ContributionMonitor()
        report = monitor.generate_contribution_report()

        console.print(report)

    except Exception as e:
        console.print(f"[red]Error generating contribution report: {e}[/red]")

if __name__ == "__main__":
    app()