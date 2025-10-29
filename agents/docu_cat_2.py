import os
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from tools import run_command, read_file, write_file, query_vector_store
from typing import Literal
from langgraph.prebuilt import ToolNode
from agents.docu_cat_state import DocuCatState
from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate


system_prompt_template = PromptTemplate.from_template("""
You are an expert technical writer who is responsible for updating documentation and code comments based on code changes.

<instructions>
You should follow the steps below to complete your task:

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
   For each document or code file that needs updates:
   a. Use read_file to read the current content
   b. Determine what sections need to be updated
   c. Use write_file to write the updated content
   d. Be precise and only update what's related to the changes.

4. SUMMARIZE:
   After completing updates, provide a summary listing:
   - Which documents were updated
   - What changes were made to each
   - If no documents needed updates, clearly state "NO_UPDATES_NEEDED"
</instructions>

<information>
Repository path: {repo_path}
Changed files:
{files_list}
</information>

<notes>
Remember to use the repository path as the working_dir when using any tools.
</notes>

Begin your analysis and document updates now.
""")

def create_agent_node(llm_with_tools):
    """
    Create the agent node that calls the LLM with tools.

    Args:
        llm_with_tools: LLM instance with tools bound

    Returns:
        Function that processes the state and calls the LLM
    """
    def agent(state: DocuCatState) -> DocuCatState:
        """Call the LLM to analyze or use tools."""
        messages = state.get("messages", [])
        response = llm_with_tools.invoke([SystemMessage(content=system_prompt_template.format(repo_path=state.get("repo_path"), files_list=state.get("changed_files")))] + messages)
        print(f"💬 {response.content}")
        return {"messages": [response]}

    return agent

def should_continue(state: DocuCatState) -> Literal["tools", "end"]:
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

def create_workflow() -> StateGraph:
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
        max_tokens=4096,
        temperature=0.7,
    )

    # Create tools list - always include base tools
    tools = [run_command, read_file, write_file, query_vector_store]

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Create the graph
    workflow = StateGraph(DocuCatState)

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

agent_docu_cat = create_workflow()
