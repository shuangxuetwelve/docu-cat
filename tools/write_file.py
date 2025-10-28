"""
File writing tool for the AI agent.

This module provides a LangChain tool that allows the agent to write
or update file contents in the repository. This is essential for the agent to:
- Update documentation files (README.md, TOOLS.md, etc.)
- Create new documentation when needed
- Apply fixes or updates to existing files

The tool includes safety checks and error handling for write operations.
"""

from langchain_core.tools import tool


@tool
def write_file(filepath: str, content: str, working_dir: str = ".") -> str:
    """
    Write or update the contents of a file in the repository.

    Use this to update documentation files or create new files based on
    code changes analysis.

    Args:
        filepath: Relative path to the file (e.g., "README.md", "docs/api.md")
        content: Complete new content to write to the file
        working_dir: Working directory/repository root (default: current directory)

    Returns:
        Success message or error message if write fails
    """
    import os

    print(f"🔍 Writing file: {filepath} in {working_dir}")

    try:
        # Construct full path
        full_path = os.path.join(working_dir, filepath)

        # Create directory if it doesn't exist
        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Write file contents
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"✅ Successfully wrote {len(content)} characters to '{filepath}'"

    except Exception as e:
        return f"Error writing file '{filepath}': {str(e)}"
