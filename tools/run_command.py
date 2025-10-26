"""
Command execution tool for the AI agent.

This module provides a LangChain tool that allows the agent to execute
shell commands within a repository. This is essential for the agent to:
- Inspect file contents (e.g., cat, head, tail)
- Check git diffs to understand code changes
- Run git commands to analyze commit history
- Execute other commands needed to understand repository context

The tool is designed with safety features including timeouts and error handling
to prevent runaway commands from affecting the system.
"""

import subprocess
from langchain_core.tools import tool


@tool
def run_command(command: str, working_dir: str = ".") -> str:
    """
    Execute a shell command and return the result.

    Use this to inspect file contents, check git diffs, or run other commands
    to better understand the changes in the repository.

    Args:
        command: The shell command to execute (e.g., "cat main.py", "git diff HEAD~1 main.py")
        working_dir: Working directory for command execution (default: current directory)

    Returns:
        Command output as a string, or error message if command fails
    """
    # Print the command being executed
    print(f"🔧 Running command: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=30  # 30 second timeout for safety
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            return output if output else "(command executed successfully, no output)"
        else:
            return f"Error (exit code {result.returncode}): {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"
