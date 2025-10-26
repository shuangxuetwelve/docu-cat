"""
LangGraph workflow for analyzing code changes and understanding intent.
"""

import os
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class AnalysisState(TypedDict):
    """State for the analysis workflow."""
    changed_files: list[str]
    messages: Annotated[list, add_messages]
    analysis_result: str


def analyze_changes(state: AnalysisState) -> AnalysisState:
    """
    Analyze changed files using Claude Haiku via OpenRouter to understand the intent.

    Args:
        state: Current analysis state

    Returns:
        Updated state with analysis result
    """
    changed_files = state.get("changed_files", [])

    if not changed_files:
        return {
            **state,
            "analysis_result": "No changed files to analyze."
        }

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {
            **state,
            "analysis_result": "Error: OPENROUTER_API_KEY not set. Cannot analyze changes."
        }

    # Create prompt for Claude
    files_list = "\n".join(f"  - {f}" for f in changed_files)
    prompt = f"""Analyze the following changed files from a code commit and determine the intent of the changes:

Changed files:
{files_list}

Based on these file paths and names, what is the likely intent or purpose of this change?
Consider:
1. What feature or functionality is being added/modified?
2. What type of change is this (feature, bugfix, refactor, documentation, etc.)?
3. What areas of the codebase are affected?

Provide a concise analysis (2-3 sentences) focusing on the intent and purpose."""

    try:
        # Initialize ChatOpenAI with OpenRouter
        llm = ChatOpenAI(
            model="anthropic/claude-haiku-4.5",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=500,
            temperature=0.7,
        )

        # Call the model
        response = llm.invoke(prompt)

        # Extract the analysis
        analysis = response.content

        return {
            **state,
            "analysis_result": analysis
        }

    except Exception as e:
        return {
            **state,
            "analysis_result": f"Error during analysis: {str(e)}"
        }


def create_analysis_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for analyzing changes.

    Returns:
        Compiled StateGraph workflow
    """
    # Create the graph
    workflow = StateGraph(AnalysisState)

    # Add nodes
    workflow.add_node("analyze", analyze_changes)

    # Define edges
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", END)

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
    workflow = create_analysis_workflow()

    initial_state = {
        "changed_files": changed_files,
        "messages": [],
        "analysis_result": ""
    }

    result = workflow.invoke(initial_state)
    return result.get("analysis_result", "No analysis available")
