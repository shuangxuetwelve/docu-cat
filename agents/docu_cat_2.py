import os
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from tools import run_command, read_file, write_file, query_vector_store
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, Literal
from langgraph.prebuilt import ToolNode


class AgentState(TypedDict):
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
    def agent(state: AgentState) -> AgentState:
        """Call the LLM to analyze or use tools."""
        messages = state.get("messages", [])
        response = llm_with_tools.invoke(messages)
        print(f"💬 Response: {response.content}")
        return {"messages": [response]}

    return agent

def should_continue(state: AgentState) -> Literal["tools", "end"]:
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
        max_tokens=4096,
        temperature=0.7,
    )

    # Create tools list - always include base tools
    tools = [run_command, read_file, write_file, query_vector_store]

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Create the graph
    workflow = StateGraph(AgentState)

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

agent = create_workflow()
