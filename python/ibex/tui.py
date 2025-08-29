# ibex/tui.py
"""
Textual User Interface for IBEX - Intelligent Development Companion
"""

import asyncio
from pathlib import Path
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, Footer, Header, Input, Label, ListItem, ListView,
    Markdown, Placeholder, Static, TextArea, Tree
)
from textual.widgets.tree import TreeNode
from textual.binding import Binding
from textual import events
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .core import IbexWatcher
from .telemetry import TelemetryClient
from .ai import AIManager


class DashboardScreen(Screen):
    """Main dashboard showing current status and activity"""

    BINDINGS = [
        Binding("d", "switch_mode('dashboard')", "Dashboard"),
        Binding("s", "switch_mode('stake')", "Stake Points"),
        Binding("c", "switch_mode('chat')", "AI Chat"),
        Binding("a", "switch_mode('ai')", "AI Config"),
        Binding("h", "switch_mode('history')", "History"),
        Binding("m", "switch_mode('monitor')", "Self-Monitor"),
        Binding("t", "switch_mode('telemetry')", "Telemetry"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.watcher = IbexWatcher(".")
        self.telemetry = TelemetryClient()
        self.ai_manager = AIManager()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Vertical():
                with Horizontal():
                    with Vertical(id="status-panel"):
                        yield Static("📊 Current Status", id="status-title")
                        yield Static("", id="status-content")
                    with Vertical(id="changes-panel"):
                        yield Static("📝 Recent Changes", id="changes-title")
                        yield ListView(id="changes-list")
                with Horizontal():
                    with Vertical(id="stakes-panel"):
                        yield Static("🎯 Recent Stakes", id="stakes-title")
                        yield ListView(id="stakes-list")
                    with Vertical(id="activity-panel"):
                        yield Static("⚡ Activity Feed", id="activity-title")
                        yield ListView(id="activity-list")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_dashboard()

    async def refresh_dashboard(self) -> None:
        """Refresh all dashboard data"""
        await self.update_status()
        await self.update_changes()
        await self.update_stakes()
        await self.update_activity()

    async def update_status(self) -> None:
        """Update status panel"""
        state = self.watcher.load_state()
        intent = state.get('intent', 'No intent set')

        status_content = f"""[bold]Project Intent:[/bold] {intent}
[bold]Total Stakes:[/bold] {len(state.get('stakes', []))}
[bold]Active Changes:[/bold] {len(state.get('changes', []))}
[bold]AI Provider:[/bold] {self.ai_manager.provider}
[bold]AI Model:[/bold] {self.ai_manager.model}"""

        status_widget = self.query_one("#status-content", Static)
        status_widget.update(status_content)

    async def update_changes(self) -> None:
        """Update changes list"""
        changes_list = self.query_one("#changes-list", ListView)
        changes_list.clear()

        state = self.watcher.load_state()
        for change in state.get('changes', [])[-10:]:  # Last 10 changes
            changes_list.append(ListItem(Label(f"{change['timestamp'][:19]} - {change['summary']}")))

        if not state.get('changes'):
            changes_list.append(ListItem(Label("No recent changes")))

    async def update_stakes(self) -> None:
        """Update stakes list"""
        stakes_list = self.query_one("#stakes-list", ListView)
        stakes_list.clear()

        state = self.watcher.load_state()
        for stake in state.get('stakes', [])[-5:]:  # Last 5 stakes
            stakes_list.append(ListItem(Label(f"{stake['timestamp'][:19]} - {stake['name']}")))

        if not state.get('stakes'):
            stakes_list.append(ListItem(Label("No stakes created yet")))

    async def update_activity(self) -> None:
        """Update activity feed"""
        activity_list = self.query_one("#activity-list", ListView)
        activity_list.clear()

        # Get recent telemetry events
        events = self.telemetry.get_recent_events(10)
        for event in events:
            activity_list.append(ListItem(Label(f"{event['timestamp'][:19]} - {event['event']}")))

        if not events:
            activity_list.append(ListItem(Label("No recent activity")))

    def action_switch_mode(self, mode: str) -> None:
        """Switch to different screen mode"""
        if mode == "dashboard":
            pass  # Already on dashboard
        elif mode == "stake":
            self.app.push_screen(StakeScreen())
        elif mode == "chat":
            self.app.push_screen(ChatScreen())
        elif mode == "ai":
            self.app.push_screen(AIConfigScreen())
        elif mode == "history":
            self.app.push_screen(HistoryScreen())
        elif mode == "monitor":
            self.app.push_screen(MonitorScreen())
        elif mode == "telemetry":
            self.app.push_screen(TelemetryScreen())


class StakeScreen(Screen):
    """Screen for managing stake points"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("n", "new_stake", "New Stake"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.watcher = IbexWatcher(".")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Vertical():
                yield Static("🎯 Stake Point Management", id="title")
                with Horizontal():
                    yield Button("New Stake", id="new-stake-btn", variant="primary")
                    yield Button("Refresh", id="refresh-btn")
                yield ListView(id="stakes-list")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_stakes()

    async def refresh_stakes(self) -> None:
        """Refresh stakes list"""
        stakes_list = self.query_one("#stakes-list", ListView)
        stakes_list.clear()

        state = self.watcher.load_state()
        for stake in reversed(state.get('stakes', [])):
            stake_info = f"""[bold]{stake['name']}[/bold]
{stake['message']}
[italic]{stake['timestamp'][:19]}[/italic]
Changes: {len(stake.get('changes', []))}"""
            stakes_list.append(ListItem(Label(stake_info)))

        if not state.get('stakes'):
            stakes_list.append(ListItem(Label("No stakes created yet")))

    def action_back(self) -> None:
        """Go back to dashboard"""
        self.app.pop_screen()

    def action_new_stake(self) -> None:
        """Create new stake"""
        self.app.push_screen(NewStakeScreen())

    def action_refresh(self) -> None:
        """Refresh stakes"""
        asyncio.create_task(self.refresh_stakes())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-stake-btn":
            self.action_new_stake()
        elif event.button.id == "refresh-btn":
            await self.refresh_stakes()


class NewStakeScreen(Screen):
    """Screen for creating new stake points"""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "create", "Create Stake"),
    ]

    def __init__(self):
        super().__init__()
        self.watcher = IbexWatcher(".")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Vertical():
                yield Static("🎯 Create New Stake Point", id="title")
                yield Label("Stake Name:")
                yield Input(placeholder="Enter stake point name", id="stake-name")
                yield Label("Description:")
                yield TextArea("", id="stake-description")
                with Horizontal():
                    yield Button("Create", id="create-btn", variant="primary")
                    yield Button("Cancel", id="cancel-btn")
        yield Footer()

    def action_cancel(self) -> None:
        """Cancel stake creation"""
        self.app.pop_screen()

    def action_create(self) -> None:
        """Create the stake"""
        asyncio.create_task(self.create_stake())

    async def create_stake(self) -> None:
        """Create stake point"""
        name_input = self.query_one("#stake-name", Input)
        desc_input = self.query_one("#stake-description", TextArea)

        name = name_input.value.strip()
        description = desc_input.text.strip()

        if not name or not description:
            # Show error message
            return

        try:
            await self.watcher.create_stake(name, description)
            self.app.pop_screen()  # Go back to stake screen
            self.app.pop_screen()  # Go back to dashboard
        except Exception as e:
            # Show error message
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            await self.create_stake()
        elif event.button.id == "cancel-btn":
            self.action_cancel()


class ChatScreen(Screen):
    """AI Chat interface screen"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("ctrl+enter", "send", "Send"),
    ]

    def __init__(self):
        super().__init__()
        self.ai_manager = None
        self.messages = []
        self.conversation_history = []
        self._ai_available = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Vertical():
                yield Static("🤖 AI Chat", id="title")
                yield ListView(id="messages-list")
                with Horizontal():
                    yield Input(placeholder="Type your message...", id="message-input")
                    yield Button("Send", id="send-btn", variant="primary")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize AI manager and check availability"""
        try:
            self.ai_manager = AIManager()
            self._ai_available = self.ai_manager.is_available()

            if self._ai_available:
                welcome_msg = f"🤖 AI Chat Ready!\nProvider: {self.ai_manager.provider}\nModel: {self.ai_manager.model}\n\nAsk me anything about your project!"
            else:
                welcome_msg = "❌ AI Chat Unavailable\n\nPlease configure an AI provider:\n• Set OPENAI_API_KEY for OpenAI GPT\n• Or install Ollama for local models\n\nRun: python run_ibex.py ai config"

            self.messages.append({"role": "assistant", "content": welcome_msg})
            await self.update_messages()

        except Exception as e:
            error_msg = f"❌ Failed to initialize AI: {str(e)}\n\nPlease check your AI provider configuration."
            self.messages.append({"role": "assistant", "content": error_msg})
            await self.update_messages()

    def action_back(self) -> None:
        """Go back to dashboard"""
        self.app.pop_screen()

    def action_send(self) -> None:
        """Send message"""
        # Schedule the async task properly
        self.app.call_next_tick(self._send_message_async)

    def _send_message_async(self) -> None:
        """Helper to run async send in Textual's event loop"""
        asyncio.create_task(self.send_message())

    async def send_message(self) -> None:
        """Send message to AI with enhanced context"""
        input_widget = self.query_one("#message-input", Input)
        message = input_widget.value.strip()

        if not message:
            return

        # Check if AI is available
        if not self._ai_available or not self.ai_manager:
            error_msg = "❌ AI is not available. Please configure an AI provider first."
            self.messages.append({"role": "assistant", "content": error_msg})
            await self.update_messages()
            return

        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.messages.append({"role": "user", "content": message})

        # Update UI immediately
        await self.update_messages()

        # Clear input
        input_widget.value = ""

        # Show typing indicator
        self.messages.append({"role": "assistant", "content": "🤖 Thinking..."})
        await self.update_messages()

        # Get AI response with enhanced context
        try:
            # Use the enhanced chat method with project context
            response = await self.ai_manager.chat_with_context(
                user_message=message,
                conversation_history=self.conversation_history[:-2],  # Exclude current message and typing indicator
                include_project_context=True
            )

            # Remove typing indicator and add real response
            self.messages.pop()  # Remove typing indicator
            self.conversation_history.append({"role": "assistant", "content": response})
            self.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            # Remove typing indicator and add error
            self.messages.pop()  # Remove typing indicator
            error_msg = f"❌ Chat Error: {str(e)}\n\nTroubleshooting:\n• Run 'python run_ibex.py ai diagnose' for help\n• Check AI provider configuration\n• Ensure AI service is running"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            self.messages.append({"role": "assistant", "content": error_msg})

        # Update UI with final response
        await self.update_messages()

    async def update_messages(self) -> None:
        """Update messages display"""
        messages_list = self.query_one("#messages-list", ListView)
        messages_list.clear()

        for msg in self.messages[-20:]:  # Show last 20 messages
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            content = msg["content"]
            if len(content) > 200:
                content = content[:200] + "..."
            messages_list.append(ListItem(Label(f"{role_icon} {content}")))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.action_send()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key press in input field"""
        if event.input.id == "message-input":
            self.action_send()


class AIConfigScreen(Screen):
    """AI Configuration screen"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.ai_manager = AIManager()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Vertical():
                yield Static("⚙️ AI Configuration", id="title")
                yield ListView(id="providers-list")
                with Horizontal():
                    yield Button("Refresh", id="refresh-btn")
                    yield Button("Test Config", id="test-btn", variant="primary")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_config()

    def action_back(self) -> None:
        """Go back to dashboard"""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh configuration"""
        asyncio.create_task(self.refresh_config())

    async def refresh_config(self) -> None:
        """Refresh AI configuration display"""
        providers_list = self.query_one("#providers-list", ListView)
        providers_list.clear()

        providers = self.ai_manager.list_providers()
        current_provider = self.ai_manager.provider
        current_model = self.ai_manager.model

        for provider in providers:
            status = "✓ ACTIVE" if provider == current_provider else "○ inactive"
            info = f"""[bold]{provider.upper()}[/bold] - {status}
Current Model: {current_model if provider == current_provider else 'N/A'}
Status: {'Valid' if self.ai_manager.validate_config()[0] else 'Invalid'}"""
            providers_list.append(ListItem(Label(info)))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-btn":
            await self.refresh_config()
        elif event.button.id == "test-btn":
            await self.test_config()

    async def test_config(self) -> None:
        """Test AI configuration"""
        test_messages = [{"role": "user", "content": "Hello, respond with 'OK'"}]
        try:
            response = await self.ai_manager.chat(test_messages)
            # Show success message
        except Exception as e:
            # Show error message
            pass


class HistoryScreen(Screen):
    """History viewer screen"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.watcher = IbexWatcher(".")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Vertical():
                yield Static("📚 Semantic History", id="title")
                yield Button("Refresh", id="refresh-btn")
                yield ListView(id="history-list")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_history()

    def action_back(self) -> None:
        """Go back to dashboard"""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh history"""
        asyncio.create_task(self.refresh_history())

    async def refresh_history(self) -> None:
        """Refresh history display"""
        history_list = self.query_one("#history-list", ListView)
        history_list.clear()

        history = self.watcher.llm.get_semantic_history()

        if not history:
            history_list.append(ListItem(Label("No semantic history found")))
            return

        for entry in reversed(history):
            history_info = f"""[bold]{entry['timestamp'][:19]}[/bold]
[italic]Intent:[/italic] {entry.get('intent', 'N/A')}
[italic]Description:[/italic] {entry.get('description', 'N/A')[:200]}..."""
            history_list.append(ListItem(Label(history_info)))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-btn":
            await self.refresh_history()


class MonitorScreen(Screen):
    """Self-monitoring dashboard screen"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quality_check", "Quality Check"),
        Binding("a", "analyze", "Analyze"),
    ]

    def __init__(self):
        super().__init__()
        try:
            from .ai.self_monitor import IBEXSelfMonitor
            self.monitor = IBEXSelfMonitor()
        except ImportError:
            self.monitor = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Vertical():
                yield Static("🐙 IBEX Self-Monitoring", id="title")
                with Horizontal():
                    yield Button("Quality Check", id="quality-btn", variant="primary")
                    yield Button("Analyze Changes", id="analyze-btn")
                    yield Button("Refresh", id="refresh-btn")
                yield Static("", id="results-content")
        yield Footer()

    def action_back(self) -> None:
        """Go back to dashboard"""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh monitoring data"""
        asyncio.create_task(self.refresh_monitor())

    def action_quality_check(self) -> None:
        """Run quality check"""
        asyncio.create_task(self.run_quality_check())

    def action_analyze(self) -> None:
        """Analyze recent changes"""
        asyncio.create_task(self.analyze_changes())

    async def refresh_monitor(self) -> None:
        """Refresh monitoring display"""
        if not self.monitor:
            self.query_one("#results-content", Static).update("Self-monitoring not available")
            return

        # Get recent analysis or status
        results_widget = self.query_one("#results-content", Static)
        results_widget.update("Monitoring data refreshed")

    async def run_quality_check(self) -> None:
        """Run quality check"""
        if not self.monitor:
            return

        results_widget = self.query_one("#results-content", Static)
        results_widget.update("Running quality checks...")

        try:
            results = self.monitor.run_quality_checks()
            results_text = "🔍 Quality Check Results\n\n"

            # Python quality
            py_check = results.get('python_linting', {})
            if py_check.get('status') == 'checked':
                results_text += f"✅ Python: {py_check['files_checked']} files, {py_check.get('issues_count', 0)} issues\n"
            else:
                results_text += f"❌ Python: {py_check.get('message', 'Failed')}\n"

            # Dependencies
            dep_check = results.get('dependencies', {})
            if dep_check.get('status') == 'found':
                results_text += f"✅ Dependencies: {dep_check.get('dependencies', 0)} packages\n"
            else:
                results_text += f"❌ Dependencies: {dep_check.get('message', 'Missing')}\n"

            results_widget.update(results_text)

        except Exception as e:
            results_widget.update(f"Error running quality check: {str(e)}")

    async def analyze_changes(self) -> None:
        """Analyze recent changes with enhanced context"""
        if not self.monitor:
            return

        results_widget = self.query_one("#results-content", Static)
        results_widget.update("🔍 Performing enhanced analysis with full context...")

        try:
            result = await self.monitor.analyze_recent_changes()

            if result['status'] == 'no_changes':
                results_widget.update("📝 No uncommitted changes found to analyze")
                return

            if result['status'] == 'error':
                results_widget.update(f"❌ Analysis error: {result['message']}")
                return

            analysis = result['analysis']

            # Enhanced display with more details
            analysis_text = f"""📊 Enhanced Contribution Analysis
Quality Score: {analysis.get('quality_score', 0)}/10
Files Analyzed: {result.get('files_analyzed', 0)}
Project Intent: {result.get('project_intent', 'Not specified')}
Analysis Depth: {result.get('analysis_depth', 'Basic')}

🔍 Basic Feedback:
{chr(10).join(f"• {item}" for item in analysis.get('feedback', []))}

💡 Suggestions:
{chr(10).join(f"• {item}" for item in analysis.get('suggestions', []))}
"""

            # Add AI analysis if available
            ai_analysis = analysis.get('ai_analysis', {})
            if 'analysis' in ai_analysis and ai_analysis['analysis']:
                analysis_text += f"""

🤖 AI Analysis ({ai_analysis.get('provider', 'unknown')}):
{ai_analysis['analysis'][:1000]}{'...' if len(ai_analysis['analysis']) > 1000 else ''}
"""

            # Add improvements section
            improvements = result.get('improvements', [])
            if improvements:
                analysis_text += f"""

🚀 Improvement Suggestions:
{chr(10).join(f"• {item}" for item in improvements)}
"""

            # Add capabilities info
            capabilities = result.get('ai_capabilities', {})
            if capabilities:
                analysis_text += f"""

⚡ Analysis Capabilities Used:
{chr(10).join(f"• {k.replace('_', ' ').title()}: {'✅' if v else '❌'}" for k, v in capabilities.items())}
"""

            results_widget.update(analysis_text)

        except Exception as e:
            results_widget.update(f"❌ Error analyzing changes: {str(e)}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quality-btn":
            await self.run_quality_check()
        elif event.button.id == "analyze-btn":
            await self.analyze_changes()
        elif event.button.id == "refresh-btn":
            await self.refresh_monitor()


class TelemetryScreen(Screen):
    """Telemetry viewer screen"""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.telemetry = TelemetryClient()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Vertical():
                yield Static("📊 Telemetry Dashboard", id="title")
                yield Button("Refresh", id="refresh-btn")
                yield Static("", id="telemetry-content")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_telemetry()

    def action_back(self) -> None:
        """Go back to dashboard"""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh telemetry"""
        asyncio.create_task(self.refresh_telemetry())

    async def refresh_telemetry(self) -> None:
        """Refresh telemetry display"""
        telemetry_widget = self.query_one("#telemetry-content", Static)

        events = self.telemetry.get_recent_events(20)
        if not events:
            telemetry_widget.update("No telemetry events found")
            return

        telemetry_text = "📈 Recent Telemetry Events\n\n"
        for event in events:
            telemetry_text += f"• {event['timestamp'][:19]} - {event['event']}\n"
            if event.get('data'):
                telemetry_text += f"  Data: {str(event['data'])[:100]}...\n"

        telemetry_widget.update(telemetry_text)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-btn":
            await self.refresh_telemetry()


class IBEXTUI(App):
    """Main IBEX TUI Application"""

    CSS = """
    Screen {
        background: $surface;
    }

    #main {
        height: 100%;
        padding: 1;
    }

    #status-panel, #changes-panel, #stakes-panel, #activity-panel {
        width: 50%;
        height: 50%;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }

    #status-title, #changes-title, #stakes-title, #activity-title {
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }

    #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    Button {
        margin: 1;
    }

    ListView {
        height: 100%;
        border: solid $border;
        margin: 1;
    }

    Input {
        margin: 1;
    }

    TextArea {
        height: 20;
        margin: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.title = "🐙 IBEX - Intelligent Development Companion"

    def on_mount(self) -> None:
        """Set up the initial screen"""
        self.push_screen(DashboardScreen())

    async def action_quit(self) -> None:
        """Quit the application"""
        self.exit()


def show_ibex_mascot(message: str = ""):
    """Show IBEX mascot in TUI style"""
    return f"""
    /|      __
   / |   .-'  '-.
  /  |  /  .-.  \\
 |   | |  /   \\  |
 |   | | |     | |
 |   | |  \\   /  |
 |   |   '-.__.'  {message}
 |   |    (◕‿◕)
 |   |     IBEX
 |   |
"""


if __name__ == "__main__":
    app = IBEXTUI()
    app.run()
