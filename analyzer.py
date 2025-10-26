"""
LangGraph workflow for analyzing code changes and understanding intent.
Supports tool calling for executing commands to inspect files.
"""

import os
import subprocess
from typing import TypedDict, Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


class AnalysisState(TypedDict):
    """State for the analysis workflow."""
    changed_files: list[str]
    messages: Annotated[list, add_messages]


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


def create_agent_node(llm_with_tools):
    """
    Create the agent node that calls the LLM with tools.

    Args:
        llm_with_tools: LLM instance with tools bound

    Returns:
        Function that processes the state and calls the LLM
    """
    def agent(state: AnalysisState) -> AnalysisState:
        """Call the LLM to analyze or use tools."""
        messages = state.get("messages", [])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    return agent


def should_continue(state: AnalysisState) -> Literal["tools", "end"]:
    """
    Determine if we should continue with tool calls or end.

    Args:
        state: Current analysis state

    Returns:
        "tools" if there are tool calls to execute, "end" otherwise
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None

    # If the last message has tool calls, continue to tools node
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, we're done
    return "end"


def create_analysis_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for analyzing changes with tool support.

    Returns:
        Compiled StateGraph workflow
    """
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set. Cannot create workflow.")

    # Initialize ChatOpenAI with OpenRouter
    llm = ChatOpenAI(
        model="anthropic/claude-haiku-4.5",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        max_tokens=1500,
        temperature=0.7,
    )

    # Create tools list
    tools = [run_command]

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Create the graph
    workflow = StateGraph(AnalysisState)

    # Add nodes
    workflow.add_node("agent", create_agent_node(llm_with_tools))
    workflow.add_node("tools", ToolNode(tools))

    # Define edges
    workflow.add_edge(START, "agent")

    # Add conditional edge from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # After tools, always go back to agent
    workflow.add_edge("tools", "agent")

    # Compile the graph
    return workflow.compile()


def analyze_changed_files(changed_files: list[str]) -> str:
    """
    Convenience function to analyze a list of changed files.

    Args:
        changed_files: List of file paths that changed

    Returns:
        Analysis result string
    """
    if not changed_files:
        return "No changed files to analyze."

    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "Error: OPENROUTER_API_KEY not set. Cannot analyze changes."

    try:
        workflow = create_analysis_workflow()

        # Create initial prompt
        files_list = "\n".join(f"  - {f}" for f in changed_files)
        initial_prompt = f"""Analyze the following changed files from a code commit and determine the intent of the changes:

Changed files:
{files_list}

You have access to the run_command tool to inspect file contents or check git diffs.
Use this tool to gather more information about the changes if needed.

Based on your analysis, determine:
1. What feature or functionality is being added/modified?
2. What type of change is this (feature, bugfix, refactor, documentation, etc.)?
3. What areas of the codebase are affected?

Provide a concise analysis (2-4 sentences) focusing on the intent and purpose of the changes."""

        initial_state = {
            "changed_files": changed_files,
            "messages": [HumanMessage(content=initial_prompt)],
        }

        # Run the workflow
        result = workflow.invoke(initial_state)

        # Extract final analysis from the last AI message
        messages = result.get("messages", [])
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                return message.content

        return "No analysis available"

    except Exception as e:
        return f"Error during analysis: {str(e)}"
