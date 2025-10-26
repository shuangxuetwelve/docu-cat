"""
File reading tool for the AI agent.

This module provides a LangChain tool that allows the agent to read
file contents from the repository. This is essential for the agent to:
- Read current documentation contents before updating them
- Inspect specific file sections that changed
- Understand the full context of files being modified

The tool includes error handling for missing files and read failures.
"""

from langchain_core.tools import tool


@tool
def read_file(filepath: str, working_dir: str = ".") -> str:
    """
    Read the contents of a file in the repository.

    Use this to read current documentation or code files to understand
    their structure and content before making updates.

    Args:
        filepath: Relative path to the file (e.g., "README.md", "tools/run_command.py")
        working_dir: Working directory/repository root (default: current directory)

    Returns:
        File contents as a string, or error message if file cannot be read
    """
    import os

    try:
        # Construct full path
        full_path = os.path.join(working_dir, filepath)

        # Check if file exists
        if not os.path.exists(full_path):
            return f"Error: File '{filepath}' not found in {working_dir}"

        # Read file contents
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content if content else "(file is empty)"

    except Exception as e:
        return f"Error reading file '{filepath}': {str(e)}"
