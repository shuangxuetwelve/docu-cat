# DocuCat 🐱📄

An AI assistant that generates or updates documents from changes in a GitHub pull request.

## Overview

DocuCat is a GitHub Action that analyzes pull request changes and helps maintain documentation. It can:
- Detect changed files in pull requests
- Generate or update documentation or comments based on code changes
- Run as a GitHub Action in any repository
- Run locally for development and testing
- Use Milvus Lite to search for documents or comments semantically.

## Quick Start

### Using DocuCat as a GitHub Action

1. Add your OpenRouter API key as a repository secret:
   - Go to your repository Settings → Secrets and variables → Actions
   - Create a new secret named `OPENROUTER_API_KEY`
   - Get your API key from https://openrouter.ai/keys
   - Paste your OpenRouter API key value

2. Create a workflow file in your repository at `.github/workflows/trigger-docu-cat.yml`:

```yaml
name: DocuCat - Document Generator

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  docu-cat:
    runs-on: ubuntu-latest
    name: Generate/Update Documentation

    # Required permissions for DocuCat to commit and push changes
    permissions:
      contents: write        # Allow pushing commits
      pull-requests: write   # Allow updating PR

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Fetch full history for git diff
          token: ${{ secrets.GITHUB_TOKEN }}
          # Checkout the PR branch (head ref) to allow pushing commits
          ref: ${{ github.event.pull_request.head.ref }}

      - name: Run DocuCat
        uses: ./ # Use this when testing in the DocuCat repository itself
        # For other repositories, use:
        # uses: lu/docu-cat@main  # or use a specific version tag
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

See [PULL_REQUEST_TEMPLATE_EXAMPLE.md](.github/PULL_REQUEST_TEMPLATE_EXAMPLE.md) as an example of the pull request description template.

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

3. Sync the Python environments:
   ```bash
   uv sync
   ```

4. Run DocuCat using uv:
   ```bash
   # Analyze last commit in current directory
   uv run run_docu_cat.py

   # Analyze last 5 commits
   uv run run_docu_cat.py --count 5

   # Analyze another repository
   uv run run_docu_cat.py --path /path/to/repo --count 10
   ```

4. Or install and use the CLI command:
   ```bash
   # Install locally
   uv pip install -e .

   # Run from anywhere
   docu-cat --count 5
   docu-cat --path /path/to/repo --count 10
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
- Splits files into chunks
- Generates embeddings using Google Gemini (gemini-embedding-001 model)
- Stores chunks with their embeddings in the database

**Supported file types:**
Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, R, Objective-C, Markdown, LaTeX, HTML, XML, JSON, YAML, Bash, PowerShell, SQL, and plain text.

### Project Structure

```
docu-cat/
├── action.yml                      # GitHub Action definition
├── pyproject.toml                  # Python project configuration
├── AGENTS.md                       # Project guidelines and task list for coding agents
├── CLAUDE.md                       # Project guidelines and task list for Claude Code coding agent
├── run_docu_cat.py                 # CLI entry point for local execution
├── run_docu_cat_github.py          # Entry file for DocuCat GitHub Action
├── rag.py                          # RAG command for vector store operations
├── vector_store.py                 # Vector store management module
|-- agents/                         # Agents
|   ├── docu_cat.py                 # The main agent of DocuCat
├── tools/                          # LangChain tools for the AI agent
│   ├── run_command.py              # Command execution tool
│   ├── read_file.py                # File reading tool
│   ├── write_file.py               # File writing tool
|   └── query_vector_store          # Vector store query tool
└── .github/
    └── workflow-examples/
        ├── trigger-docucat.yml     # Example workflow to run DocuCat as a Github action
        └── trigger-vector-store-sync.yml     # Comment-triggered workflow
```

## Contributing

DocuCat is currently under construction.

## License

MIT License
