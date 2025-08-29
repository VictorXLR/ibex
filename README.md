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

- Go 1.16 or later
- Python 3.7 or later
- Git

### Building from Source

1. Clone the repository:
```bash
git clone <repository-url>
cd ibex
```

2. Build the executable:
```bash
./build.sh
```

This will create an `ibex` executable that embeds all the Python dependencies.

### Dependencies

The Python dependencies are automatically installed when you run IBEX for the first time:

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
ibex init --intent "Building a web application with React and Node.js"
```

This will:
- Create a `.ibex` directory in your project
- Start watching for file changes
- Track your development intent

### Create Stake Points

Mark your progress with stake points:

```bash
ibex stake "user-authentication" "Implemented JWT-based authentication system"
```

This will:
- Analyze your changes using AI
- Create a Git commit with an intelligent message
- Store semantic information about the changes
- Clear the change tracking for the next milestone

### Check Status

View current changes and Git status:

```bash
ibex status
```

### View History

See your semantic change history:

```bash
ibex history
```

### AI Integration

#### Configure AI Provider

Set up your preferred AI provider:

```bash
# Use OpenAI GPT-4
export OPENAI_API_KEY="your-api-key"
ibex ai config --provider openai --model gpt-4

# Use Anthropic Claude
export ANTHROPIC_API_KEY="your-api-key"
ibex ai config --provider claude --model claude-3-sonnet-20240229

# Use local Ollama
ibex ai config --provider ollama --model codellama
```

#### Chat with AI

Interact directly with AI models:

```bash
ibex ai chat "Help me write a Python function to parse JSON"
```

#### List Available Providers and Models

```bash
# List all available providers
ibex ai providers

# List models for a specific provider
ibex ai models openai
ibex ai models claude
ibex ai models ollama
```

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
- **Automated Quality Checks**: Python linting, Go builds, dependency checks
- **Documentation Monitoring**: Ensures docs stay current with code changes

### Start Telemetry Server

Start the telemetry server for development insights:

```bash
ibex telemetry-server
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
export OLLAMA_MODEL="codellama"  # optional, defaults to codellama
```
Ollama doesn't require an API key as it runs locally.

#### Default Provider
```bash
export IBEX_AI_PROVIDER="openai"  # or "claude" or "ollama"
```

### Telemetry

Telemetry is optional and runs locally. You can start the telemetry server to collect development insights:

```bash
ibex telemetry-server
```

The server runs on `http://localhost:5000` by default.

## Project Structure

```
ibex/
├── .ibex/                 # IBEX data directory
│   ├── state.json        # Current state and changes
│   └── semantic.db       # SQLite database for semantic history
├── main.go               # Go entry point
├── build.sh              # Build script
├── requirements.txt      # Python dependencies
└── python/ibex/          # Embedded Python code
    ├── ai/               # AI module
    │   ├── __init__.py   # Unified AI manager
    │   ├── providers/    # Provider implementations
    │   │   ├── openai_provider.py
    │   │   ├── anthropic_provider.py
    │   │   └── ollama_provider.py
    │   ├── utils.py      # AI utilities
    │   └── README.md     # AI documentation
    ├── cli.py            # Command-line interface
    ├── core.py           # Core functionality
    ├── llm.py            # Legacy LLM integration
    ├── git_integration.py # Git integration
    └── telemetry.py      # Telemetry functionality
```

## How It Works

1. **File Watching**: IBEX uses the `watchdog` library to monitor file system changes
2. **Change Tracking**: Changes are tracked with file hashes and timestamps
3. **Git Integration**: Only tracks files that are part of the Git repository
4. **LLM Analysis**: When creating stake points, IBEX uses OpenAI's API to analyze changes
5. **Semantic Storage**: All semantic information is stored in a local SQLite database

## Examples

### Web Development Workflow

```bash
# Start IBEX for a web project
ibex init --intent "Building a React e-commerce application"

# Work on features...
# IBEX automatically tracks your changes

# Create a stake point when you complete a feature
ibex stake "product-catalog" "Implemented product listing with search and filtering"

# Check what you've been working on
ibex status

# View your development history
ibex history
```

### API Development Workflow

```bash
# Start IBEX for an API project
ibex init --intent "Building a REST API with Express.js"

# Work on endpoints...
# IBEX tracks your changes

# Create stake points for completed endpoints
ibex stake "user-endpoints" "Implemented CRUD operations for user management"
ibex stake "auth-middleware" "Added JWT authentication middleware"
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
