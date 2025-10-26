# DocuCat Tools

This document describes the tools available to the DocuCat AI agent for analyzing code changes.

## Available Tools

### run_command

Execute a shell command and return the result. The AI agent can use this tool to inspect file contents, check git diffs, or run other commands to better understand changes in the repository.

**Parameters:**
- `command` (str): The shell command to execute
  - Examples: `"cat main.py"`, `"git diff HEAD~1 main.py"`, `"head -20 analyzer.py"`
- `working_dir` (str, optional): Working directory for command execution (default: current directory)

**Returns:**
- Command output as a string
- Error message if command fails or times out

**Safety Features:**
- Prints every command before execution for transparency
- 30-second timeout to prevent hanging commands
- Error handling for failed commands
- Captures both stdout and stderr

**Example Usage by AI:**

When analyzing changed files, the AI agent can automatically decide to use this tool:

```
Repository path: /Users/user/my-project
Changed files: main.py, analyzer.py

AI Agent thinks: "I should inspect what changed in these files"
AI Agent calls: run_command("git diff HEAD~1 main.py", working_dir="/Users/user/my-project")
Tool prints: 🔧 Running command: git diff HEAD~1 main.py
Tool returns: [actual diff output]
AI Agent: "Based on the diff, this adds a new feature..."
```

The agent receives the repository path in the initial prompt and is instructed to use it with the `working_dir` parameter when calling `run_command`.

## Workflow Architecture

The LangGraph workflow uses a ReAct pattern:

```
START → agent → [decision] → tools → agent → [decision] → END
                    ↓                            ↑
                    └────────────── end ─────────┘
```

**Nodes:**
1. **agent**: Calls LLM with tools bound, receives changed files list and repository path
2. **tools**: Executes tool calls made by the agent
3. **conditional edge**: Decides whether to continue with tools or end

**State:**
- `changed_files`: List of file paths that were modified
- `repo_path`: Absolute path to the repository being analyzed
- `messages`: Conversation history including tool calls and responses

**Flow:**
1. Agent receives list of changed files and repository path
2. Agent analyzes and optionally calls `run_command` to inspect files in the repository
3. If tool calls are made, execute them and return to agent
4. Agent provides final analysis based on gathered information
5. Workflow ends

## Adding New Tools

To add a new tool to the workflow:

1. Define the tool using the `@tool` decorator:
   ```python
   @tool
   def my_tool(param: str) -> str:
       """Tool description that the AI will see."""
       # Implementation
       return result
   ```

2. Add it to the tools list in `create_analysis_workflow()`:
   ```python
   tools = [run_command, my_tool]
   ```

3. The AI agent will automatically have access to the new tool

## Future Tool Ideas

Potential tools that could be added:

- `read_file_range(filepath, start_line, end_line)`: Read specific line ranges
- `search_code(pattern, filepath)`: Search for patterns in files
- `get_git_blame(filepath, line_number)`: Get blame info for specific lines
- `analyze_dependencies(filepath)`: Analyze import/dependency changes
- `get_test_coverage(filepath)`: Check test coverage for changed files
