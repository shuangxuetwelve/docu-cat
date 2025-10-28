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

4. Open a pull request and DocuCat will automatically:
   - Analyze code changes
   - Update documentation if needed
   - Create a commit with the changes (if configured)
   - Post a summary comment to the PR

   See [PR_COMMENT_EXAMPLE.md](docs/PR_COMMENT_EXAMPLE.md) for examples of PR comments.

### Configuring DocuCat via PR Description

You can configure DocuCat on a per-pull-request basis by adding a configuration section to your PR description:

**Add this section to your PR description:**
```markdown
## Configurations of DocuCat

- [x] Enable DocuCat
- [x] Should DocuCat create commits?
```

**Disable DocuCat on a specific PR:**
```markdown
## Configurations of DocuCat

- [ ] Enable DocuCat
- [x] Should DocuCat create commits?
```

**Analyze only (don't create commits):**
```markdown
## Configurations of DocuCat

- [x] Enable DocuCat
- [ ] Should DocuCat create commits?
```

See [CONFIGURATION.md](CONFIGURATION.md) for all configuration options and examples.

### Guiding DocuCat with PR Comments

DocuCat reads and follows developer instructions from PR comments. You can guide what gets documented:

**Give specific instructions:**
```markdown
@DocuCat please update docs/api.md with the new authentication endpoints
```

**Request multiple updates:**
```markdown
DocuCat: update README.md and CHANGELOG.md with the breaking changes
```

**Provide context:**
```markdown
@DocuCat this adds OAuth2 support. Focus on security documentation.
```

See [docs/DEVELOPER_INSTRUCTIONS.md](docs/DEVELOPER_INSTRUCTIONS.md) for complete guide and examples.

### Triggering DocuCat On-Demand via Comments

In addition to automatic triggers on PR creation and updates, you can manually trigger DocuCat by posting a comment on your pull request. This is useful when you want to re-run DocuCat without pushing new commits.

**To trigger DocuCat manually, post a comment with one of these phrases:**

```markdown
@DocuCat
```

```markdown
run docu-cat
```

```markdown
@docu-cat
```

DocuCat will:
1. Detect the trigger phrase in your comment
2. React to your comment with a 🚀 emoji to confirm it's running
3. Analyze the current state of the PR
4. Update documentation if needed
5. Post a summary comment with the results

**Setting up comment-triggered execution:**

Copy the workflow file from `.github/workflows/comment-trigger.yml` to your repository, or add the following workflow:

```yaml
name: DocuCat - Comment Triggered

on:
  issue_comment:
    types: [created]

jobs:
  # ... (see .github/workflows/comment-trigger.yml for complete configuration)
```

**Note:** The comment trigger workflow requires the same permissions and secrets as the automatic workflow (`GITHUB_TOKEN` and `OPENROUTER_API_KEY`).

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
   uv run python run_docu_cat.py

   # Analyze last 5 commits
   uv run python run_docu_cat.py --count 5

   # Analyze another repository
   uv run python run_docu_cat.py --path /path/to/repo --count 10
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

**Note:** DocuCat requires an OpenRouter API key to analyze changes with Claude Haiku 4.5.
- Get your API key from https://openrouter.ai/keys
- Store it in a `.env` file (recommended) or set as an environment variable
- OpenRouter provides access to Claude and many other LLMs through a unified API

### Vector Store for Semantic Search

DocuCat can create a local vector store using Milvus Lite to enable semantic search across your codebase. This allows DocuCat to find relevant code and documentation more intelligently.

**Prerequisites:**
- Set the `GEMINI_API_KEY` environment variable with your Google Gemini API key
- Get your API key from https://ai.google.dev/gemini-api/docs/api-key

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

**Initialize a vector store:**

```bash
# Initialize in current directory
uv run python rag.py --init

# Initialize in a specific repository
uv run python rag.py --init /path/to/repo

# Force recreation of existing store
uv run python rag.py --force-init /path/to/repo

# Show vector store information
uv run python rag.py --info

# Show info for specific repository
uv run python rag.py --info /path/to/repo
```

Or using the installed command:

```bash
# Install locally
uv pip install -e .

# Use the command
rag --init
rag --init /path/to/repo
rag --force-init /path/to/repo
rag --info
```

**What it does:**
- Creates a `.docucat` directory in your repository
- Initializes a Milvus Lite vector database
- Sets up a collection for code/document embeddings
- Scans all files with supported extensions (Python, JavaScript, Markdown, etc.)
- Splits files into chunks (200 characters with 30 character overlap)
- Generates embeddings using Google Gemini (text-embedding-004 model)
- Stores chunks with their embeddings in the database

**Supported file types:**
Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, R, Objective-C, Markdown, LaTeX, HTML, XML, JSON, YAML, Bash, PowerShell, SQL, and plain text.

**Note:** The `.docucat` directory is automatically ignored by git. The vector store uses Google Gemini embeddings with task type `RETRIEVAL_DOCUMENT` (1536-dimension vectors) for high-quality semantic search.

## Current Features

- ✅ Detects and prints changed files in pull requests
- ✅ AI-powered change analysis using Claude Haiku 4.5 via OpenRouter and LangChain
- ✅ Understands the intent and purpose of code changes
- ✅ Automatically updates documentation and creates commits
- ✅ Posts summary comments to pull requests
- ✅ Follows developer instructions from PR comments
- ✅ Manual triggering via PR comments (on-demand execution)
- ✅ AI-powered comment assistant - answers questions on PRs
- ✅ Vector store initialization for semantic search (Milvus Lite)
- ✅ Per-PR configuration via PR description
- ✅ Local execution mode - analyze commits in any repository
- ✅ CLI interface with flexible options

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
   uv run python run_docu_cat_github.py
   ```

### Project Structure

```
docu-cat/
├── action.yml                      # GitHub Action definition
├── pyproject.toml                  # Python project configuration
├── AGENTS.md                       # Project guidelines and task list
├── CONFIGURATION.md                # Configuration documentation
├── __init__.py                     # Package initialization
├── run_docu_cat.py                         # CLI entry point for local execution
├── run_docu_cat_github.py          # Entry file for DocuCat GitHub Action
├── comment_reply_agent.py          # Entry file for comment reply agent
├── rag.py                          # RAG command for vector store operations
├── vector_store.py                 # Vector store management module
├── analyzer.py                     # LangGraph workflow for AI analysis
├── configuration_expert.py         # AI agent for parsing PR configurations
├── comment_instructions_parser.py  # AI agent for parsing developer instructions
├── docs/                           # Documentation
│   ├── PR_DESCRIPTION_EXAMPLE.md   # Example PR description with config
│   ├── PR_COMMENT_EXAMPLE.md       # Example PR comments from DocuCat
│   └── DEVELOPER_INSTRUCTIONS.md   # Guide for developer instructions
|-- agents/                         # Agents
|   ├── docu_cat.py                 # The main agent of DocuCat
├── tools/                          # LangChain tools for the AI agent
│   ├── run_command.py              # Command execution tool
│   ├── read_file.py                # File reading tool
│   └── write_file.py               # File writing tool
└── .github/
    └── workflows/
        ├── example.yml             # Example workflow configuration
        └── comment-trigger.yml     # Comment-triggered workflow
```

### Implementation Details

- Built with Python 3.12+
- Managed with uv for fast, reliable dependency management
- Uses LangGraph for AI workflow orchestration
- Powered by Claude Haiku 4.5 via OpenRouter for intelligent change analysis
- LangChain integration for LLM abstraction
- Integrates with GitHub API for PR analysis
- OpenRouter provides unified access to multiple LLM providers
- Milvus Lite for local vector storage and semantic search
- Google Gemini (text-embedding-004) for high-quality code/document embeddings

## How It Works

DocuCat can be triggered in two ways:

**Automatic Trigger:** When a pull request is created or updated
**Manual Trigger:** When a comment with `@DocuCat` or similar phrase is posted on a PR

When triggered, DocuCat:

1. Checks out the repository
2. Reads configuration from the PR description (if any)
3. Checks if DocuCat is enabled for this PR
4. Detects changed files between base and head commits
5. Reads and parses developer instructions from PR comments
6. Analyzes changes using Claude Haiku 4.5 via OpenRouter and LangGraph to understand the intent
7. Follows developer instructions while determining which documentation files need updates
8. Updates the documentation files
9. Creates a commit and pushes changes back to the PR (if configured to do so)
10. Posts a summary comment to the PR with the analysis results

## Contributing

DocuCat is currently under construction. See `AGENTS.md` for the task list and development guidelines.

## License

MIT License
