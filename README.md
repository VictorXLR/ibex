# IBEX - Intelligent Development Companion

IBEX is an intelligent development tool that watches your project files, tracks changes, and helps you create meaningful Git commits with AI-powered analysis.

## Features

- **File Watching**: Automatically tracks changes to your project files
- **Stake Points**: Mark your progress with meaningful milestones
- **AI-Powered Commits**: Uses LLM to generate intelligent commit messages
- **Multi-Provider AI**: Support for OpenAI, Anthropic Claude, and Ollama
- **Git Integration**: Seamless integration with Git repositories
- **Semantic History**: Track the semantic meaning of your changes over time
- **Telemetry**: Optional telemetry for development insights
- **AI Chat**: Direct interaction with AI models through CLI

## Installation

### Prerequisites

- Python 3.8 or later
- Git
- Ollama (optional, for local AI models)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ibex
```

2. Install Python dependencies:
```bash
pip install -r python/requirements.txt
```

3. (Optional) Install Ollama for local AI models:
```bash
# Install Ollama from https://ollama.ai/
ollama pull qwen3-coder:30b
```

### Dependencies

The project requires the following Python packages:

- `typer` - CLI framework
- `rich` - Beautiful terminal output
- `watchdog` - File system monitoring
- `openai` - OpenAI GPT integration
- `anthropic` - Anthropic Claude integration
- `ollama` - Ollama local LLM integration
- `gitpython` - Git integration
- `flask` - Telemetry server
- `requests` - HTTP client

## Usage

### Initialize IBEX

Start IBEX watching your project:

```bash
python run_ibex.py init --intent "Building a web application with React and Node.js"
```

This will:
- Create a `.ibex` directory in your project
- Start watching for file changes
- Track your development intent

### Create Stake Points

Mark your progress with stake points:

```bash
python run_ibex.py stake "user-authentication" "Implemented JWT-based authentication system"
```

This will:
- Analyze your changes using AI
- Create a Git commit with an intelligent message
- Store semantic information about the changes
- Clear the change tracking for the next milestone

### Check Status

View current changes and Git status:

```bash
python run_ibex.py status
```

### View History

See your semantic change history:

```bash
python run_ibex.py history
```

### AI Integration

#### Configure AI Provider

Set up your preferred AI provider:

```bash
# Use OpenAI GPT-4 (requires API key)
export OPENAI_API_KEY="your-api-key"
python run_ibex.py ai config --provider openai --model gpt-4

# Use Anthropic Claude (requires API key)
export ANTHROPIC_API_KEY="your-api-key"
python run_ibex.py ai config --provider claude --model claude-3-sonnet-20240229

# Use local Ollama (default, no API key needed)
python run_ibex.py ai config --provider ollama --model qwen3-coder:30b
```

#### Chat with AI

Interact directly with AI models:

```bash
python run_ibex.py ai chat "Help me write a Python function to parse JSON"
```

#### List Available Providers and Models

```bash
# List all available providers
python run_ibex.py ai providers

# List models for a specific provider
python run_ibex.py ai models openai
python run_ibex.py ai models claude
python run_ibex.py ai models ollama
```

#### AI Diagnosis and Troubleshooting

If you're having issues with AI chat or analysis:

```bash
# Diagnose AI connectivity and configuration
python run_ibex.py ai diagnose

# Test your AI configuration
python run_ibex.py ai config --test

# Check available AI providers
python run_ibex.py ai providers
```

The diagnosis tool will:
- Check your AI provider configuration
- Test connectivity to AI services
- Verify chat functionality
- Provide troubleshooting tips

#### Self-Monitoring Features

IBEX includes advanced self-monitoring capabilities to analyze and improve its own codebase:

##### Start Self-Monitoring

```bash
# Start IBEX watching its own codebase
python start_self_monitoring.py

# Or use the CLI command
python run_ibex.py ai self-monitor
```

##### Analyze Contributions

```bash
# Analyze recent contributions to IBEX
python run_ibex.py ai analyze-contribution
```

##### Quality Checks

```bash
# Run comprehensive quality checks
python run_ibex.py ai quality-check
```

##### Generate Improvement Plans

```bash
# Get AI-generated improvement suggestions
python run_ibex.py ai improvement-plan
```

##### Contribution Reports

```bash
# View detailed contribution history and analytics
python run_ibex.py ai contribution-report
```

### Self-Monitoring Features

When IBEX monitors itself, it provides:

- **Real-time Analysis**: Automatic analysis of code changes
- **Quality Scoring**: 1-10 quality assessment of contributions
- **AI Feedback**: Intelligent suggestions for improvements
- **Category Analysis**: Organized feedback by code type (core, AI, docs, etc.)
- **Contribution Tracking**: Historical analysis of all changes
- **Automated Quality Checks**: Python linting, dependency checks, documentation validation
- **Documentation Monitoring**: Ensures docs stay current with code changes



**Chat Features:**
- Enter to send messages
- AI provides project context awareness
- Supports conversation history
- Real-time typing indicators
- Enhanced error handling with diagnostics

**Chat Troubleshooting:**
If chat isn't working:
1. Check AI configuration: `python run_ibex.py ai diagnose`
2. Ensure your AI provider is running (Ollama, etc.)
3. Verify API keys are set for cloud providers
4. Use the diagnosis tool for detailed troubleshooting

### Start Telemetry Server

Start the telemetry server for development insights:

```bash
python run_ibex.py telemetry-server
```

## Configuration

### AI Providers

#### OpenAI
```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_MODEL="gpt-4"  # optional, defaults to gpt-4
```

#### Anthropic Claude
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export ANTHROPIC_MODEL="claude-3-sonnet-20240229"  # optional
```

#### Ollama (Local)
```bash
export OLLAMA_MODEL="qwen3-coder:30b"  # optional, defaults to qwen3-coder:30b
```
Ollama doesn't require an API key as it runs locally.

#### Default Provider
```bash
export IBEX_AI_PROVIDER="ollama"  # or "openai" or "claude"
```

### Telemetry

Telemetry is optional and runs locally. You can start the telemetry server to collect development insights:

```bash
python run_ibex.py telemetry-server
```

The server runs on `http://localhost:5000` by default.

## Project Structure

```
ibex/
├── .ibex/                 # IBEX data directory
│   ├── state.json        # Current state and changes
│   └── semantic.db       # SQLite database for semantic history
├── python/               # Python package directory
│   └── ibex/             # Main IBEX package
│       ├── __init__.py   # Package initialization
│       ├── cli.py        # Command-line interface
│       ├── core.py       # Core functionality
│       ├── ai/           # AI module
│       │   ├── __init__.py   # Unified AI manager
│       │   ├── providers/    # Provider implementations
│       │   │   ├── openai_provider.py
│       │   │   ├── anthropic_provider.py
│       │   │   └── ollama_provider.py
│       │   ├── utils.py      # AI utilities
│       │   ├── self_monitor.py # Self-monitoring system
│       │   ├── contrib_monitor.py # Contribution analysis
│       │   └── README.md     # AI documentation
│       ├── git_integration.py # Git integration
│       ├── telemetry.py      # Telemetry functionality
├── tests/                # Test suite
│   ├── __init__.py
│   ├── debug_ai.py
│   ├── simple_ollama_test.py
│   └── test_ollama.py
├── run_ibex.py          # Main runner script
├── start_self_monitoring.py # Self-monitoring launcher
├── setup.py             # Package installation
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## How It Works

1. **File Watching**: IBEX uses the `watchdog` library to monitor file system changes
2. **Change Tracking**: Changes are tracked with file hashes and timestamps
3. **Git Integration**: Only tracks files that are part of the Git repository
4. **AI Analysis**: When creating stake points, IBEX uses your configured AI provider (Ollama, OpenAI, or Claude) to analyze changes
5. **Semantic Storage**: All semantic information is stored in a local SQLite database

## Examples

### Web Development Workflow

```bash
# Start IBEX for a web project
python run_ibex.py init --intent "Building a React e-commerce application"

# Work on features...
# IBEX automatically tracks your changes

# Create a stake point when you complete a feature
python run_ibex.py stake "product-catalog" "Implemented product listing with search and filtering"

# Check what you've been working on
python run_ibex.py status

# View your development history
python run_ibex.py history
```

### API Development Workflow

```bash
# Start IBEX for an API project
python run_ibex.py init --intent "Building a REST API with Express.js"

# Work on endpoints...
# IBEX tracks your changes

# Create stake points for completed endpoints
python run_ibex.py stake "user-endpoints" "Implemented CRUD operations for user management"
python run_ibex.py stake "auth-middleware" "Added JWT authentication middleware"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
