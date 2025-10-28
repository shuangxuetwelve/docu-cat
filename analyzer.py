"""
LangGraph workflow for analyzing code changes and understanding intent.
Supports tool calling for executing commands to inspect files.
"""

import os
from typing import TypedDict, Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from tools import run_command, read_file, write_file, query_vector_store
from vector_store import check_vector_store


class AnalysisState(TypedDict):
    """State for the analysis workflow."""
    changed_files: list[str]
    repo_path: str
    messages: Annotated[list, add_messages]

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


def create_analysis_workflow(repo_path: str = ".") -> StateGraph:
    """
    Create the LangGraph workflow for analyzing changes with tool support.

    Args:
        repo_path: Path to the repository (used to check for vector store availability)

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
        max_tokens=4000,
        temperature=0.7,
    )

    # Create tools list - always include base tools
    tools = [run_command, read_file, write_file]
    
    # Add query_vector_store tool if vector store is available
    if check_vector_store(repo_path):
        tools.append(query_vector_store)

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


def identify_and_update_documents(changed_files: list[str], repo_path: str = ".", developer_instructions: str = "") -> dict:
    """
    Analyze changed files and identify/update documents that need changes.

    Args:
        changed_files: List of file paths that changed
        repo_path: Path to the repository being analyzed (default: current directory)
        developer_instructions: Optional instructions from PR comments (default: "")

    Returns:
        Dictionary with:
        - 'analysis': Analysis of code changes
        - 'documents_updated': List of documents that were updated
        - 'no_updates_needed': Boolean indicating if no documents needed updates
    """
    if not changed_files:
        return {
            "analysis": "No changed files to analyze.",
            "documents_updated": [],
            "no_updates_needed": True
        }

    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "analysis": "Error: OPENROUTER_API_KEY not set. Cannot analyze changes.",
            "documents_updated": [],
            "no_updates_needed": True
        }

    try:
        workflow = create_analysis_workflow(repo_path)

        # Create initial prompt for code analysis and document identification
        files_list = "\n".join(f"  - {f}" for f in changed_files)

        # Add developer instructions if provided
        instructions_section = ""
        if developer_instructions:
            instructions_section = f"""
{developer_instructions}
"""

        # Build tools description
        tools_description = """You have access to these tools:
- run_command: Execute shell commands (git diff, cat, etc.)
- read_file: Read file contents
- write_file: Write/update file contents"""
        
        # Add query_vector_store tool description if available
        if check_vector_store(repo_path):
            tools_description += """
- query_vector_store: Query the local vector store for relevant code/document chunks"""

        initial_prompt = f"""Analyze the following changed files from a code commit and update relevant documentation:

Repository path: {repo_path}
Changed files:
{files_list}
{instructions_section}
{tools_description}

Your task is to:

1. ANALYZE CODE CHANGES:
   - Use run_command to inspect what changed in each file (e.g., git diff)
   - Determine the intent and purpose of the changes
   - Identify what features/functionality were added/modified

2. IDENTIFY DOCUMENTS AND CODE COMMENTS TO UPDATE:
   - Determine which documentation files need updates based on the code changes
   - Common documents to check:
     * README.md - If project structure, features, or usage changed
     * Other .md files as needed
   - You must call the tool query_vector_store to search the local vector store for relevant documentation files and code files, if you are provided with the tool. If you found any comments need updates in code files, you must update the comments.

3. UPDATE DOCUMENTS:
   For each document that needs updates:
   a. Use read_file to read the current content
   b. Determine what sections need to be updated
   c. Use write_file to write the updated content
   d. Be precise and only update what's necessary

4. SUMMARIZE:
   After completing updates, provide a summary listing:
   - Which documents were updated
   - What changes were made to each
   - If no documents needed updates, clearly state "NO_UPDATES_NEEDED"

Remember to specify working_dir="{repo_path}" when using any tools.

Begin your analysis and document updates now."""

        initial_state = {
            "changed_files": changed_files,
            "repo_path": repo_path,
            "messages": [HumanMessage(content=initial_prompt)],
        }

        # Run the workflow
        result = workflow.invoke(initial_state)

        # Extract information from messages
        messages = result.get("messages", [])
        analysis = ""
        documents_updated = []
        no_updates_needed = False

        # Find the final AI response
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                analysis = message.content
                break

        # Check if agent indicated no updates needed
        if "NO_UPDATES_NEEDED" in analysis:
            no_updates_needed = True

        # Find all write_file tool calls to determine which documents were updated
        for message in messages:
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.get("name") == "write_file":
                        filepath = tool_call.get("args", {}).get("filepath")
                        if filepath and filepath not in documents_updated:
                            documents_updated.append(filepath)

        return {
            "analysis": analysis if analysis else "No analysis available",
            "documents_updated": documents_updated,
            "no_updates_needed": no_updates_needed
        }

    except Exception as e:
        return {
            "analysis": f"Error during analysis: {str(e)}",
            "documents_updated": [],
            "no_updates_needed": True
        }
