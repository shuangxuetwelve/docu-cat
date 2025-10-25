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

## Current Features

- ✅ Detects and prints changed files in pull requests
- 🚧 Document generation (coming soon)
- 🚧 Local execution mode (coming soon)

## Development

### Project Structure

```
docu-cat/
├── action.yml              # GitHub Action definition
├── detect_changes.py       # Main script for detecting PR changes
├── AGENTS.md              # Project guidelines and task list
└── .github/
    └── workflows/
        └── example.yml    # Example workflow configuration
```

### Implementation Details

- Built with Python 3.11+
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
