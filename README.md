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

**Example workflow file:** See [.github/workflow-examples/trigger-docucat.yml](.github/workflow-examples/trigger-docucat.yml)

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

### Using Vector Store for Semantic Search Locally

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

### Using Vector Store for Semantic Search on Github

You can set up a GitHub workflow to automatically initialize or update the vector store whenever changes are pushed to your main branch. This ensures DocuCat always has access to up-to-date embeddings for semantic search.

**Prerequisites:**
- Add `GEMINI_API_KEY` as a repository secret:
  - Go to your repository Settings → Secrets and variables → Actions
  - Create a new secret named `GEMINI_API_KEY`
  - Get your API key from https://ai.google.dev/gemini-api/docs/api-key
  - Paste your Gemini API key value

**Setup:**

1. Copy the example workflow to your repository at `.github/workflows/vector-store-sync.yml`:

```yaml
name: Vector Store Sync

on:
  push:
    branches:
      - main
    paths-ignore:
      - ".docucat/**" # Ignore changes to the vector store itself

jobs:
  update-vector-store:
    runs-on: ubuntu-latest
    name: Initialize or Update Vector Store

    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
          path: target-repo

      - name: Checkout DocuCat
        uses: actions/checkout@v4
        with:
          repository: shuangxuetwelve/docu-cat
          path: docu-cat

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install DocuCat dependencies
        shell: bash
        run: cd docu-cat && uv sync

      - name: Initialize or Update Vector Store
        shell: bash
        run: uv run --directory docu-cat python init_update_store_aga.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TARGET_REPO_PATH: ${{ github.workspace }}/target-repo
```

**Example workflow file:** See [.github/workflow-examples/trigger-vector-store-sync.yml](.github/workflow-examples/trigger-vector-store-sync.yml)

2. The workflow will automatically:
   - **On first run**: Initialize the vector store with embeddings for all code and documents
   - **On subsequent runs**: Update only the changed files since the last update
   - Commit and push the vector store changes back to the repository

**What happens:**
- When you merge a pull request to main, the workflow triggers
- It checks if `.docucat/store.json` exists
  - **If not**: Initializes a new vector store with all repository files
  - **If yes**: Updates only the files that changed since the last SHA recorded in `store.json`
- Creates a commit with the updated vector store
- Pushes the commit to the main branch
- DocuCat can then use the vector store for semantic search in future pull requests

**Note:** The workflow uses `paths-ignore: [".docucat/**"]` to prevent infinite loops when the vector store itself is updated.

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

## Evaluation

You can run experiments to evaluate DocuCat's performance using Langfuse and Docker. The evaluation measures how accurately DocuCat identifies and updates the correct documentation files.

**Prerequisites:**

1. Set up required environment variables:
  - `OPENROUTER_API_KEY`: Your OpenRouter API key (required for running DocuCat)
  - `GEMINI_API_KEY`: Your Gemini API key (required if using vector store)
  - Langfuse API keys if you want to bring your own Langfuse dataset
    - `LANGFUSE_PUBLIC_KEY`: Your Langfuse public key
    - `LANGFUSE_SECRET_KEY`: Your Langfuse secret key
    - `LANGFUSE_HOST`: Your Langfuse host URL (optional, defaults to Langfuse cloud)

Place the API keys in .env.

2. Prepare a dataset in Langfuse with test cases, or use the local dataset included in the Docker image.

**Running the Evaluation:**

1. **Build the Docker image:**

```bash
docker build -t docu-cat .
```

This builds a Docker image that includes:
- DocuCat source code at `/home/docu-cat`
- Test dataset at `/home/datasets`

2. **Run an interactive container:**

```bash
docker run --rm -it docu-cat /bin/bash
```

This command starts an interactive bash shell inside the container with your environment variables.

3. **Run the experiment inside the container:**

```bash
# Run experiment with the local dataset
uv run run_experiment.py --path /home/datasets --local
```

**What the evaluation does:**

- Runs DocuCat on each test case in the dataset
- Compares the documents DocuCat updates against expected documents
- Calculates an F1 score for each test case
- Aggregates results across all test cases
- Reports evaluation metrics to Langfuse

**Evaluation Metrics:**

The experiment calculates **F1 Score** to measure DocuCat's accuracy:
- **Precision**: Percentage of documents DocuCat updated that should have been updated
- **Recall**: Percentage of documents that should have been updated that DocuCat found
- **F1 Score**: Harmonic mean of precision and recall

**Viewing Results:**

After the experiment completes, the experiment results will be printed in the console. If you use Langfuse, you can view the results in the Langfuse dashboard at your configured `LANGFUSE_HOST`.

## License

MIT License
