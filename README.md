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

1. Create a workflow file in your repository at `.github/workflows/docu-cat.yml`:

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
```

2. Create an `AGENTS.md` file in your repository root to help DocuCat understand your codebase structure (optional but recommended).

3. Open a pull request and DocuCat will automatically run!

### Running DocuCat Locally

You can run DocuCat locally to analyze recent commits in any repository:

1. Install uv (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Run DocuCat using uv:
   ```bash
   # Analyze last commit in current directory
   uv run --no-project src/main.py

   # Analyze last 5 commits
   uv run --no-project src/main.py --count 5

   # Analyze another repository
   uv run --no-project src/main.py --path /path/to/repo --count 10
   ```

3. Or install and use the CLI command:
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

## Current Features

- ✅ Detects and prints changed files in pull requests
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
   uv run src/detect_changes.py
   ```

### Project Structure

```
docu-cat/
├── action.yml              # GitHub Action definition
├── pyproject.toml         # Python project configuration
├── AGENTS.md              # Project guidelines and task list
├── src/                   # Source code directory
│   ├── __init__.py        # Package initialization
│   ├── main.py            # CLI entry point for local execution
│   └── detect_changes.py  # GitHub Action script for PR changes
└── .github/
    └── workflows/
        └── example.yml    # Example workflow configuration
```

### Implementation Details

- Built with Python 3.12+
- Managed with uv for fast, reliable dependency management
- Uses LangGraph for AI orchestration (planned)
- Integrates with GitHub API for PR analysis

## How It Works

When a pull request is created or updated:

1. DocuCat checks out the repository
2. Detects changed files between base and head commits
3. Reads `AGENTS.md` to understand code/document structure
4. Generates or updates relevant documentation
5. Prints the results

## Contributing

DocuCat is currently under construction. See `AGENTS.md` for the task list and development guidelines.

## License

MIT License
