# DocuCat 🐱📄

An AI assistant that generates or updates documents from changes in a GitHub pull request.

## Overview

DocuCat is a GitHub Action that analyzes pull request changes and helps maintain documentation. It can:
- Detect changed files in pull requests
- Generate or update documentation based on code changes
- Run as a GitHub Action in any repository
- Run locally for development and testing

## Quick Start

### Using DocuCat as a GitHub Action

1. Add your OpenRouter API key as a repository secret:
   - Go to your repository Settings → Secrets and variables → Actions
   - Create a new secret named `OPENROUTER_API_KEY`
   - Get your API key from https://openrouter.ai/keys
   - Paste your OpenRouter API key value

2. Create a workflow file in your repository at `.github/workflows/docu-cat.yml`:

```yaml
name: DocuCat - Document Generator

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  docu-cat:
    runs-on: ubuntu-latest
    name: Generate/Update Documentation

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run DocuCat
        uses: lu/docu-cat@main  # Replace with actual repository path
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          openrouter-api-key: ${{ secrets.OPENROUTER_API_KEY }}
```

3. Create an `AGENTS.md` file in your repository root to help DocuCat understand your codebase structure (optional but recommended).

4. Open a pull request and DocuCat will automatically run!

### Running DocuCat Locally

You can run DocuCat locally to analyze recent commits in any repository:

1. Set your OpenRouter API key (choose one method):

   **Option A: Using .env file (recommended)**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and add your API key
   # OPENROUTER_API_KEY=your-actual-api-key-here
   ```

   **Option B: Using environment variable**
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```

   Get your API key from https://openrouter.ai/keys

2. Install uv (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Run DocuCat using uv:
   ```bash
   # Analyze last commit in current directory
   uv run python main.py

   # Analyze last 5 commits
   uv run python main.py --count 5

   # Analyze another repository
   uv run python main.py --path /path/to/repo --count 10
   ```

4. Or install and use the CLI command:
   ```bash
   # Install locally
   uv pip install -e .

   # Run from anywhere
   docu-cat --count 5
   docu-cat --path ../other-repo --count 10
   ```

**Command line options:**
- `-p, --path`: Path to repository (default: current directory)
- `-c, --count`: Number of recent commits to analyze (default: 1)

**Note:** DocuCat requires an OpenRouter API key to analyze changes with Claude Haiku 3.5.
- Get your API key from https://openrouter.ai/keys
- Store it in a `.env` file (recommended) or set as an environment variable
- OpenRouter provides access to Claude and many other LLMs through a unified API

## Current Features

- ✅ Detects and prints changed files in pull requests
- ✅ AI-powered change analysis using Claude Haiku 3.5 via OpenRouter and LangChain
- ✅ Understands the intent and purpose of code changes
- ✅ Local execution mode - analyze commits in any repository
- ✅ CLI interface with flexible options
- 🚧 Document generation (coming soon)

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

### Local Setup

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/lu/docu-cat.git
   cd docu-cat
   ```

3. Run scripts using uv:
   ```bash
   uv run python detect_changes.py
   ```

### Project Structure

```
docu-cat/
├── action.yml              # GitHub Action definition
├── pyproject.toml         # Python project configuration
├── AGENTS.md              # Project guidelines and task list
├── __init__.py            # Package initialization
├── main.py                # CLI entry point for local execution
├── detect_changes.py      # GitHub Action script for PR changes
├── analyzer.py            # LangGraph workflow for AI analysis
└── .github/
    └── workflows/
        └── example.yml    # Example workflow configuration
```

### Implementation Details

- Built with Python 3.12+
- Managed with uv for fast, reliable dependency management
- Uses LangGraph for AI workflow orchestration
- Powered by Claude 3.5 Haiku via OpenRouter for intelligent change analysis
- LangChain integration for LLM abstraction
- Integrates with GitHub API for PR analysis
- OpenRouter provides unified access to multiple LLM providers

## How It Works

When a pull request is created or updated:

1. DocuCat checks out the repository
2. Detects changed files between base and head commits
3. Analyzes changes using Claude Haiku 3.5 via OpenRouter and LangGraph to understand the intent
4. Determines the type of change (feature, bugfix, refactor, etc.) and affected areas
5. (Coming soon) Reads `AGENTS.md` to understand code/document structure
6. (Coming soon) Generates or updates relevant documentation
7. Prints the analysis results

## Contributing

DocuCat is currently under construction. See `AGENTS.md` for the task list and development guidelines.

## License

MIT License
